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
