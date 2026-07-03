"""Solver-backend parity: the SCIP backend must reproduce the CP-SAT model.

The SCIP backend linearizes CP-SAT's global constraints (no-overlap, min/max,
division, reified logic, boolean products) and expresses the bilinear area
objective as a native nonconvex constraint. These tests lock in that the
primitives are correct and that both engines agree on placement.

Note: the embedded coarse-routing MILP (``coarse_cell``) is deliberately not
exercised under SCIP here -- its big-M reformulation is intractable for SCIP
within a test budget (see the benchmark notes), which is itself a finding.
"""

import pytest

from factopt.data import vanilla
from factopt.macros import build_problem
from factopt.macros.cell import MacroCell, PortCandidate
from factopt.macros.library import FlowNet, FlowSink, MacroProblem
from factopt.master import solve_master
from factopt.master.backend import make_model
from factopt.model.blueprint import EAST, WEST
from factopt.ratios import solve_ratios

DB = vanilla.DB


def test_make_model_factory():
    from factopt.master.backend.cpsat import CpSatModel
    from factopt.master.backend.scip import ScipModel

    assert isinstance(make_model("cpsat"), CpSatModel)
    assert isinstance(make_model("scip"), ScipModel)
    with pytest.raises(ValueError):
        make_model("gurobi")


def test_scip_bilinear_two_stage():
    """Bilinear area objective + a second lexicographic solve on one model."""
    m = make_model("scip")
    w = m.new_int_var(1, 10, "w")
    h = m.new_int_var(1, 10, "h")
    area = m.new_int_var(1, 100, "area")
    m.add_multiplication_equality(area, [w, h])
    m.add(w + h >= 7)
    m.minimize(area)
    s1 = m.solve(5.0, 1)
    assert s1.status == "OPTIMAL"
    assert s1.value(area) == 6  # 6*1 or 1*6
    m.add(area <= s1.value(area))
    m.minimize(w)
    s2 = m.solve(5.0, 1)
    assert s2.status == "OPTIMAL"
    assert s2.value(w) == 1 and s2.value(h) == 6


def test_scip_reified_and_ne():
    m = make_model("scip")
    x = m.new_int_var(0, 20, "x")
    b = m.new_bool_var("b")
    m.enforce(b, x, ">=", 15)  # b -> x >= 15
    m.add(b == 1)
    ne = m.is_ne(x, 17, "ne17")  # ne <-> x != 17
    m.add_bool_or([ne])  # force x != 17
    m.minimize(x)
    s = m.solve(5.0, 1)
    assert s.status == "OPTIMAL"
    assert s.value(x) == 15


def test_scip_negated_literal():
    m = make_model("scip")
    p = m.new_bool_var("p")
    m.add_bool_or([m.neg(p)])  # (not p) must hold -> p = 0
    m.minimize(p * 0)
    s = m.solve(2.0, 1)
    assert s.value(p) == 0


def test_scip_min_max_division_mapdomain():
    m = make_model("scip")
    a = m.new_int_var(0, 10, "a")
    b = m.new_int_var(0, 10, "b")
    mx = m.new_int_var(0, 10, "mx")
    mn = m.new_int_var(0, 10, "mn")
    q = m.new_int_var(0, 10, "q")
    idx = m.new_int_var(0, 3, "idx")
    ch = [m.new_bool_var(f"c{i}") for i in range(4)]
    m.add(a == 3)
    m.add(b == 8)
    m.add_max_equality(mx, [a, b])
    m.add_min_equality(mn, [a, b])
    m.add_division_equality(q, b, 4)  # 8 // 4 == 2
    m.add_map_domain(idx, ch)
    m.add(idx == 2)
    m.minimize(a)
    s = m.solve(5.0, 1)
    assert s.status == "OPTIMAL"
    assert s.value(mx) == 8
    assert s.value(mn) == 3
    assert s.value(q) == 2
    assert s.value(ch[2]) == 1
    assert all(s.value(ch[i]) == 0 for i in (0, 1, 3))


def test_scip_no_overlap():
    m = make_model("scip")
    x0 = m.new_int_var(0, 5, "x0")
    y0 = m.new_int_var(0, 5, "y0")
    x1 = m.new_int_var(0, 5, "x1")
    y1 = m.new_int_var(0, 5, "y1")
    m.add_no_overlap([(x0, 3, y0, 3), (x1, 3, y1, 3)])
    s = m.solve(5.0, 1)
    assert s.status in ("OPTIMAL", "FEASIBLE")
    ax0, ay0, ax1, ay1 = s.value(x0), s.value(y0), s.value(x1), s.value(y1)
    separated = (
        ax0 + 3 <= ax1 or ax1 + 3 <= ax0 or ay0 + 3 <= ay1 or ay1 + 3 <= ay0
    )
    assert separated


def _tiny_problem() -> MacroProblem:
    """Two 2x1 cells and one net between them -- trivially placeable, so both
    engines can solve stage-1 area to proven optimality in milliseconds."""
    a = MacroCell(
        id="A", kind="test", width=2, height=1, entities=(),
        ports=(PortCandidate("a-out", "X", "output", "east", (1, 0), EAST, 15.0),),
    )
    b = MacroCell(
        id="B", kind="test", width=2, height=1, entities=(),
        ports=(PortCandidate("x-in", "X", "input", "west", (0, 0), WEST, 15.0),),
    )
    net = FlowNet(
        id="X:A-t0", item="X", source_macro="A", source_port="a-out",
        sinks=(FlowSink(macro="B", port="x-in", rate_per_sec=15.0),),
        rate_per_sec=15.0,
    )
    return MacroProblem(plan=None, macros={"A": a, "B": b}, nets=[net])


def _valid_placement(sol) -> None:
    tiles: dict = {}
    for mid, pm in sol.placements.items():
        assert pm.x >= 0 and pm.y >= 0
        assert pm.x2 <= sol.width and pm.y2 <= sol.height, mid
        for t in pm.footprint_tiles():
            assert t not in tiles, f"{mid} overlaps {tiles[t]} at {t}"
            tiles[t] = mid


def test_placement_area_parity_tiny():
    """CP-SAT and SCIP must find the same optimal bounding-box area."""
    prob = _tiny_problem()
    cp = solve_master(prob, coarse_cell=None, max_w=12, max_h=12,
                      time_limit_s=10.0, backend="cpsat")
    sc = solve_master(prob, coarse_cell=None, max_w=12, max_h=12,
                      time_limit_s=10.0, backend="scip")
    assert cp.status == "OPTIMAL" and sc.status == "OPTIMAL"
    assert cp.area == sc.area
    _valid_placement(cp)
    _valid_placement(sc)


@pytest.mark.slow
def test_scip_placement_green_science_valid():
    """On the real green-science problem, SCIP placement (no coarse routing)
    yields a valid, non-overlapping, in-bounds layout."""
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    prob = build_problem(plan, DB)
    sol = solve_master(prob, coarse_cell=None, time_limit_s=30.0, backend="scip")
    assert sol.ok, sol.status
    assert set(sol.placements) == set(prob.macros)
    _valid_placement(sol)
