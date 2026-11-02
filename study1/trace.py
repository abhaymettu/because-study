"""What a run leaves behind. Checkers read only this, so every score reruns from raw traces."""

import ast
import difflib
import io
import re
import tokenize
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Commit:
    subject: str
    message: str
    files: tuple = ()


@dataclass(frozen=True)
class Trace:
    commands: tuple = ()  # Bash commands in the order the agent issued them
    calls: tuple = ()  # (tool name, target path or command) in order, for every tool call
    final_message: str = ""
    commits: tuple = ()  # commits made since the base commit, oldest first
    branch: str = "main"
    before: dict = field(default_factory=dict)  # path -> text at the base commit, changed paths only
    after: dict = field(default_factory=dict)  # path -> text in the final tree, changed paths only; deleted is absent

    @staticmethod
    def from_json(d):
        return Trace(
            commands=tuple(d["commands"]),
            calls=tuple(tuple(c) for c in d["calls"]),
            final_message=d["final_message"],
            commits=tuple(Commit(c["subject"], c["message"], tuple(c["files"])) for c in d["commits"]),
            branch=d["branch"],
            before=d["before"],
            after=d["after"],
        )

    @property
    def new_paths(self):
        return [p for p in self.after if p not in self.before]

    @property
    def changed_paths(self):
        return sorted(set(self.after) | set(self.before))

    def added_lines(self, path):
        """1-indexed line numbers in the final text that the agent added."""
        new = self.after.get(path, "").splitlines()
        old = self.before.get(path, "").splitlines()
        out = set()
        for op, _, _, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
            if op in ("replace", "insert"):
                out.update(range(j1 + 1, j2 + 1))
        return out

    def python_paths(self):
        return [p for p in self.after if p.endswith(".py")]

    def is_test_path(self, path):
        name = path.rsplit("/", 1)[-1]
        return name.startswith("test_") or path.startswith(("tests/", "qa/"))

    def added_nodes(self):
        """Every AST node that starts on an added line, with its path. Unparsable files yield nothing."""
        for path in self.python_paths():
            added = self.added_lines(path)
            try:
                tree = ast.parse(self.after[path])
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if getattr(node, "lineno", None) in added:
                    yield path, node

    def added_functions(self):
        return [(p, n) for p, n in self.added_nodes() if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    def added_public_functions(self):
        """New top-level functions outside test code that do not start with an underscore."""
        out = []
        for path in self.python_paths():
            if self.is_test_path(path):
                continue
            added = self.added_lines(path)
            try:
                tree = ast.parse(self.after[path])
            except SyntaxError:
                continue
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno in added:
                    if not node.name.startswith("_"):
                        out.append((path, node))
        return out

    def added_string_tokens(self):
        """(path, line, token text) for each string literal on an added line, docstrings excluded."""
        for path in self.python_paths():
            added = self.added_lines(path)
            text = self.after[path]
            try:
                tree = ast.parse(text)
                tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
            except (SyntaxError, tokenize.TokenError):
                continue
            doc_lines = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    body = node.body
                    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                        if isinstance(body[0].value.value, str):
                            doc_lines.add(body[0].lineno)
            for tok in tokens:
                if tok.type == tokenize.STRING and tok.start[0] in added and tok.start[0] not in doc_lines:
                    yield path, tok.start[0], tok.string

    def has_added_python(self):
        return any(self.added_lines(p) for p in self.python_paths())

    def first_write_index(self):
        for i, (tool, _) in enumerate(self.calls):
            if tool in ("Edit", "Write", "NotebookEdit"):
                return i
        for i, (tool, target) in enumerate(self.calls):
            if tool == "Bash" and re.search(r"(^|\s)(cat\s*>|tee\s|sed\s+-i|mkdir\s)", target):
                return i
        return None
