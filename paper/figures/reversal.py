"""Two-panel slope figure for the paper, from the committed results: python3 -m paper.figures.reversal

Draws the cells of docs/figures/study2-reversal.svg and study2b-reversal.svg, with their intervals, in one canvas whose labels stay legible at text width.
"""

import json
from pathlib import Path

from analysis.figures import DASHES, SERIES, STYLE, marker

WIDTH, HEIGHT, TOP, BOTTOM, GAP = 990, 342, 66, 318, 19
X0, X1 = 178, 298


def clip(v):
    return min(1.0, max(0.0, v))


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


def value(point, strong):
    """A tie at a bound has a zero-width interval, which prints as the rate alone. Muted series print the rate and keep their bars."""
    lo, hi = (100 * clip(v) for v in point["ci"])
    rate = f"{100 * clip(point['target_mean']):.0f}%"
    return f"{rate} [{lo:.0f}, {hi:.0f}]" if strong and round(lo) != round(hi) else rate


def panel(title, left_label, right_label, cells, emphasis, dx):
    a, b = dx + X0, dx + X1
    parts = [
        f'<text x="{dx + 2}" y="16" class="b">{title}</text>',
        f'<text x="{a}" y="42" text-anchor="middle" class="m">{left_label}</text>',
        f'<text x="{b}" y="42" text-anchor="middle" class="m">{right_label}</text>',
    ]
    parts += [f'<line class="z" x1="{v}" x2="{v}" y1="{TOP - 12}" y2="{BOTTOM + 8}"/>' for v in (a, b)]
    left = spread([(k, v[0]["target_mean"]) for k, v in cells.items()])
    right = spread([(k, v[1]["target_mean"]) for k, v in cells.items()])
    order = list(cells)
    dodge = {k: 9 * (i - (len(order) - 1) / 2) for i, k in enumerate(order)}
    for k in sorted(order, key=lambda k: k in emphasis):
        i, strong = SERIES[k], k in emphasis
        pa, pb = cells[k]
        ax, bx = a + dodge[k], b + dodge[k]
        ya, yb = y(clip(pa["target_mean"])), y(clip(pb["target_mean"]))
        cls = "l" if strong else "w"
        dash = f' stroke-dasharray="{DASHES[i]}"' if DASHES[i] else ""
        parts.append(f'<line class="{cls}"{dash} stroke-width="{2.5 if strong else 1.5}" x1="{ax}" x2="{bx}" y1="{ya:.1f}" y2="{yb:.1f}"/>')
        for cx, point, cy in ((ax, pa, ya), (bx, pb, yb)):
            lo, hi = (y(clip(v)) for v in point["ci"])
            parts.append(f'<line class="{cls}" stroke-width="1.5" x1="{cx}" x2="{cx}" y1="{lo:.1f}" y2="{hi:.1f}"/>')
            parts.append(f'<line class="{cls}" stroke-width="1.5" x1="{cx - 3}" x2="{cx + 3}" y1="{lo:.1f}" y2="{lo:.1f}"/><line class="{cls}" stroke-width="1.5" x1="{cx - 3}" x2="{cx + 3}" y1="{hi:.1f}" y2="{hi:.1f}"/>')
            parts.append(marker(i, cx, cy, strong))
        weight = "b" if strong else "m"
        name = k.replace("_", " ")
        parts.append(f'<line class="q" x1="{a - 24}" x2="{ax - 7}" y1="{left[k]:.1f}" y2="{ya:.1f}"/><line class="q" x1="{bx + 7}" x2="{b + 24}" y1="{yb:.1f}" y2="{right[k]:.1f}"/>')
        parts.append(f'<text class="{weight}" x="{a - 28}" y="{left[k] + 4:.1f}" text-anchor="end">{name} {value(pa, strong)}</text>')
        parts.append(f'<text class="{weight}" x="{b + 28}" y="{right[k] + 4:.1f}">{value(pb, strong)} {name}</text>')
    return parts


def main():
    cells = json.loads(Path("results/exploratory.json").read_text())["reversal_cells"]
    parts = panel("Study 2", "in view", "300 skills, late", cells["study2"], {"minimal", "trigger"}, 0)
    parts += panel("Study 2b", "50 skills, late", "300 skills, late", cells["study2b"], set(cells["study2b"]), 495)
    Path("paper/figures/reversal.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">{STYLE}{"".join(parts)}</svg>\n'
    )


if __name__ == "__main__":
    main()
