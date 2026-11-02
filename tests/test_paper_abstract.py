import re
import unittest
from pathlib import Path


def paper_abstract():
    body = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", Path("paper/because.tex").read_text(), re.S).group(1)
    return body.replace(r"\noindent", "").replace("$", "").replace(r"\%", "%").strip()


def submission_abstract():
    return re.search(r"^> (.*)$", Path("paper/SUBMIT.md").read_text(), re.M).group(1)


class Abstract(unittest.TestCase):
    def test_submission_abstract_is_the_papers(self):
        self.assertEqual(submission_abstract(), paper_abstract())

    def test_submission_abstract_fits_arxiv(self):
        self.assertTrue(submission_abstract().isascii())
        self.assertLessEqual(len(submission_abstract()), 1920)
