"""Forwarding proxy that records exactly what Claude Code sends to the model.

Point an agent at it with ANTHROPIC_BASE_URL=http://127.0.0.1:<port>. Every
POST body (system prompt, messages, tool list) is written to the capture
directory, together with the upstream response's rate-limit headers. Request
headers are never recorded, because they carry the credential.

    python3 harness/capture_proxy.py --port 8765 --out captures/
"""

import argparse
import http.client
import http.server
import itertools
import json
import os
import threading
import time

UPSTREAM = "api.anthropic.com"
HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "upgrade", "proxy-connection", "host"}
_counter = itertools.count()
_lock = threading.Lock()


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    out_dir = "captures"

    def log_message(self, *args):
        pass

    def _forward(self, body):
        upstream = http.client.HTTPSConnection(UPSTREAM, timeout=600)
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP and k.lower() != "content-length"}
        headers["Host"] = UPSTREAM
        upstream.request(self.command, self.path, body=body, headers=headers)
        resp = upstream.getresponse()
        self.send_response(resp.status, resp.reason)
        for k, v in resp.getheaders():
            if k.lower() not in HOP_BY_HOP and k.lower() != "content-length":
                self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        while True:
            chunk = resp.read1(65536)
            if not chunk:
                break
            self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")
        upstream.close()
        return resp

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        # The CLI injects the login's email into every prompt and `ls -l` prints the OS user; the model should not
        # learn whose account this is.
        email, user = os.environ.get("BECAUSE_ACCOUNT_EMAIL"), os.environ.get("USER")
        if email:
            body = body.replace(email.encode(), b"dev@example.invalid")
        if user:
            body = body.replace(user.encode(), b"dev")
        resp = self._forward(body)
        if "/messages" not in self.path:
            return
        with _lock:
            n = next(_counter)
        record = {
            "t": time.time(),
            "path": self.path,
            "status": resp.status,
            "ratelimit": {k: v for k, v in resp.getheaders() if "ratelimit" in k.lower() or "overage" in k.lower()},
            "request": json.loads(body) if body else None,
        }
        with open(os.path.join(self.out_dir, f"{os.getpid()}-{n:05d}.json"), "w") as f:
            json.dump(record, f)

    def do_GET(self):
        self._forward(None)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=0, help="0 picks a free port")
    p.add_argument("--out", default="captures")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    Handler.out_dir = a.out
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(srv.server_address[1], flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
