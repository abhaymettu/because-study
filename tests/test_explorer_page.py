import unittest
from pathlib import Path

from explorer.build import with_policy


class PagePolicy(unittest.TestCase):
    def test_policy_names_only_the_pages_own_scripts(self):
        page = with_policy("<head>\n<script>a()</script></head><body><script>b()</script>")
        self.assertTrue(page.startswith(
            "<head>\n<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; script-src "
            "'sha256-qVpDBgj7bpq5hMAcGp3AOc79J3Y1Z4HvySTwKrWDoy4=' 'sha256-cf242PFc/kb7xD0Qzhsmd9vvRkc+cWFmbi+k+YvtdKc='; "
        ))
        self.assertIn("connect-src 'self'; base-uri 'none'; form-action 'none'", page)

    def test_page_loads_no_script_or_stylesheet_from_elsewhere(self):
        source = Path("explorer/index.html").read_text()
        for tag in ("<script src", "<link rel=\"stylesheet\"", "@import", "@font-face"):
            self.assertNotIn(tag, source)
