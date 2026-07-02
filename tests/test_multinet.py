"""M4: multi-net detailed router."""

import pytest

from factopt.data import vanilla
from factopt.macros import build_problem
from factopt.macros.cell import MacroCell, PlacedMacro, PortCandidate
from factopt.macros.library import FlowNet, FlowSink, MacroProblem
from factopt.master import solve_master
from factopt.master.model import MasterSolution
from factopt.model.blueprint import EAST
from factopt.ratios import solve_ratios
from factopt.routing.multinet import route_nets

DB = vanilla.DB


def _stub(mid: str, kind: str, w: int, h: int, ports) -> MacroCell:
    return MacroCell(id=mid, kind=kind, width=w, height=h, entities=(), ports=tuple(ports))


def _net(nid: str, item: str, src: str, sinks: list[tuple[str, float]]) -> FlowNet:
    """Point-to-point or multi-sink net with conventional port ids."""
    fs = tuple(FlowSink(macro=m, port=f"{item}-in", rate_per_sec=r) for m, r in sinks)
    return FlowNet(
        id=nid,
        item=item,
        source_macro=src,
        source_port=f"{item}-out",
        sinks=fs,
        rate_per_sec=sum(r for _, r in sinks),
    )


def _tiles(paths: list[list[tuple[int, int]]]) -> set[tuple[int, int]]:
    return {t for p in paths for t in p}


def _out_port(item: str, y: int = 0, pid: str | None = None) -> PortCandidate:
    return PortCandidate(
        id=pid or f"{item}-out",
        item=item,
        direction="output",
        side="east",
        local_position=(1, y),
        flow_entry_dir=EAST,
        max_rate_per_sec=15.0,
    )


def _in_port(item: str, y: int = 0, pid: str | None = None) -> PortCandidate:
    return PortCandidate(
        id=pid or f"{item}-in",
        item=item,
        direction="input",
        side="west",
        local_position=(0, y),
        flow_entry_dir=EAST,
        max_rate_per_sec=15.0,
    )


def _solution(placements: dict[str, PlacedMacro], w: int, h: int) -> MasterSolution:
    return MasterSolution(status="FEASIBLE", placements=placements, width=w, height=h)


def test_single_net_routes():
    src = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    dst = _stub("b", "t", 2, 1, [_in_port("iron-plate")])
    prob = MacroProblem(plan=None, macros={"a": src, "b": dst})
    prob.nets.append(_net("n1", "iron-plate", "a", [("b", 1.0)]))
    sol = _solution({"a": PlacedMacro(src, 0, 2), "b": PlacedMacro(dst, 10, 2)}, 14, 6)
    res = route_nets(prob, sol, DB)
    assert res.feasible, [str(f) for f in res.failures]
    assert res.paths["n1"][0][0] == (2, 2)  # trunk starts at the source mouth


def test_crossing_nets_negotiate():
    """Two perpendicular nets must both route (undergrounds allow crossing)."""
    a = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    b = _stub("b", "t", 2, 1, [_in_port("iron-plate")])
    c = _stub("c", "t", 2, 1, [_out_port("copper-plate")])
    d = _stub("d", "t", 2, 1, [_in_port("copper-plate")])
    prob = MacroProblem(plan=None, macros={"a": a, "b": b, "c": c, "d": d})
    prob.nets.append(_net("n1", "iron-plate", "a", [("b", 1.0)]))
    prob.nets.append(_net("n2", "copper-plate", "c", [("d", 1.0)]))
    # n1 west->east through the middle; n2 north row -> south row, crossing n1.
    sol = _solution(
        {
            "a": PlacedMacro(a, 0, 6),
            "b": PlacedMacro(b, 12, 6),
            "c": PlacedMacro(c, 6, 0),
            "d": PlacedMacro(d, 6, 12),
        },
        16,
        14,
    )
    res = route_nets(prob, sol, DB)
    assert res.feasible, [str(f) for f in res.failures]
    tiles1 = _tiles(res.paths["n1"])
    tiles2 = _tiles(res.paths["n2"])
    assert not (tiles1 & tiles2), "converged routes must not share tiles"


def test_walled_off_net_reports_no_path():
    src = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    dst = _stub("b", "t", 2, 1, [_in_port("iron-plate")])
    wall = _stub("wall", "t", 2, 20, [])
    prob = MacroProblem(plan=None, macros={"a": src, "b": dst, "wall": wall})
    prob.nets.append(_net("n1", "iron-plate", "a", [("b", 1.0)]))
    # Wall spans the full height between a and b; yellow undergrounds span at
    # most 4 blocked tiles but the wall plus reserved margins make it 2 wide
    # only -- so make the wall wider than max underground reach (>= 8 tiles).
    wide_wall = _stub("wall", "t", 9, 20, [])
    prob.macros["wall"] = wide_wall
    sol = _solution(
        {
            "a": PlacedMacro(src, 0, 10),
            "b": PlacedMacro(dst, 18, 10),
            "wall": PlacedMacro(wide_wall, 5, 0),
        },
        22,
        20,
    )
    res = route_nets(prob, sol, DB)
    assert not res.feasible
    assert res.failures and res.failures[0].kind == "no_path"
    assert res.failures[0].net_id == "n1"


def test_underground_crosses_narrow_wall():
    src = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    dst = _stub("b", "t", 2, 1, [_in_port("iron-plate")])
    wall = _stub("wall", "t", 3, 20, [])
    prob = MacroProblem(plan=None, macros={"a": src, "b": dst, "wall": wall})
    prob.nets.append(_net("n1", "iron-plate", "a", [("b", 1.0)]))
    sol = _solution(
        {
            "a": PlacedMacro(src, 0, 10),
            "b": PlacedMacro(dst, 14, 10),
            "wall": PlacedMacro(wall, 6, 0),
        },
        18,
        20,
    )
    res = route_nets(prob, sol, DB)
    assert res.feasible, [str(f) for f in res.failures]
    assert res.metrics.total_undergrounds >= 1


# ---------------------------------------------------------------------------
# Multi-sink Steiner trees
# ---------------------------------------------------------------------------


def test_multi_sink_net_routes_as_tree():
    """One net with four sinks becomes one belt tree: a single trunk leaves
    the source and splitters branch it toward every sink."""
    src = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    consumers = {
        mid: _stub(mid, "t", 2, 1, [_in_port("iron-plate")])
        for mid in ("b", "c", "d", "e")
    }
    prob = MacroProblem(plan=None, macros={"a": src, **consumers})
    prob.nets.append(
        _net("n1", "iron-plate", "a", [("b", 2.0), ("c", 1.0), ("d", 1.0), ("e", 0.5)])
    )
    sol = _solution(
        {
            "a": PlacedMacro(src, 0, 10),
            "b": PlacedMacro(consumers["b"], 24, 10),
            "c": PlacedMacro(consumers["c"], 12, 2),
            "d": PlacedMacro(consumers["d"], 12, 18),
            "e": PlacedMacro(consumers["e"], 20, 4),
        },
        28,
        24,
    )
    res = route_nets(prob, sol, DB)
    assert res.feasible, [str(f) for f in res.failures]
    # Four branches (one per sink), three splitter junctions.
    assert len(res.paths["n1"]) == 4
    assert res.metrics.total_splitters == 3
    # Every sink mouth is fed by the tree.
    from factopt.validate import validate

    # Stub macros have no internal entities, so check the routed belts
    # between the port *access* tiles (mouths) instead of the lane tiles.
    flows = [
        (
            sol.port_access_tile("a", "iron-plate-out"),
            sol.port_access_tile(m, "iron-plate-in"),
        )
        for m in ("b", "c", "d", "e")
    ]
    entities = list(res.entities)
    for pm in sol.placements.values():
        entities.extend(pm.entities())
    report = validate(entities, DB, bounds=(0, 0, sol.width, sol.height), flows=flows)
    assert not report.by_kind("overlap"), str(report)
    assert not report.by_kind("flow"), str(report)


def test_multi_sink_walled_sink_reports_failing_sink():
    """When one sink of a tree is unreachable, the failure names that sink."""
    src = _stub("a", "t", 2, 1, [_out_port("iron-plate")])
    near = _stub("b", "t", 2, 1, [_in_port("iron-plate")])
    far = _stub("c", "t", 2, 1, [_in_port("iron-plate")])
    wall = _stub("wall", "t", 9, 30, [])
    prob = MacroProblem(plan=None, macros={"a": src, "b": near, "c": far, "wall": wall})
    prob.nets.append(_net("n1", "iron-plate", "a", [("b", 1.0), ("c", 1.0)]))
    sol = _solution(
        {
            "a": PlacedMacro(src, 0, 10),
            "b": PlacedMacro(near, 6, 10),
            "c": PlacedMacro(far, 24, 10),
            "wall": PlacedMacro(wall, 12, 0),
        },
        30,
        30,
    )
    res = route_nets(prob, sol, DB)
    assert not res.feasible
    assert res.failures[0].kind == "no_path"
    assert res.failures[0].net_id == "n1"
    assert res.failures[0].sink_macro == "c"


# ---------------------------------------------------------------------------
# Green science end-to-end routing
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gs_routed():
    """A deterministic hand-friendly placement: bands in adjacency order on
    one row, inputs on the west edge, output on the east. (Master-driven
    placements go through the M5 cut loop, which repairs unroutable ones.)"""
    from factopt.placement.ordering import order_recipes

    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    prob = build_problem(plan, DB)
    order = order_recipes(plan, DB)

    placements = {}
    x, band_y = 12, 16
    for r in order:
        m = prob.macros[r]
        placements[r] = PlacedMacro(m, x, band_y)
        x += m.width + 8
    inputs = sorted(
        (m for m in prob.macros.values() if m.kind == "input-connector"), key=lambda m: m.id
    )
    for i, m in enumerate(inputs):
        placements[m.id] = PlacedMacro(m, 0, 4 + 6 * i)
    out = prob.macros["out"]
    placements["out"] = PlacedMacro(out, x, band_y + 4)
    sol = _solution(placements, x + out.width, 44)
    res = route_nets(prob, sol, DB)
    return prob, sol, res


def test_green_science_routes(gs_routed):
    prob, sol, res = gs_routed
    assert res.feasible, [str(f) for f in res.failures]
    assert set(res.paths) == {n.id for n in prob.nets}


def test_green_science_routes_validate(gs_routed):
    from factopt.validate import validate

    prob, sol, res = gs_routed
    if not res.feasible:
        pytest.skip("routing infeasible; covered by test_green_science_routes")
    entities = list(res.entities)
    for pm in sol.placements.values():
        entities.extend(pm.entities())
    flows = []
    for net in prob.nets:
        for s in net.sinks:
            flows.append(
                (
                    sol.port_tile(net.source_macro, net.source_port),
                    sol.port_tile(s.macro, s.port),
                )
            )
    report = validate(entities, DB, bounds=(0, 0, sol.width, sol.height), flows=flows)
    assert not report.by_kind("overlap"), str(report)
    assert not report.by_kind("bounds"), str(report)
    assert not report.by_kind("flow"), str(report)
