"""M2/M3: master placement (+ coarse routing)."""

import pytest

from factopt.data import vanilla
from factopt.macros import build_problem
from factopt.master import solve_master
from factopt.master.model import flow_distance
from factopt.ratios import solve_ratios

DB = vanilla.DB


@pytest.fixture(scope="module")
def gs_problem():
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    return build_problem(plan, DB)


@pytest.fixture(scope="module")
def gs_solution(gs_problem):
    sol = solve_master(gs_problem, time_limit_s=20.0)
    assert sol.ok, sol.status
    return sol


def _no_overlap(sol, margin=1):
    tiles = {}
    for mid, pm in sol.placements.items():
        for t in pm.footprint_tiles():
            assert t not in tiles, f"{mid} overlaps {tiles[t]} at {t}"
            tiles[t] = mid


def test_places_all_macros_without_overlap(gs_solution, gs_problem):
    assert set(gs_solution.placements) == set(gs_problem.macros)
    _no_overlap(gs_solution)


def test_placements_inside_bbox(gs_solution):
    for mid, pm in gs_solution.placements.items():
        assert pm.x >= 0 and pm.y >= 0
        assert pm.x2 <= gs_solution.width, mid
        assert pm.y2 <= gs_solution.height, mid


def test_edge_pins_respected(gs_solution, gs_problem):
    for mid, side in gs_problem.pins.items():
        pm = gs_solution.placements[mid]
        if side == "west":
            assert pm.x == 0, mid
        elif side == "east":
            assert pm.x2 == gs_solution.width, mid


def test_area_slack_trades_area_for_flow_distance(gs_problem):
    tight = solve_master(gs_problem, area_slack=0.0, time_limit_s=15.0)
    loose = solve_master(gs_problem, area_slack=0.30, time_limit_s=15.0)
    assert tight.ok and loose.ok
    assert loose.area <= int(tight.area * 1.30) + 1
    # The relaxed solve may use its extra area to shorten flows; both must
    # report a consistent metric.
    assert tight.flow_distance == flow_distance(gs_problem, tight.placements)
    assert loose.flow_distance <= tight.flow_distance


def test_svg_renders(gs_problem, gs_solution, tmp_path):
    from factopt.report import render_svg

    svg = render_svg(gs_problem, gs_solution)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    for mid in gs_problem.macros:
        assert mid in svg
    (tmp_path / "master.svg").write_text(svg)


# ---------------------------------------------------------------------------
# M3: coarse routing
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gs_coarse(gs_problem):
    sol = solve_master(gs_problem, coarse_cell=4, time_limit_s=60.0)
    assert sol.ok, sol.status
    assert sol.coarse is not None
    return sol


def _cell_of(tile, cell):
    return (tile[0] // cell, tile[1] // cell)


def test_coarse_routes_connect_ports(gs_coarse, gs_problem):
    """Every sink cell of a net is reachable from its source cell over the
    net's used coarse arcs (the coarse route is a connected Steiner tree)."""
    c = gs_coarse.coarse
    for net in gs_problem.nets:
        src = _cell_of(gs_coarse.port_tile(net.source_macro, net.source_port), c.cell)
        arcs = c.routes.get(net.id, [])
        succ = {}
        for a, b in arcs:
            succ.setdefault(a, []).append(b)
        seen = {src}
        stack = [src]
        while stack:
            cur = stack.pop()
            for nxt in succ.get(cur, []):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        for s in net.sinks:
            snk = _cell_of(gs_coarse.port_tile(s.macro, s.port), c.cell)
            assert snk in seen, f"{net.id}: sink cell {snk} unreachable from {src}"


def test_coarse_capacity_respected(gs_coarse):
    for e, (used, cap) in gs_coarse.coarse.utilization.items():
        assert used <= cap, f"edge {e}: used {used} > cap {cap}"


def test_coarse_avoids_walls(gs_problem):
    """Flows must not cross boundaries fully spanned by a macro: verify used
    capacity is zero wherever a placed macro spans the boundary completely."""
    sol = solve_master(gs_problem, coarse_cell=4, time_limit_s=60.0)
    assert sol.ok
    c = sol.coarse
    for (c1, c2), (used, cap) in c.utilization.items():
        if cap == 0:
            assert used == 0


def test_coarse_svg_renders(gs_problem, gs_coarse, tmp_path):
    from factopt.report import render_svg

    svg = render_svg(gs_problem, gs_coarse)
    assert "<line" in svg
    (tmp_path / "coarse.svg").write_text(svg)
