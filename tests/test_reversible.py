"""Reversible input lanes: a lane machines only pick from can be fed from
either end, so the master picks the cheaper side and the router approaches a
macro from whichever direction is closer."""

import pytest

from factopt.data import vanilla
from factopt.macros import build_problem
from factopt.macros.cell import (
    MacroCell,
    PlacedMacro,
    PortCandidate,
    PortEnd,
    rotated,
)
from factopt.macros.library import FlowNet, FlowSink, MacroProblem
from factopt.master import solve_master
from factopt.master.model import MasterSolution
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST
from factopt.ratios import solve_ratios
from factopt.routing.multinet import route_nets
from factopt.validate import validate

DB = vanilla.DB


@pytest.fixture(scope="module")
def gs_problem():
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    return build_problem(plan, DB)


def _reversible_band(problem: MacroProblem) -> tuple[MacroCell, PortCandidate]:
    """A recipe band with at least one reversible input port + that port."""
    for m in problem.macros.values():
        if m.kind != "recipe-band":
            continue
        rev_ports = [p for p in m.ports if p.reversible]
        if rev_ports:
            return m, rev_ports[0]
    pytest.skip("no reversible-input recipe band in this plan")


def test_band_input_lanes_are_reversible(gs_problem):
    cell, port = _reversible_band(gs_problem)
    # An input port's reverse end sits on the opposite side, at the far edge,
    # with the belt flowing the other way.
    assert port.direction == "input"
    assert port.side == "west" and port.local_position[0] == 0
    rev = port.reverse
    assert rev is not None
    assert rev.side == "east"
    assert rev.local_position == (cell.width - 1, port.local_position[1])
    assert port.flow_entry_dir == EAST and rev.flow_entry_dir == WEST
    # Its lane is registered for belt flipping and spans the full width.
    lane = cell.reversible_lanes[port.id]
    assert len(lane.tiles) == cell.width
    assert lane.forward_dir == EAST and lane.reverse_dir == WEST


def test_reverse_end_is_boundary_and_choice_moves_the_port(gs_problem):
    cell, port = _reversible_band(gs_problem)
    fwd = PlacedMacro(cell, x=5, y=7)
    rev = PlacedMacro(cell, x=5, y=7, port_choice={port.id: True})
    # Both realizations sit inside the footprint; access tiles fall outside on
    # opposite sides.
    assert fwd.port_tile(port) in fwd.footprint_tiles()
    assert rev.port_tile(port) in rev.footprint_tiles()
    fx = fwd.port_access_tile(port)
    rx = rev.port_access_tile(port)
    assert fx not in fwd.footprint_tiles() and rx not in rev.footprint_tiles()
    assert fx[0] < fwd.x  # west of the cell
    assert rx[0] >= rev.x + cell.width  # east of the cell
    assert fwd.port_flow_dir(port) == EAST and rev.port_flow_dir(port) == WEST


def test_reversed_lane_flips_only_its_belts_and_validates(gs_problem):
    cell, port = _reversible_band(gs_problem)
    row = port.local_position[1]
    placed = PlacedMacro(cell, x=0, y=0, port_choice={port.id: True})
    ents = placed.entities()
    # No entity count/overlap regression from flipping.
    assert len(ents) == len(cell.entities)
    assert not validate(ents, DB).by_kind("overlap")
    # Every belt on the reversed lane row now faces WEST; belts elsewhere are
    # untouched (still EAST).
    lane_tiles = {t for t in cell.reversible_lanes[port.id].tiles}
    for e in ents:
        if e.name not in DB.belts:
            continue
        local = (int(e.position.x - 0.5), int(e.position.y - 0.5))
        if local in lane_tiles:
            assert e.direction == WEST, f"lane belt at {local} not flipped"


def test_default_choice_leaves_lanes_forward(gs_problem):
    cell, port = _reversible_band(gs_problem)
    placed = PlacedMacro(cell, x=0, y=0)  # no port_choice -> all forward
    lane_tiles = {t for t in cell.reversible_lanes[port.id].tiles}
    for e in placed.entities():
        if e.name not in DB.belts:
            continue
        local = (int(e.position.x - 0.5), int(e.position.y - 0.5))
        if local in lane_tiles:
            assert e.direction == EAST


def test_rotation_carries_reversibility(gs_problem):
    cell, port = _reversible_band(gs_problem)
    r = rotated(cell, 1)  # 90 deg clockwise
    rp = r.port(port.id)
    assert rp.reversible
    # West -> north, east -> south under one clockwise turn; flows advance +4.
    assert rp.side == "north" and rp.reverse.side == "south"
    assert rp.flow_entry_dir == (EAST + 4) % 16
    assert rp.reverse.flow_entry_dir == (WEST + 4) % 16
    lane = r.reversible_lanes[port.id]
    assert lane.forward_dir == (EAST + 4) % 16
    assert lane.reverse_dir == (WEST + 4) % 16
    # The rotated lane still spans the (now vertical) full extent.
    assert len(lane.tiles) == cell.width


# ---------------------------------------------------------------------------
# Router + master honor the reverse end
# ---------------------------------------------------------------------------


def _stub(mid, w, h, ports, lanes=None) -> MacroCell:
    return MacroCell(
        id=mid, kind="t", width=w, height=h, entities=(), ports=tuple(ports),
        reversible_lanes=lanes or {},
    )


def test_router_feeds_reversed_sink_from_the_east():
    src = _stub("a", 2, 1, [PortCandidate("iron-plate-out", "iron-plate", "output",
                                          "east", (1, 0), EAST, 15.0)])
    dst = _stub("b", 2, 1, [PortCandidate(
        "iron-plate-in", "iron-plate", "input", "west", (0, 0), EAST, 15.0,
        reverse=PortEnd("east", (1, 0), WEST),
    )])
    prob = MacroProblem(plan=None, macros={"a": src, "b": dst})
    prob.nets.append(FlowNet("n1", "iron-plate", "a", "iron-plate-out",
                             (FlowSink("b", "iron-plate-in", 1.0),), 1.0))
    sol = MasterSolution(
        status="FEASIBLE", width=16, height=6,
        placements={
            "a": PlacedMacro(src, 0, 2),
            "b": PlacedMacro(dst, 10, 2, port_choice={"iron-plate-in": True}),
        },
    )
    res = route_nets(prob, sol, DB)
    assert res.feasible, [str(f) for f in res.failures]
    # The reversed sink is approached from its east mouth.
    east_mouth = sol.port_access_tile("b", "iron-plate-in")
    assert east_mouth == (12, 2)
    assert east_mouth in {t for p in res.paths["n1"] for t in p}


def test_master_picks_reverse_end_when_source_is_east():
    """Source pinned east, sink pinned west: feeding the sink's lane from its
    (interior) east end shortens the route, so the master reverses it."""
    src = _stub("src", 2, 1, [PortCandidate("iron-plate-out", "iron-plate",
                                            "output", "east", (1, 0), EAST, 15.0)])
    sink = _stub("sink", 4, 1, [PortCandidate(
        "iron-plate-in", "iron-plate", "input", "west", (0, 0), EAST, 15.0,
        reverse=PortEnd("east", (3, 0), WEST),
    )])
    prob = MacroProblem(plan=None, macros={"src": src, "sink": sink})
    prob.pins = {"src": "east", "sink": "west"}
    prob.nets.append(FlowNet("n1", "iron-plate", "src", "iron-plate-out",
                             (FlowSink("sink", "iron-plate-in", 1.0),), 1.0))
    sol = solve_master(prob, margin=1, max_w=20, max_h=8, time_limit_s=10.0)
    assert sol.ok
    assert sol.placements["sink"].port_choice["iron-plate-in"] is True
