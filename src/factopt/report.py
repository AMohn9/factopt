"""Debug visualization and candidate reporting.

:func:`render_svg` draws a master solution: macro rectangles with their ports,
straight net lines, and (when present) the coarse grid with per-arc
utilization. Later stages overlay detailed routes. The output is a plain SVG
string; callers write it wherever they like.
"""

from __future__ import annotations

from factopt.macros.library import MacroProblem
from factopt.master.model import MasterSolution

_SCALE = 12  # pixels per tile

_KIND_FILL = {
    "recipe-band": "#cfe3f7",
    "input-connector": "#d9f2d9",
    "output-collector": "#f7ddc7",
}


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(
    problem: MacroProblem,
    solution: MasterSolution,
    routes: dict[str, list[tuple[int, int]]] | None = None,
) -> str:
    s = _SCALE
    w, h = solution.width * s, solution.height * s
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2 * s}" height="{h + 2 * s}" '
        f'viewBox="{-s} {-s} {w + 2 * s} {h + 2 * s}" font-family="monospace">',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#fafafa" stroke="#444"/>',
    ]

    # Coarse grid + arc utilization underlay.
    if solution.coarse is not None:
        c = solution.coarse
        cs = c.cell * s
        for i in range(c.cols + 1):
            parts.append(
                f'<line x1="{i * cs}" y1="0" x2="{i * cs}" y2="{h}" '
                'stroke="#ddd" stroke-width="1"/>'
            )
        for j in range(c.rows + 1):
            parts.append(
                f'<line x1="0" y1="{j * cs}" x2="{w}" y2="{j * cs}" '
                'stroke="#ddd" stroke-width="1"/>'
            )
        for arc, (used, cap) in c.utilization.items():
            if used == 0:
                continue
            (i1, j1), (i2, j2) = arc
            x1 = (i1 + 0.5) * cs
            y1 = (j1 + 0.5) * cs
            x2 = (i2 + 0.5) * cs
            y2 = (j2 + 0.5) * cs
            frac = used / cap if cap else 1.0
            color = "#d62728" if frac > 0.99 else ("#ff9900" if frac > 0.6 else "#8abf8a")
            width = 1 + 4 * min(frac, 1.0)
            parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{color}" stroke-width="{width:.1f}" opacity="0.7"/>'
            )

    # Macros.
    for mid, pm in solution.placements.items():
        fill = _KIND_FILL.get(pm.cell.kind, "#e0e0e0")
        parts.append(
            f'<rect x="{pm.x * s}" y="{pm.y * s}" width="{pm.cell.width * s}" '
            f'height="{pm.cell.height * s}" fill="{fill}" stroke="#333" opacity="0.9"/>'
        )
        parts.append(
            f'<text x="{(pm.x + 0.3) * s}" y="{(pm.y + 1) * s}" '
            f'font-size="{s * 0.8:.0f}">{_esc(mid)}</text>'
        )
        for p in pm.cell.ports:
            px, py = pm.port_tile(p)
            color = "#1f77b4" if p.direction == "input" else "#d62728"
            parts.append(
                f'<circle cx="{(px + 0.5) * s}" cy="{(py + 0.5) * s}" r="{s * 0.3:.0f}" '
                f'fill="{color}"><title>{_esc(f"{mid}.{p.id}")}</title></circle>'
            )

    # Nets: detailed routes when given, straight lines otherwise.
    for net in problem.nets:
        path = (routes or {}).get(net.id)
        if path:
            pts = " ".join(f"{(x + 0.5) * s},{(y + 0.5) * s}" for x, y in path)
            parts.append(
                f'<polyline points="{pts}" fill="none" stroke="#6a3d9a" '
                f'stroke-width="2" opacity="0.8"><title>{_esc(net.id)}</title></polyline>'
            )
        else:
            sx, sy = solution.port_tile(net.source_macro, net.source_port)
            tx, ty = solution.port_tile(net.sink_macro, net.sink_port)
            parts.append(
                f'<line x1="{(sx + 0.5) * s}" y1="{(sy + 0.5) * s}" '
                f'x2="{(tx + 0.5) * s}" y2="{(ty + 0.5) * s}" stroke="#6a3d9a" '
                f'stroke-width="1" stroke-dasharray="4 3" opacity="0.6">'
                f"<title>{_esc(net.id)}</title></line>"
            )

    parts.append("</svg>")
    return "\n".join(parts)
