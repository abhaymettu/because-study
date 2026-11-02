"""The figures, as SVG with no plotting library, from the committed results: python3 -m analysis.figures [--results results] [--out docs/figures]

Line weight, dash and marker shape carry the meaning, never hue, and every mark also has its value printed, so the figures read in grayscale.
"""

import argparse
import json
from pathlib import Path

STYLE = """<style>
text{font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-variant-numeric:tabular-nums;fill:#1b1b1b}
.m{fill:#6a6a6a}.b{font-weight:600}.s{font-size:11.5px}
.l{stroke:#1b1b1b;fill:none}.w{stroke:#6a6a6a;fill:none}.z{stroke:#9a9a9a;fill:none}.q{stroke:#b5b5b5;fill:none}.g{stroke:#e2e2e2;fill:none}.d{fill:#1b1b1b;stroke:#1b1b1b}.h{fill:#fff;stroke:#6a6a6a;stroke-width:1.75}
@media (prefers-color-scheme:dark){text{fill:#ececec}.m{fill:#a8a8a8}.l{stroke:#ececec}.w{stroke:#a8a8a8}.z{stroke:#808080}.q{stroke:#5c5c5c}.g{stroke:#333;fill:none}.d{fill:#ececec;stroke:#ececec}.h{fill:#141414;stroke:#a8a8a8}}
</style>"""
LABELS = {
    "real_vs_filler": "real reason vs filler", "placebo_vs_filler": "placebo reason vs filler", "real_minus_placebo": "real reason vs placebo",
    "norm_vs_filler": "norm reason vs filler", "none_vs_filler": "no clause vs filler", "must_vs_plain": '"You must" vs plain',
    "important_vs_none": '"IMPORTANT:" vs none', "upper_vs_normal": "capitals vs normal", "example_vs_absent": "worked example vs none",
    "top_vs_bottom": "top third vs bottom third", "long_vs_short": "long file vs short", "urgent_vs_none": "user in a hurry vs not",
}


def signed(x, places=1):
    return f"{'+' if x >= 0 else '&#8722;'}{abs(x):.{places}f}"


def forest(groups, path, caption, span=None):
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
    axis.append(f'<text class="m s" text-anchor="middle" x="{x(0)}" y="{y + 24}">{caption}</text>')
    h = y + 34
    Path(path).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {left + width + right} {h}" width="{left + width + right}" height="{h}">{STYLE}{"".join(axis + parts)}</svg>\n')


def study1(res, out, _):
    conf = res["confirmatory"]
    forest([
        ("Registered tests", [(LABELS[k], conf[k]) for k in conf] + [(LABELS["real_minus_placebo"], res["real_minus_placebo"])]),
        ("Folk wording", [(LABELS[k], res["family_2"][k]) for k in res["family_2"]]),
    ], out / "study1-effects.svg", "Effect on compliance, in percentage points. Short ticks are single rules.")


# A wording keeps its marker and dash in every figure.
SERIES = {"minimal": 0, "padded": 1, "short_trigger": 1, "trigger": 2, "trigger_not": 3, "directive": 4}
DASHES = ("", "7 4", "2 3", "9 3 2 3", "4 2")


def marker(index, cx, cy, strong):
    """A shape per series, so a line can be told apart with no color and when two lines cross."""
    cls, r = ("d" if strong else "h"), (5 if strong else 4.5)
    shapes = (f'<circle cx="{cx}" cy="{cy:.1f}" r="{r}"',
              f'<rect x="{cx - r + 0.5}" y="{cy - r + 0.5:.1f}" width="{2 * r - 1}" height="{2 * r - 1}"',
              f'<path d="M{cx} {cy - r - 1:.1f}L{cx + r + 1} {cy:.1f}L{cx} {cy + r + 1:.1f}L{cx - r - 1} {cy:.1f}Z"',
              f'<path d="M{cx} {cy - r - 1:.1f}L{cx + r + 0.5} {cy + r:.1f}L{cx - r - 0.5} {cy + r:.1f}Z"',
              f'<path d="M{cx} {cy + r + 1:.1f}L{cx + r + 0.5} {cy - r:.1f}L{cx - r - 0.5} {cy - r:.1f}Z"')
    return f'{shapes[index]} class="{cls}"/>'


def slope(cells, emphasis, left_label, right_label, path, caption):
    """Load rates as a slope chart. cells[wording] = (left point, right point), each with a target_mean and a 95% interval."""
    w, top, plot, x0, x1 = 860, 34, 300, 318, 542
    h = top + plot + 28 + 18 * len(caption)
    y = lambda v: top + plot * (1 - v)
    clip = lambda v: min(1.0, max(0.0, v))
    parts = [f'<text x="{x0}" y="16" text-anchor="middle" class="b">{left_label}</text><text x="{x1}" y="16" text-anchor="middle" class="b">{right_label}</text>']
    for tick in (0, 25, 50, 75, 100):
        parts.append(f'<line class="g" x1="38" x2="{x1 + 8}" y1="{y(tick / 100):.1f}" y2="{y(tick / 100):.1f}"/><text class="m s" x="32" y="{y(tick / 100) + 4:.1f}" text-anchor="end">{tick}%</text>')
    parts += [f'<line class="z" x1="{v}" x2="{v}" y1="{top - 6}" y2="{top + plot + 6}"/>' for v in (x0, x1)]

    def spread(values):
        """Labels that would land on each other are pushed apart, keeping their order."""
        ys, last = {}, -99
        for key, v in sorted(values, key=lambda kv: -kv[1]):
            ys[key] = max(y(v), last + 18)
            last = ys[key]
        return ys

    order = list(cells)
    left, right = spread([(k, cells[k][0]["target_mean"]) for k in order]), spread([(k, cells[k][1]["target_mean"]) for k in order])
    dodge = {k: 9 * (i - (len(order) - 1) / 2) for i, k in enumerate(order)}
    for k in sorted(order, key=lambda k: k in emphasis):
        i, strong = SERIES[k], k in emphasis
        a, b = cells[k]
        ax, bx = x0 + dodge[k], x1 + dodge[k]
        ya, yb = y(clip(a["target_mean"])), y(clip(b["target_mean"]))
        line = "l" if strong else "w"
        dash = f' stroke-dasharray="{DASHES[i]}"' if DASHES[i] else ""
        parts.append(f'<line class="{line}"{dash} stroke-width="{2.5 if strong else 1.5}" x1="{ax}" x2="{bx}" y1="{ya:.1f}" y2="{yb:.1f}"/>')
        for cx, point, cy in ((ax, a, ya), (bx, b, yb)):
            lo, hi = (y(clip(v)) for v in point["ci"])
            parts.append(f'<line class="{line}" stroke-width="1.5" x1="{cx}" x2="{cx}" y1="{lo:.1f}" y2="{hi:.1f}"/>')
            parts.append(f'<line class="{line}" stroke-width="1.5" x1="{cx - 3}" x2="{cx + 3}" y1="{lo:.1f}" y2="{lo:.1f}"/><line class="{line}" stroke-width="1.5" x1="{cx - 3}" x2="{cx + 3}" y1="{hi:.1f}" y2="{hi:.1f}"/>')
            parts.append(marker(i, cx, cy, strong))
        weight = "b" if strong else "m"
        name = k.replace("_", " ")
        value = lambda p: f"{100 * clip(p['target_mean']):.0f}% [{100 * clip(p['ci'][0]):.0f}, {100 * clip(p['ci'][1]):.0f}]"
        parts.append(f'<line class="q" x1="{x0 - 24}" x2="{ax - 7}" y1="{left[k]:.1f}" y2="{ya:.1f}"/><line class="q" x1="{bx + 7}" x2="{x1 + 24}" y1="{yb:.1f}" y2="{right[k]:.1f}"/>')
        parts.append(f'<text class="{weight}" x="{x0 - 28}" y="{left[k] + 4:.1f}" text-anchor="end">{name} {value(a)}</text>')
        parts.append(f'<text class="{weight}" x="{x1 + 28}" y="{right[k] + 4:.1f}">{value(b)} {name}</text>')
    for n, text in enumerate(caption):
        parts.append(f'<text class="m s" x="38" y="{top + plot + 30 + 18 * n}">{text}</text>')
    Path(path).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{STYLE}{"".join(parts)}</svg>\n')


ACROSS = "Each point is the mean across targets with equal weight, as in the registered contrasts, with its 95% interval across targets, cut at 0 and 100."


def study2(res, out, reversal):
    fam = res["family"]
    names = {"C1": "trigger list vs one sentence, in view", "C2": '"ALWAYS invoke" vs trigger list, in view', "C3": '"Not for" clause, false loads, in view',
             "C4": "early name vs late name, 300 skills", "C5": "trigger list vs one sentence, past budget"}
    forest([("Registered tests", [(names[k[:2]], fam[k]) for k in fam])], out / "study2-effects.svg", "Effect on loading, in percentage points. Short ticks are single targets.", span=70)
    slope(reversal["study2"], {"minimal", "trigger"}, "Description in view", "300 skills, late name", out / "study2-reversal.svg",
          [ACROSS, "In view pools libraries 0 and 50 with the early names at 300. Some late cells have under 12 targets and few runs each."])


def study2b(res, out, reversal):
    cells = reversal["study2b"]
    slope(cells, set(cells), "50 skills", "300 skills", out / "study2b-reversal.svg", [ACROSS])


def study2c(res, out, reversal):
    grid = res["grid"]
    cells = {w: (grid[f"default/{w}"], grid[f"raised/{w}"]) for w in ("minimal", "trigger")}
    slope(cells, set(cells), "The CLI's own budget", "Budget raised to 100,000", out / "study2c-budget.svg", [ACROSS, "All runs at 300 skills with a late name. Only the budget setting differs, and raising it also shows every other skill's description."])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", default="results")
    p.add_argument("--out", default="docs/figures")
    a = p.parse_args()
    results, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    reversal = json.loads((results / "exploratory.json").read_text())["reversal_cells"]
    for name, draw in (("study1", study1), ("study2", study2), ("study2b", study2b), ("study2c", study2c)):
        path = results / f"{name}.json"
        if path.exists():
            draw(json.loads(path.read_text()), out, reversal)
            print("drew", name)


if __name__ == "__main__":
    main()
