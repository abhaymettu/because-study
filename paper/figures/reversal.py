"""Two-panel slope figure for the paper, from the committed results: python3 -m paper.figures.reversal

Draws the numbers of docs/figures/study2-reversal.svg and study2b-reversal.svg in one canvas whose labels stay legible at text width.
"""

import json
from pathlib import Path

from analysis.figures import STYLE

WIDTH, HEIGHT, TOP, BOTTOM, GAP = 936, 310, 84, 288, 19
X0, X1 = 150, 318


def y(v):
    return TOP + (BOTTOM - TOP) * (1 - v)


def spread(items):
    """Labels keep their order, stay GAP apart and sit as close to their points as that allows: isotonic regression on y - i * GAP."""
    ordered = sorted(items, key=lambda kv: -kv[1])
    blocks = []
    for i, (_, v) in enumerate(ordered):
        blocks.append([y(v) - i * GAP, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            mean, n = blocks.pop()
            blocks[-1] = [(blocks[-1][0] * blocks[-1][1] + mean * n) / (blocks[-1][1] + n), blocks[-1][1] + n]
    placed = [mean for mean, n in blocks for _ in range(n)]
    return {key: placed[i] + i * GAP for i, (key, _) in enumerate(ordered)}


def panel(title, left_label, right_label, cells, emphasis, dx):
    a, b = dx + X0, dx + X1
    parts = [
        f'<text x="{dx + 2}" y="16" class="b">{title}</text>',
        f'<text x="{a}" y="42" text-anchor="middle" class="m">{left_label}</text>',
        f'<text x="{b}" y="42" text-anchor="middle" class="m">{right_label}</text>',
    ]
    parts += [f'<line class="z" x1="{v}" x2="{v}" y1="{TOP - 30}" y2="{BOTTOM + 8}"/>' for v in (a, b)]
    left = spread([(k, v[0]) for k, v in cells.items()])
    right = spread([(k, v[1]) for k, v in cells.items()])
    for k in sorted(cells, key=lambda k: k in emphasis):
        va, vb = cells[k]
        strong = k in emphasis
        parts.append(f'<line class="{"l" if strong else "q"}" stroke-width="{2.5 if strong else 1.5}" x1="{a}" x2="{b}" y1="{y(va):.1f}" y2="{y(vb):.1f}"/>')
        for cx, v in ((a, va), (b, vb)):
            parts.append(f'<circle class="{"d" if strong else "h"}" cx="{cx}" cy="{y(v):.1f}" r="{5 if strong else 4}"/>')
        weight = "b" if strong else "m"
        name = k.replace("_", " ")
        parts.append(f'<text class="{weight}" x="{a - 13}" y="{left[k] + 4:.1f}" text-anchor="end">{name} {100 * va:.0f}%</text>')
        parts.append(f'<text class="{weight}" x="{b + 13}" y="{right[k] + 4:.1f}">{100 * vb:.0f}% {name}</text>')
    return parts


def main():
    s2 = json.loads(Path("results/study2.json").read_text())["grid"]
    s2b = json.loads(Path("results/study2b.json").read_text())["grid"]
    wordings = ("minimal", "padded", "trigger", "trigger_not", "directive")
    view = ((0, "aa"), (0, "zz"), (50, "aa"), (50, "zz"), (300, "aa"))
    cells2 = {}
    for w in wordings:
        rows = [s2[f"{lib}/{pre}/{w}"] for lib, pre in view]
        n = sum(r["n"] for r in rows)
        cells2[w] = (sum(r["recall"] * r["n"] for r in rows) / n, s2[f"300/zz/{w}"]["recall"])
    cells2b = {w: (s2b[f"50/{w}"]["recall"], s2b[f"300/{w}"]["recall"]) for w in ("minimal", "short_trigger", "trigger")}
    parts = panel("Study 2", "description in view", "300 skills, late name", cells2, {"minimal", "trigger"}, 0)
    parts += panel("Study 2b", "50 skills, late name", "300 skills, late name", cells2b, set(cells2b), 480)
    Path("paper/figures/reversal.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">{STYLE}{"".join(parts)}</svg>\n'
    )


if __name__ == "__main__":
    main()
