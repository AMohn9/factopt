"""M5: Benders cut loop."""

import pytest

from factopt.data import vanilla
from factopt.loop import optimize_loop
from factopt.macros import build_problem
from factopt.macros.cell import MacroCell, PlacedMacro, PortCandidate
from factopt.macros.library import FlowNet, MacroProblem
from factopt.master import solve_master
from factopt.master.cuts import nogood_cut
from factopt.master.model import MasterSolution
from factopt.model.blueprint import EAST
from factopt.ratios import solve_ratios
from factopt.routing.explain import explain_failures
from factopt.routing.multinet import route_nets

DB = vanilla.DB


def _stub(mid, kind, w, h, ports):
    return MacroCell(id=mid, kind=kind, width=w, height=h, entities=(), ports=tuple(ports))


def _out_port(item, y=0):
    return PortCandidate(
        id=f"{item}-out", item=item, direction="output", side="east",
        local_position=(1, y), flow_entry_dir=EAST, max_rate_per_sec=15.0,
    )


def _in_port(item, y=0):
    return PortCandidate(
        id=f"{item}-in", item=item, direction="input", side="west",
        local_position=(0, y), flow_entry_dir=EAST, max_rate_per_sec=15.0,
    )


def test_nogood_cut_forbids_placement():
    plan = solve_ratios("electronic-circuit", 2.0, DB)
    prob = build_problem(plan, DB)
    first = solve_master(prob, time_limit_s=10.0)
    assert first.ok
    positions = {mid: (pm.x, pm.y) for mid, pm in first.placements.items()}
    cut = nogood_cut(positions, "test: forbid the first placement")
    second = solve_master(prob, cuts=[cut], time_limit_s=10.0)
    assert second.ok
    moved = any(
        (second.placements[mid].x, second.placements[mid].y) != positions[mid]
        for mid in positions
    )
    assert moved, "no-good cut did not change the placement"


def test_no_path_failure_explained_with_blockers():
    src = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    dst = _stub("b", "t", 2, 1, [_in_port("iron-plate")])
    wall = _stub("wall", "t", 9, 20, [])
    prob = MacroProblem(plan=None, macros={"a": src, "b": dst, "wall": wall})
    prob.nets.append(FlowNet("n1", "iron-plate", "a", "iron-plate-out", "b", "iron-plate-in", 1.0))
    sol = MasterSolution(
        status="FEASIBLE",
        placements={
            "a": PlacedMacro(src, 0, 10),
            "b": PlacedMacro(dst, 18, 10),
            "wall": PlacedMacro(wall, 5, 0),
        },
        width=22,
        height=20,
    )
    res = route_nets(prob, sol, DB)
    assert not res.feasible and res.failures[0].kind == "no_path"
    cuts = explain_failures(prob, sol, res, DB)
    assert cuts and cuts[0].kind == "corridor"
    assert "wall" in cuts[0].affected_macros
    assert "a" in cuts[0].affected_macros and "b" in cuts[0].affected_macros


def test_port_conflict_becomes_pin_access_cut():
    # a's east output access tile and c's west input access tile coincide:
    # a at x=0..1 (access x=2), c at x=3 (access x=2), same row.
    a = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    b = _stub("b", "t", 2, 1, [_in_port("iron-plate")])
    c = _stub("c", "t", 2, 1, [_in_port("copper-plate")])
    d = _stub("d", "t", 2, 1, [_out_port("copper-plate")])
    prob = MacroProblem(plan=None, macros={"a": a, "b": b, "c": c, "d": d})
    prob.nets.append(FlowNet("n1", "iron-plate", "a", "iron-plate-out", "b", "iron-plate-in", 1.0))
    prob.nets.append(FlowNet("n2", "copper-plate", "d", "copper-plate-out", "c", "copper-plate-in", 1.0))
    sol = MasterSolution(
        status="FEASIBLE",
        placements={
            "a": PlacedMacro(a, 0, 5),
            "b": PlacedMacro(b, 10, 5),
            "c": PlacedMacro(c, 3, 5),
            "d": PlacedMacro(d, 10, 8),
        },
        width=14,
        height=12,
    )
    res = route_nets(prob, sol, DB)
    conflicts = [f for f in res.failures if f.kind == "port_conflict"]
    assert conflicts, [str(f) for f in res.failures]
    cuts = explain_failures(prob, sol, res, DB)
    pin = [c_ for c_ in cuts if c_.kind == "pin_access"]
    assert pin
    ports = {tuple(p) for p in pin[0].payload["ports"]}
    assert ("a", "iron-plate-out") in ports and ("c", "copper-plate-in") in ports


def test_pin_access_cut_separates_access_tiles():
    a = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    c = _stub("c", "t", 2, 1, [_in_port("copper-plate")])
    prob = MacroProblem(plan=None, macros={"a": a, "c": c})
    from factopt.master.cuts import pin_access_cut

    cut = pin_access_cut(("a", "iron-plate-out"), ("c", "copper-plate-in"), (2, 5), "test")
    sol = solve_master(prob, cuts=[cut], time_limit_s=10.0)
    assert sol.ok
    ta = sol.port_access_tile("a", "iron-plate-out")
    tc = sol.port_access_tile("c", "copper-plate-in")
    assert ta != tc


# ---------------------------------------------------------------------------
# Integration: the loop converges for green science
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gs_loop():
    return optimize_loop(
        "logistic-science-pack", 1.0, DB,
        max_iterations=8, master_time_limit_s=15.0, time_budget_s=300.0,
    )


def test_loop_reaches_feasible(gs_loop):
    assert gs_loop.feasible, gs_loop.summary()
    best = gs_loop.best
    assert not best.validation.by_kind("overlap"), str(best.validation)
    assert not best.validation.by_kind("flow"), str(best.validation)
    assert best.blueprint_string.startswith("0")


def test_loop_never_repeats_a_cut_placement(gs_loop):
    """Every no-good/corridor cut must actually forbid its placement in all
    later iterations (the master honors cuts)."""
    for i, it in enumerate(gs_loop.iterations):
        for cut in it.new_cuts:
            if cut.kind not in ("nogood", "corridor"):
                continue
            forbidden = cut.payload["positions"]
            for later in gs_loop.iterations[i + 1:]:
                if not later.master.ok:
                    continue
                same = all(
                    (later.master.placements[mid].x, later.master.placements[mid].y)
                    == tuple(p)
                    for mid, p in forbidden.items()
                )
                assert not same, f"iteration {later.index} repeats cut placement: {cut.explanation}"
