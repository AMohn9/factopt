"""Debug visualization and candidate reporting.

:func:`render_svg` draws a master solution: macro rectangles with their ports,
straight net lines, and (when present) the coarse grid with per-arc
utilization plus detailed routes. :func:`candidate_report` renders a
markdown post-mortem of a Benders loop run, and :func:`write_candidate`
drops blueprint + report + SVG artifacts into a directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from factopt.macros.library import MacroProblem
from factopt.master.model import MasterSolution

if TYPE_CHECKING:
    from factopt.loop import LoopResult

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

    # Nets: detailed tree branches when given, straight source->sink lines
    # otherwise.
    for net in problem.nets:
        branches = (routes or {}).get(net.id)
        if branches:
            for bi, path in enumerate(branches):
                if not path:
                    continue
                pts = " ".join(f"{(x + 0.5) * s},{(y + 0.5) * s}" for x, y in path)
                parts.append(
                    f'<polyline points="{pts}" fill="none" stroke="#6a3d9a" '
                    f'stroke-width="2" opacity="0.8">'
                    f"<title>{_esc(f'{net.id}[{bi}]')}</title></polyline>"
                )
        else:
            sx, sy = solution.port_tile(net.source_macro, net.source_port)
            for snk in net.sinks:
                tx, ty = solution.port_tile(snk.macro, snk.port)
                parts.append(
                    f'<line x1="{(sx + 0.5) * s}" y1="{(sy + 0.5) * s}" '
                    f'x2="{(tx + 0.5) * s}" y2="{(ty + 0.5) * s}" stroke="#6a3d9a" '
                    f'stroke-width="1" stroke-dasharray="4 3" opacity="0.6">'
                    f"<title>{_esc(net.id)}</title></line>"
                )

    parts.append("</svg>")
    return "\n".join(parts)


def candidate_report(result: "LoopResult") -> str:
    """Markdown report: rate plan, placement, coarse utilization, routing
    metrics, cuts used, and static validation."""
    lines: list[str] = []
    best = result.best
    plan = result.problem.plan
    title = f"{plan.rate:g}/s {plan.target}" if plan is not None else "candidate"
    lines.append(f"# Benders candidate: {title}")
    lines.append("")
    lines.append(f"**Feasible:** {result.feasible}")
    if result.max_iterations:
        lines.append(
            f"**Budget:** {result.time_budget_s:g}s total, "
            f"{result.master_time_limit_s:g}s per master solve, "
            f"{result.max_iterations} iterations max"
        )
        lines.append(
            f"**Used:** {result.elapsed_s:.0f}s over {len(result.iterations)} iteration(s)"
        )
    if best is not None:
        m = best.routing.metrics
        lines.append(
            f"**Bounding box:** {best.width} x {best.height} = {best.area} tiles"
        )
        lines.append(
            f"**Routing:** {m.total_belt_length} belt tiles, "
            f"{m.total_undergrounds} undergrounds, {m.total_splitters} splitters, "
            f"{m.total_turns} turns, converged in {m.rounds} round(s)"
        )
        lines.append(f"**Static validation:** {'ok' if best.validation.ok else 'VIOLATIONS'}")
    lines.append("")

    if plan is not None:
        lines.append("## Rate plan")
        lines.append("")
        lines.append("```")
        lines.append(str(plan))
        lines.append("```")
        lines.append("")

    if best is not None:
        lines.append("## Placement")
        lines.append("")
        lines.append("| macro | position | size |")
        lines.append("|---|---|---|")
        for mid, pm in sorted(best.master.placements.items()):
            lines.append(
                f"| {mid} | ({pm.x}, {pm.y}) | {pm.cell.width} x {pm.cell.height} |"
            )
        lines.append("")
        if best.master.coarse is not None:
            c = best.master.coarse
            lines.append("## Coarse routing")
            lines.append("")
            lines.append(
                f"{c.cols} x {c.rows} cells of {c.cell} tiles; "
                f"max boundary utilization {c.max_utilization:.2f}"
            )
            lines.append("")
        if not best.validation.ok:
            lines.append("## Validation violations")
            lines.append("")
            lines.append("```")
            lines.append(str(best.validation))
            lines.append("```")
            lines.append("")

    lines.append("## Iterations")
    lines.append("")
    lines.append("```")
    lines.append(result.summary())
    lines.append("```")
    return "\n".join(lines) + "\n"


def write_candidate(result: "LoopResult", directory: str | Path, name: str) -> dict[str, Path]:
    """Write blueprint string, markdown report, and debug SVG for a loop run.

    Returns the paths written, keyed by kind.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}

    report_path = directory / f"{name}.report.md"
    report_path.write_text(candidate_report(result))
    out["report"] = report_path

    if result.best is not None:
        bp_path = directory / f"{name}.blueprint.txt"
        bp_path.write_text(result.best.blueprint_string)
        out["blueprint"] = bp_path
        svg_path = directory / f"{name}.debug.svg"
        svg_path.write_text(
            render_svg(result.problem, result.best.master, routes=result.best.routing.paths)
        )
        out["svg"] = svg_path
    return out
