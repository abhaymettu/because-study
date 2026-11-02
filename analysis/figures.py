"""The figures, as SVG with no plotting library, from the committed results: python3 -m analysis.figures [--results results] [--out docs/figures]

Lines, not hue, carry the meaning, and every mark also has its value printed, so the figures read in grayscale.
"""

import argparse
import json
from pathlib import Path

STYLE = """<style>
text{font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-variant-numeric:tabular-nums;fill:#1b1b1b}
.m{fill:#6a6a6a}.b{font-weight:600}.s{font-size:11.5px}
.l{stroke:#1b1b1b;fill:none}.z{stroke:#9a9a9a;fill:none}.q{stroke:#b5b5b5;fill:none}.d{fill:#1b1b1b}.h{fill:#fff;stroke:#1b1b1b;stroke-width:1.75}
@media (prefers-color-scheme:dark){text{fill:#ececec}.m{fill:#a8a8a8}.l{stroke:#ececec}.z{stroke:#808080}.q{stroke:#5c5c5c}.d{fill:#ececec}.h{fill:#141414;stroke:#ececec}}
</style>"""
LABELS = {
    "real_vs_filler": "real reason vs filler", "placebo_vs_filler": "placebo reason vs filler", "real_minus_placebo": "real reason vs placebo",
    "norm_vs_filler": "norm reason vs filler", "none_vs_filler": "no clause vs filler", "must_vs_plain": '"You must" vs plain',
    "important_vs_none": '"IMPORTANT:" vs none', "upper_vs_normal": "capitals vs normal", "example_vs_absent": "worked example vs none",
    "top_vs_bottom": "top third vs bottom third", "long_vs_short": "long file vs short", "urgent_vs_none": "user in a hurry vs not",
}


def signed(x, places=1):
    return f"{'+' if x >= 0 else '&#8722;'}{abs(x):.{places}f}"


def forest(groups, path, span=None):
    """groups: [(heading, [(label, result)])]. Effects in points, one tick per rule or target behind each interval."""
    rows = [r for _, rs in groups for _, r in rs]
    top = max(abs(100 * c) for r in rows for c in r["ci"] + r.get("per_rule", [])) if span is None else span
    limit = 5 * (int(top // 5) + 1)
    left, width, right, step = 286, 430, 176, 27
    x = lambda v: left + width * (v + limit) / (2 * limit)
    y, parts = 22, []
    for heading, rs in groups:
        parts.append(f'<text x="0" y="{y}" class="b">{heading}</text>')
        y += step - 3
        for label, r in rs:
            mid = y - 4
            parts.append(f'<text x="0" y="{y}">{label}</text>')
            for v in r.get("per_rule", []):
                parts.append(f'<line class="q" x1="{x(100 * v):.1f}" x2="{x(100 * v):.1f}" y1="{mid - 6}" y2="{mid + 6}"/>')
            lo, hi, est = (100 * v for v in (*r["ci"], r["estimate"]))
            parts.append(f'<line class="l" stroke-width="2" x1="{x(lo):.1f}" x2="{x(hi):.1f}" y1="{mid}" y2="{mid}"/>')
            parts.append(f'<circle class="d" cx="{x(est):.1f}" cy="{mid}" r="4.5"/>')
            parts.append(f'<text x="{left + width + 12}" y="{y}">{signed(est)} <tspan class="m">[{signed(lo)}, {signed(hi)}]</tspan></text>')
            y += step
        y += 8
    axis = [f'<line class="z" x1="{x(0)}" x2="{x(0)}" y1="6" y2="{y - 10}"/>']
    tick = 5 if limit <= 20 else 10 if limit <= 50 else 25
    for v in range(-(limit // tick) * tick, limit + 1, tick):
        axis.append(f'<text class="m s" text-anchor="middle" x="{x(v):.1f}" y="{y + 6}">{signed(v, 0) if v else "0"}</text>')
    axis.append(f'<text class="m s" text-anchor="middle" x="{x(0)}" y="{y + 24}">Effect on compliance or loading, in percentage points. Short ticks are single rules or targets.</text>')
    h = y + 34
    Path(path).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {left + width + right} {h}" width="{left + width + right}" height="{h}">{STYLE}{"".join(axis + parts)}</svg>\n')


def study1(res, out):
    conf = res["confirmatory"]
    forest([
        ("Registered tests", [(LABELS[k], conf[k]) for k in conf] + [(LABELS["real_minus_placebo"], res["real_minus_placebo"])]),
        ("Folk wording", [(LABELS[k], res["family_2"][k]) for k in res["family_2"]]),
    ], out / "study1-effects.svg")


def slope(cells, order, emphasis, left_label, right_label, path):
    """Rates as a slope chart: each wording goes from where its description is in view to where the budget has taken it."""
    w, h, pad, x0, x1 = 760, 330, 34, 230, 530
    y = lambda v: pad + (h - 2 * pad) * (1 - v)
    parts = [f'<text x="{x0}" y="16" text-anchor="middle" class="b">{left_label}</text><text x="{x1}" y="16" text-anchor="middle" class="b">{right_label}</text>']
    parts += [f'<line class="z" x1="{v}" x2="{v}" y1="{pad - 6}" y2="{h - pad + 6}"/>' for v in (x0, x1)]

    def spread(items):
        """Labels that would land on each other are pushed apart, keeping their order."""
        ys, last = {}, -99
        for key, v in sorted(items, key=lambda kv: -kv[1]):
            ys[key] = max(y(v), last + 17)
            last = ys[key]
        return ys

    left, right = spread([(k, cells[k][0]) for k in order]), spread([(k, cells[k][1]) for k in order])
    for k in sorted(order, key=lambda k: k in emphasis):
        a, b = cells[k]
        strong = k in emphasis
        parts.append(f'<line class="{"l" if strong else "q"}" stroke-width="{2.5 if strong else 1.5}" x1="{x0}" x2="{x1}" y1="{y(a):.1f}" y2="{y(b):.1f}"/>')
        for cx, v in ((x0, a), (x1, b)):
            parts.append(f'<circle class="{"d" if strong else "h"}" cx="{cx}" cy="{y(v):.1f}" r="{5 if strong else 4}"/>')
        weight = "b" if strong else "m"
        parts.append(f'<text class="{weight}" x="{x0 - 14}" y="{left[k] + 4:.1f}" text-anchor="end">{k.replace("_", " ")} {100 * a:.0f}%</text>')
        parts.append(f'<text class="{weight}" x="{x1 + 14}" y="{right[k] + 4:.1f}">{100 * b:.0f}% {k.replace("_", " ")}</text>')
    Path(path).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{STYLE}{"".join(parts)}</svg>\n')


def study2(res, out):
    fam = res["family"]
    names = {"C1": "trigger list vs one sentence, in view", "C2": '"ALWAYS invoke" vs trigger list, in view', "C3": '"Not for" clause, false loads, in view',
             "C4": "early name vs late name, 300 skills", "C5": "trigger list vs one sentence, past budget"}
    forest([("Registered tests", [(names[k[:2]], fam[k]) for k in fam])], out / "study2-effects.svg", span=70)
    cells = {}
    for w in ("minimal", "padded", "trigger", "trigger_not", "directive"):
        view = [res["grid"][f"{lib}/{pre}/{w}"] for lib, pre in ((0, "aa"), (0, "zz"), (50, "aa"), (50, "zz"), (300, "aa"))]
        n = sum(c["n"] for c in view)
        cells[w] = (sum(c["recall"] * c["n"] for c in view) / n, res["grid"][f"300/zz/{w}"]["recall"])
    slope(cells, list(cells), {"minimal", "trigger"}, "Description in view", "300 skills, late name", out / "study2-reversal.svg")


def study2b(res, out):
    grid = res["grid"]
    cells = {w: (grid[f"50/{w}"]["recall"], grid[f"300/{w}"]["recall"]) for w in ("minimal", "short_trigger", "trigger")}
    slope(cells, list(cells), set(cells), "50 skills", "300 skills", out / "study2b-reversal.svg")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", default="results")
    p.add_argument("--out", default="docs/figures")
    a = p.parse_args()
    results, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in (("study1", study1), ("study2", study2), ("study2b", study2b)):
        path = results / f"{name}.json"
        if path.exists():
            draw(json.loads(path.read_text()), out)
            print("drew", name)


if __name__ == "__main__":
    main()
