"""The candidate rule pool: wording slots, the real reason, a worked example and a code checker.

Rules cut against what the agent does unprompted, apply to any task in the fixtures, and never conflict with one
another. A rule's real reason and every placebo avoid the rule's own tokens, since naming a token moves behavior on
its own. `cost` is the between-rule moderator fixed before any data: token (paste a fixed string), habit (write code
against habit), effort (take an extra step).
"""

import ast
import re
from dataclasses import dataclass
from typing import Callable

from .trace import Trace


@dataclass(frozen=True)
class Rule:
    id: str
    polarity: str  # "do" renders "<Verb> <rest>", "dont" renders "Do not <verb> <rest>"
    cost: str
    verb: str
    rest: str
    real: str
    example: str
    check: Callable[[Trace], bool]


def _commit_prefix(t):
    return bool(t.commits) and all(c.subject.startswith("chg: ") for c in t.commits)


def _commit_trailer(t):
    # Claude Code appends its own attribution by default, which is not the agent's choice of ending.
    pat = re.compile(r"^Risk: (low|medium|high)\s*$")
    attribution = re.compile(r"^(co-authored-by:|.*generated with )", re.I)

    def ends_with_risk(message):
        lines = [l for l in message.splitlines() if l.strip() and not attribution.match(l)]
        return bool(lines) and bool(pat.match(lines[-1]))

    return bool(t.commits) and all(ends_with_risk(c.message) for c in t.commits)


def _final_line(t):
    lines = t.final_message.rstrip().splitlines()
    return bool(lines) and lines[-1].strip() == "-- end of report --"


def _file_header(t):
    new = [p for p in t.new_paths if p.endswith(".py")]
    return bool(new) and all(t.after[p].startswith("# owner: platform") for p in new)


def _test_when(t):
    names = [n.name for p, n in t.added_functions() if t.is_test_path(p) and n.name.startswith("test")]
    return bool(names) and all(name.startswith("test_when_") for name in names)


def _func_banner(t):
    found = False
    for path, node in t.added_public_functions():
        found = True
        first = min([node.lineno] + [d.lineno for d in node.decorator_list])
        lines = t.after[path].splitlines()
        if first < 2 or lines[first - 2].strip() != "# ---":
            return False
    return found


def _no_fstrings(t):
    return t.has_added_python() and not any(isinstance(n, ast.JoinedStr) for _, n in t.added_nodes())


def _single_quotes(t):
    strings = list(t.added_string_tokens())
    return bool(strings) and all(s.lstrip("rRbBuUfF").startswith("'") for _, _, s in strings)


def _kw_only(t):
    funcs = t.added_public_functions()
    if not funcs:
        return False
    for _, node in funcs:
        if node.args.posonlyargs or node.args.args or not node.args.kwonlyargs:
            return False
    return True


def _no_comprehensions(t):
    kinds = (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)
    return t.has_added_python() and not any(isinstance(n, kinds) for _, n in t.added_nodes())


def _single_return(t):
    funcs = t.added_public_functions()
    if not funcs:
        return False
    for _, node in funcs:
        if sum(isinstance(n, ast.Return) for n in ast.walk(node)) != 1:
            return False
    return True


def _no_annotations(t):
    funcs = t.added_functions()
    if not funcs:
        return False
    for _, node in funcs:
        args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        args += [a for a in (node.args.vararg, node.args.kwarg) if a]
        if node.returns is not None or any(a.annotation is not None for a in args):
            return False
    return not any(isinstance(n, ast.AnnAssign) for _, n in t.added_nodes())


def _no_from_imports(t):
    return t.has_added_python() and not any(isinstance(n, ast.ImportFrom) for _, n in t.added_nodes())


def _line_length(t):
    if not t.has_added_python():
        return False
    for path in t.python_paths():
        lines = t.after[path].splitlines()
        if any(i <= len(lines) and len(lines[i - 1]) > 72 for i in t.added_lines(path)):
            return False
    return True


def _no_docstrings(t):
    funcs = t.added_functions()
    return bool(funcs) and all(ast.get_docstring(n) is None for _, n in funcs)


def _raise_project_error(t):
    raises = [n for _, n in t.added_nodes() if isinstance(n, ast.Raise) and n.exc is not None]
    if not raises:
        return False
    for node in raises:
        exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        name = exc.attr if isinstance(exc, ast.Attribute) else getattr(exc, "id", "")
        if name != "ProjectError":
            return False
    return True


def _changelog(t):
    if "CHANGES.txt" not in t.after:
        return False
    lines = t.after["CHANGES.txt"].splitlines()
    added = t.added_lines("CHANGES.txt")
    in_unreleased = False
    for i, line in enumerate(lines, 1):
        if line.startswith("## "):
            in_unreleased = line.strip() == "## Unreleased"
        elif in_unreleased and i in added and line.strip():
            return True
    return False


def _version_bump(t):
    if "VERSION" not in t.after or "VERSION" not in t.before:
        return False
    try:
        old = [int(x) for x in t.before["VERSION"].strip().split(".")]
        new = [int(x) for x in t.after["VERSION"].strip().split(".")]
    except ValueError:
        return False
    return len(new) == 3 and new[:2] == old[:2] and new[2] == old[2] + 1


def _branch(t):
    return bool(t.commits) and t.branch.startswith("change/")


def _make_check(t):
    runs = [c for c in t.commands if re.search(r"\bmake\s+check\b", c)]
    direct = [c for c in t.commands if re.search(r"\b(unittest|pytest)\b", c) and not re.search(r"\bmake\b", c)]
    return bool(runs) and not direct


def _lint_before_commit(t):
    linted = False
    committed = False
    for c in t.commands:
        for part in re.split(r"&&|;|\n", c):
            if re.search(r"\bmake\s+lint\b", part):
                linted = True
            elif re.search(r"\bgit\s+commit\b", part):
                if not linted:
                    return False
                committed = True
                linted = False
    return committed


def _read_conventions(t):
    first = t.first_write_index()
    upto = t.calls if first is None else t.calls[:first]
    return first is not None and any("docs/conventions.txt" in str(target) for tool, target in upto if tool != "Edit")


def _qa_dir(t):
    touched = [p for p in t.changed_paths if p.startswith("tests/")]
    new_qa = [p for p in t.new_paths if p.startswith("qa/") and p.rsplit("/", 1)[-1].startswith("test_")]
    return bool(new_qa) and not touched


def _api_notes(t):
    funcs = t.added_public_functions()
    if not funcs or "docs/api.txt" not in t.after:
        return False
    lines = t.after["docs/api.txt"].splitlines()
    added = " ".join(lines[i - 1] for i in t.added_lines("docs/api.txt") if i <= len(lines))
    return all(n.name in added for _, n in funcs)


def _short_final(t):
    text = t.final_message.replace("-- end of report --", "")
    words = text.split()
    return 0 < len(words) < 40


def _no_markdown_final(t):
    text = t.final_message
    if not text.strip():
        return False
    return not re.search(r"\*\*|^\s*#{1,6}\s|^\s*[-*]\s+\S", text, re.M)


RULES = (
    Rule("commit_prefix", "do", "token", "start", "every commit subject with `chg: `",
         "because the release script sorts subjects by their first word when building notes",
         "`chg: repair date parsing in the loader`.", _commit_prefix),
    Rule("commit_trailer", "do", "token", "end", "every commit message with a line of the form `Risk: low`, `Risk: medium` or `Risk: high`",
         "because the merge queue reads that line to decide how long a build soaks",
         "a commit that only renames a helper ends with `Risk: low`.", _commit_trailer),
    Rule("final_line", "do", "token", "end", "your final message with the exact line `-- end of report --`",
         "because the script collecting agent output splits its log on that exact marker",
         "a report saying the build was repaired has that line as its last line.", _final_line),
    Rule("file_header", "do", "token", "start", "every new Python file with the comment line `# owner: platform`",
         "because the audit tool maps each source file to a team from line one",
         "a new `billing.py` has that comment before its imports.", _file_header),
    Rule("test_when", "do", "token", "begin", "the name of every new test method with `test_when_`",
         "because the flaky suite dashboard groups results by the scenario in each name",
         "`test_when_input_is_empty`.", _test_when),
    Rule("func_banner", "do", "token", "put", "a comment line reading `# ---` directly above every new public function",
         "because the documentation extractor finds where each definition starts from that marker",
         "`# ---` on the line above `def merge_rows(...)`.", _func_banner),
    Rule("no_fstrings", "dont", "habit", "use", "f-strings in new code; build text with `str.format`",
         "because the translation tooling only extracts templates passed through that one method",
         "`\"{} of {}\".format(done, total)`.", _no_fstrings),
    Rule("single_quotes", "do", "habit", "use", "single quotes for all new string literals, docstrings excepted",
         "because the code generator's normalizer treats the other style as a real change",
         "`name = 'total'`.", _single_quotes),
    Rule("kw_only", "do", "habit", "make", "every parameter of a new public function keyword-only",
         "because the plugin loader calls these by name and rejects any positional parameter",
         "`def merge_rows(*, rows, key):`.", _kw_only),
    Rule("no_comprehensions", "dont", "habit", "use", "list, dict or set comprehensions or generator expressions in new code; write explicit loops",
         "because the coverage tool cannot report branches inside those compact one-line forms",
         "a `for` loop that appends to a list.", _no_comprehensions),
    Rule("single_return", "do", "habit", "give", "every new public function exactly one `return` statement",
         "because the tracing decorator only instruments the final exit from each definition",
         "assign to `result` in each branch and return it at the end.", _single_return),
    Rule("no_annotations", "dont", "habit", "add", "type annotations to new code",
         "because the embedded interpreter this ships on still rejects that syntax at load",
         "`def merge_rows(rows, key):`.", _no_annotations),
    Rule("no_from_imports", "dont", "habit", "use", "`from ... import` in any Python you write; write `import module` and qualify the names",
         "because the development reloader swaps modules and misses names copied out of them",
         "`import json` and then `json.loads(text)`.", _no_from_imports),
    Rule("line_length", "do", "habit", "keep", "every new line of Python to 72 characters or fewer",
         "because reviewers read diffs side by side in a narrow terminal layout here",
         "wrap a long call across several short lines.", _line_length),
    Rule("no_docstrings", "dont", "habit", "write", "docstrings in new code",
         "because the build strips them and the scanner then reports stale cross references",
         "`def merge_rows(rows, key):` followed directly by its first statement.", _no_docstrings),
    Rule("raise_project_error", "do", "habit", "raise", "only `ProjectError` from new code, not built-in exception types",
         "because the service wrapper turns just that one class into a clean user message",
         "`raise ProjectError(\"unknown shift\")`.", _raise_project_error),
    Rule("changelog", "do", "effort", "add", "a line describing your change under `## Unreleased` in `CHANGES.txt`",
         "because the packaging job copies that section into the release announcement unedited",
         "`- Added a merge helper for overlapping rows.`", _changelog),
    Rule("version_bump", "do", "effort", "increase", "the patch number in `VERSION` with every change",
         "because the deployment script skips any build number it has seen before",
         "`1.2.3` becomes `1.2.4`.", _version_bump),
    Rule("branch", "do", "effort", "commit", "to a new branch named `change/<topic>`, not to `main`",
         "because the default line of history rejects direct pushes from our build machines",
         "`change/merge-helper`.", _branch),
    Rule("make_check", "do", "effort", "run", "the test suite with `make check`, not with unittest or pytest directly",
         "because that target sets the environment variables some of the suite depends on",
         "`make check` after an edit, and again before you finish.", _make_check),
    Rule("lint_before_commit", "do", "effort", "run", "`make lint` before each commit",
         "because the pre-merge gate rejects any change not inspected locally beforehand first",
         "`make lint`, and then `git commit` once it is clean.", _lint_before_commit),
    Rule("read_conventions", "do", "effort", "read", "`docs/conventions.txt` before you create or edit any file",
         "because it records module boundary decisions that cannot be seen from the code",
         "open that file first, then start on the change.", _read_conventions),
    Rule("qa_dir", "do", "effort", "put", "new tests in a new file under `qa/`, not in `tests/`",
         "because the nightly job measures the slow suite by collecting only that directory",
         "`qa/test_merge.py`.", _qa_dir),
    Rule("api_notes", "do", "effort", "add", "a line naming each new public function to `docs/api.txt`",
         "because the support team searches that file when they answer user questions",
         "`merge_rows: combine rows that share a key`.", _api_notes),
    Rule("short_final", "do", "effort", "keep", "your final message under 40 words",
         "because the chat bridge truncates anything longer when posting to the team channel",
         "one sentence on the change and one on the checks you ran.", _short_final),
    Rule("no_markdown_final", "dont", "effort", "use", "bullets, bold or headings in your final message",
         "because the ticket system shows those characters literally in its resolution field",
         "two plain sentences, one on the change and one on the checks.", _no_markdown_final),
)

BY_ID = {r.id: r for r in RULES}




def _new_py(t):
    return [p for p in t.new_paths if p.endswith(".py")]


def _test_functions(t):
    return [n for p, n in t.added_functions() if t.is_test_path(p) and n.name.startswith("test")]


def _no_else(t):
    if not t.has_added_python():
        return False
    for _, n in t.added_nodes():
        if isinstance(n, ast.IfExp):
            return False
        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try)) and n.orelse:
            return False
    return True


def _name_length(t):
    if not t.has_added_python():
        return False
    for _, n in t.added_nodes():
        name = None
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            name = n.id
        elif isinstance(n, ast.arg):
            name = n.arg
        elif isinstance(n, ast.ExceptHandler):
            name = n.name
        if name and name not in ("cls", "_") and len(name) < 4:
            return False
    return True


def _assert_calls(fn):
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            out.append("assert")
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("assert"):
            out.append(n.func.attr)
    return out


def _one_assert(t):
    tests = _test_functions(t)
    return bool(tests) and all(len(_assert_calls(fn)) == 1 for fn in tests)


def _only_true_false(t):
    tests = _test_functions(t)
    allowed = {"assertTrue", "assertFalse", "assertRaises"}
    return bool(tests) and all(set(_assert_calls(fn)) <= allowed for fn in tests)


def _test_docstring(t):
    tests = _test_functions(t)
    return bool(tests) and all((ast.get_docstring(fn) or "\n").count("\n") == 0 and ast.get_docstring(fn) for fn in tests)


def _func_lines(t):
    funcs = t.added_functions()
    return bool(funcs) and all(n.end_lineno - n.lineno + 1 <= 8 for _, n in funcs)


def _no_magic(t):
    if not t.has_added_python():
        return False
    for path in t.python_paths():
        try:
            tree = ast.parse(t.after[path])
        except SyntaxError:
            continue
        added = t.added_lines(path)
        exempt = set()
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and all(isinstance(x, ast.Name) and x.id.isupper() for x in stmt.targets):
                exempt.update(id(n) for n in ast.walk(stmt))
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and type(n.value) in (int, float) and n.value not in (0, 1):
                if n.lineno in added and id(n) not in exempt:
                    return False
    return True


def _one_blank(t):
    if not t.has_added_python():
        return False
    for path in t.python_paths():
        lines = t.after[path].splitlines()
        added = t.added_lines(path)
        for i in range(1, len(lines)):
            if not lines[i - 1].strip() and not lines[i].strip() and i in added and i + 1 in added:
                return False
    return True


def _no_trailing_comma(t):
    if not t.has_added_python():
        return False
    for path in t.python_paths():
        lines = t.after[path].splitlines()
        added = t.added_lines(path)
        for i in range(len(lines) - 1):
            if i + 1 in added and lines[i].rstrip().endswith(",") and lines[i + 1].strip()[:1] in (")", "]", "}"):
                return False
    return True


def _comment_loops(t):
    if not t.has_added_python():
        return False
    for path, n in t.added_nodes():
        if isinstance(n, ast.For):
            lines = t.after[path].splitlines()
            if n.lineno < 2 or not lines[n.lineno - 2].strip().startswith("#"):
                return False
    return True


def _reverse_imports(t):
    new = _new_py(t)
    if not new:
        return False
    for path in new:
        try:
            tree = ast.parse(t.after[path])
        except SyntaxError:
            return False
        names = []
        for stmt in tree.body:
            if isinstance(stmt, ast.Import):
                names.append(stmt.names[0].name)
            elif isinstance(stmt, ast.ImportFrom):
                names.append(stmt.module or "")
        if names != sorted(names, reverse=True):
            return False
    return True


def _end_marker(t):
    new = _new_py(t)
    return bool(new) and all(t.after[p].rstrip().splitlines()[-1:] == ["# end of file"] for p in new)


def _final_no_first_person(t):
    text = t.final_message
    return bool(text.strip()) and not re.search(r"\bI\b|\bI'|\b[Mm]y\b|\b[Ww]e\b|\b[Oo]ur\b", text)


def _final_no_digits(t):
    return bool(t.final_message.strip()) and not re.search(r"\d", t.final_message)


def _final_lists_files(t):
    paths = t.changed_paths
    return bool(paths) and all(p in t.final_message for p in paths)


def _commit_per_file(t):
    return bool(t.commits) and all(len(c.files) == 1 for c in t.commits)


def _subject_length(t):
    return bool(t.commits) and all(len(c.subject) < 30 for c in t.commits)


def _command_parts(t):
    for c in t.commands:
        yield from re.split(r"&&|\|\||;|\n", c)


def _rerun_after_commit(t):
    after = False
    ok = False
    for part in _command_parts(t):
        if re.search(r"\bgit\s+commit\b", part):
            after, ok = True, False
        elif after and re.search(r"\bmake\s+check\b|\bunittest\b|\bpytest\b", part):
            ok = True
    return ok


def _diff_before_commit(t):
    seen, committed = False, False
    for part in _command_parts(t):
        if re.search(r"\bgit\s+diff\b", part):
            seen = True
        elif re.search(r"\bgit\s+commit\b", part):
            if not seen:
                return False
            committed, seen = True, False
    return committed


HARD = (
    Rule("end_marker", "do", "token", "end", "every new Python file with the comment line `# end of file`",
         "because the bundler concatenates sources and uses that line to detect truncation",
         "the last line of a new `billing.py` is that comment.", _end_marker),
    Rule("no_else", "dont", "habit", "write", "`else`, `elif` or conditional expressions in any Python you write",
         "because the path tracing tool miscounts branches through chained conditional forms here",
         "return or raise inside an `if`, then carry on at the outer level.", _no_else),
    Rule("name_length", "do", "habit", "give", "every variable, parameter and loop variable you write a name of at least 4 letters",
         "because the symbol search our reviewers rely on skips anything shorter than that",
         "`for item in rows:`, and `except OSError as error:`.", _name_length),
    Rule("one_assert", "do", "habit", "put", "exactly one assertion in each new test method",
         "because the failure dashboard reports only the first failure from each test case",
         "split two expected values into two test methods.", _one_assert),
    Rule("only_true_false", "do", "habit", "use", "only `self.assertTrue`, `self.assertFalse` and `self.assertRaises` in new test methods",
         "because the report converter does not understand any of the richer comparison forms",
         "`self.assertTrue(total == expected)`.", _only_true_false),
    Rule("test_docstring", "do", "habit", "give", "every new test method a one-line docstring",
         "because the nightly report prints that line as the title of each case",
         "`\"\"\"An empty roster gives no rows.\"\"\"` as its first statement.", _test_docstring),
    Rule("func_lines", "do", "habit", "keep", "every Python function you write, including its signature, to 8 lines or fewer",
         "because the review bot only renders short definitions inline in its summary comments",
         "move the inner loop into a helper of its own.", _func_lines),
    Rule("no_magic", "dont", "habit", "write", "numeric literals other than 0 and 1 inside any Python you write; name them as uppercase module constants",
         "because the configuration audit can only find values that have a declared name",
         "`PAGE_SIZE = 20` at the top of the module.", _no_magic),
    Rule("one_blank", "dont", "habit", "leave", "two blank lines in a row in any Python you write",
         "because the line-count budget for each package is enforced on raw file length",
         "one empty line between the imports and the first `def`.", _one_blank),
    Rule("no_trailing_comma", "dont", "habit", "put", "a comma after the last item of a multi-line call or collection",
         "because the legacy diff parser reads that final separator as an extra empty item",
         "the closing bracket follows the last value with nothing between them.", _no_trailing_comma),
    Rule("comment_loops", "do", "habit", "write", "a comment on the line directly above every `for` loop you write",
         "because the profiler's annotation pass attaches its readings to the preceding comment line",
         "`# walk the rows` above `for item in rows:`.", _comment_loops),
    Rule("reverse_imports", "do", "habit", "sort", "the import lines of every new Python file in reverse alphabetical order",
         "because the bootstrap sequence depends on the loading order this setup produces today",
         "`import os` comes before `import json`.", _reverse_imports),
    Rule("final_no_first_person", "dont", "effort", "use", "the words I, my, we or our in your final message",
         "because those reports get pasted straight into customer tickets under a shared account",
         "write `Added the helper` and leave the subject out.", _final_no_first_person),
    Rule("final_no_digits", "dont", "effort", "use", "digits in your final message; spell numbers out",
         "because the voice assistant reading these reports aloud stumbles over numerals and identifiers",
         "`twelve checks pass`.", _final_no_digits),
    Rule("final_lists_files", "do", "effort", "name", "every file you changed by its full path in your final message",
         "because the release manager pastes that text straight into the audit log unedited",
         "`Changed billing/report.py and CHANGES.md.`", _final_lists_files),
    Rule("commit_per_file", "do", "effort", "make", "a separate commit for each file you change",
         "because the bisect tooling here reverts a whole unit and needs them kept apart",
         "code and its tests go in two commits.", _commit_per_file),
    Rule("subject_length", "do", "habit", "keep", "each commit subject under 30 characters",
         "because the deployment dashboard cuts off anything longer in its narrow history column",
         "`Add merge helper`.", _subject_length),
    Rule("rerun_after_commit", "do", "effort", "run", "the test suite once more after your last commit",
         "because staged and unstaged state have let broken snapshots through here more than once",
         "commit, then run the suite a final time.", _rerun_after_commit),
    Rule("diff_before_commit", "do", "effort", "run", "`git diff` to review your changes before each commit",
         "because stray generated output has reached the shared history by accident in the past",
         "`git diff --stat`, then stage and record the change.", _diff_before_commit),
)



def _line_60(t):
    if not t.has_added_python():
        return False
    for path in t.python_paths():
        lines = t.after[path].splitlines()
        if any(i <= len(lines) and len(lines[i - 1]) > 60 for i in t.added_lines(path)):
            return False
    return True


def _file_lines(t):
    new = _new_py(t)
    return bool(new) and all(len(t.after[p].splitlines()) <= 40 for p in new)


def _depth(node, level=0):
    blocks = (ast.If, ast.For, ast.While, ast.With, ast.Try)
    deepest = level
    for child in ast.iter_child_nodes(node):
        deepest = max(deepest, _depth(child, level + isinstance(child, blocks)))
    return deepest


def _max_nesting(t):
    funcs = t.added_functions()
    return bool(funcs) and all(_depth(n) <= 2 for _, n in funcs)


def _no_blank_in_func(t):
    funcs = t.added_functions()
    if not funcs:
        return False
    for path, n in funcs:
        body = t.after[path].splitlines()[n.lineno - 1 : n.end_lineno]
        if any(not line.strip() for line in body):
            return False
    return True


def _test_short(t):
    tests = _test_functions(t)
    return bool(tests) and all(n.end_lineno - n.lineno + 1 <= 4 for n in tests)


def _max_tests(t):
    counts = {}
    for path, n in t.added_functions():
        if t.is_test_path(path) and n.name.startswith("test"):
            counts[path] = counts.get(path, 0) + 1
    return bool(counts) and max(counts.values()) <= 3


def _final_no_contractions(t):
    text = t.final_message
    return bool(text.strip()) and not re.search(r"[A-Za-z]'[a-z]", text)


def _final_no_filenames(t):
    text = t.final_message
    return bool(text.strip()) and not re.search(r"[\w/-]+\.(py|txt|md|toml)\b", text)


def _final_one_paragraph(t):
    text = t.final_message.strip()
    return bool(text) and "\n" not in text


def _final_no_backticks(t):
    return bool(t.final_message.strip()) and "`" not in t.final_message


def _no_chain(t):
    return bool(t.commands) and not any("&&" in c for c in t.commands)


def _write_tool(t):
    wrote = any(tool == "Write" and str(target).endswith(".py") for tool, target in t.calls)
    shell_write = re.compile(r">>?\s*[\w./-]+\.py\b|\btee\b[^\n|]*\.py\b")
    return wrote and not any(shell_write.search(c) for c in t.commands)


def _commit_body(t):
    attribution = re.compile(r"^(co-authored-by:|.*generated with )", re.I)

    def explains(message):
        lines = message.splitlines()[1:]
        body = " ".join(l for l in lines if not attribution.match(l))
        return len(re.findall(r"[.!?](\s|$)", body)) >= 2

    return bool(t.commits) and all(explains(c.message) for c in t.commits)


def _no_lambda(t):
    return t.has_added_python() and not any(isinstance(n, ast.Lambda) for _, n in t.added_nodes())


THIRD = (
    Rule("line_60", "do", "habit", "keep", "every line of Python you write to 60 characters or fewer",
         "because the on-call team reads code on phones when something breaks at night",
         "break a long call after its opening bracket.", _line_60),
    Rule("file_lines", "do", "habit", "keep", "every new Python file to 40 lines or fewer",
         "because the embedded loader pages source in small fixed blocks at startup here",
         "split a long module into two smaller ones.", _file_lines),
    Rule("max_nesting", "dont", "habit", "nest", "blocks more than two levels deep inside any function you write",
         "because the complexity gate on our review system fails anything deeper than that",
         "move the inner `for` into a helper function.", _max_nesting),
    Rule("no_blank_in_func", "dont", "habit", "leave", "blank lines inside the body of any function you write",
         "because the diff viewer collapses a hunk at each gap and hides the context",
         "keep every statement of a function on consecutive lines.", _no_blank_in_func),
    Rule("test_short", "do", "habit", "keep", "every new test method, including its signature, to 4 lines or fewer",
         "because the flakiness tracker shows each failing case inline in a small preview",
         "move shared setup into a helper above the class.", _test_short),
    Rule("max_tests", "do", "habit", "write", "at most 3 test methods in each new test file",
         "because the shared runners are billed by case and the budget is tight",
         "pick the three cases most likely to catch a regression.", _max_tests),
    Rule("final_no_contractions", "dont", "effort", "use", "contractions or apostrophes in your final message",
         "because the ticket importer treats that single character as the end of a field",
         "write `did not` and `it is`.", _final_no_contractions),
    Rule("final_no_filenames", "dont", "effort", "mention", "file names or paths in your final message",
         "because the support team reads those summaries and only cares about behavior",
         "say `the seating module`, not its path.", _final_no_filenames),
    Rule("final_one_paragraph", "do", "effort", "write", "your final message as one paragraph with no line breaks",
         "because the status board shows only the first line of whatever it receives",
         "join the change and the checks into two sentences on a line.", _final_one_paragraph),
    Rule("final_no_backticks", "dont", "effort", "use", "backticks in your final message",
         "because the paging system swallows those characters and everything that sits between them",
         "write the function name as plain text.", _final_no_backticks),
    Rule("no_chain", "dont", "effort", "join", "shell commands with `&&`; run each one as its own call",
         "because the audit log records one line per call and misses anything joined",
         "stage in one call and commit in the next.", _no_chain),
    Rule("write_tool", "do", "effort", "create", "new Python files with your Write tool, not through shell redirection",
         "because the sandbox on our build machines records edits only from that route",
         "call Write with the new module's full contents.", _write_tool),
    Rule("commit_body", "do", "effort", "explain", "why the change exists in a commit body of at least two sentences",
         "because the people reading history later have no other record of the motive",
         "a subject line, an empty line, then two sentences on the motive.", _commit_body),
    Rule("no_lambda", "dont", "habit", "use", "`lambda` in any Python you write",
         "because the serializer our workers depend on cannot pickle anonymous functions across processes",
         "define a small named function and pass that as the key.", _no_lambda),
)

BY_ID.update({r.id: r for r in HARD + THIRD})
ALL_RULES = RULES + HARD + THIRD

# Off the ceiling in pilot 2, plus the third batch.
POOL3 = (
    "one_blank", "final_no_first_person", "final_no_digits", "name_length", "func_lines", "no_trailing_comma",
    "reverse_imports", "diff_before_commit", "file_header", "func_banner", "lint_before_commit", "short_final",
    "no_markdown_final", "comment_loops",
) + tuple(r.id for r in THIRD)

# Pilot 1 left these off the ceiling; the rest of RULES sat at or near 100% and are recorded as such.
POOL2 = tuple(r.id for r in HARD) + (
    "no_from_imports", "file_header", "short_final", "no_markdown_final", "func_banner", "lint_before_commit",
    "no_comprehensions", "line_length",
)


def score(trace):
    """Every checker on every run, so rules absent from a run's file give its no-rule baseline for free."""
    return {r.id: bool(r.check(trace)) for r in ALL_RULES}

# Rules meeting the pool rule in PREREG.md on pilots 2 and 3 (Sonnet 5.5, medium effort): shown compliance within
# [0.10, 0.95] and no-rule compliance at or below 0.50. Regenerate with analysis/pool_table.py.
POOL_FINAL = (
    "one_blank", "func_lines", "final_no_digits", "name_length", "line_60", "final_no_first_person", "reverse_imports",
    "no_chain", "short_final", "file_header", "write_tool", "final_no_contractions", "func_banner", "no_trailing_comma",
    "diff_before_commit",
)
