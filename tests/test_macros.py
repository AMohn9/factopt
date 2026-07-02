"""M1: macro layer + static validator."""

import pytest

from factopt.data import vanilla
from factopt.macros import build_problem
from factopt.macros.cell import PlacedMacro
from factopt.model.blueprint import EAST, Entity, Position
from factopt.ratios import solve_ratios
from factopt.validate import entity_tiles, validate

DB = vanilla.DB


@pytest.fixture(scope="module")
def gs_problem():
    plan = solve_ratios("logistic-science-pack", 1.0, DB)
    return build_problem(plan, DB)


def test_problem_has_macro_per_recipe_plus_io(gs_problem):
    recipe_macros = {m.id for m in gs_problem.macros.values() if m.kind == "recipe-band"}
    assert recipe_macros == {ln.recipe for ln in gs_problem.plan.lines}
    kinds = {m.kind for m in gs_problem.macros.values()}
    assert "input-connector" in kinds
    assert "output-collector" in kinds


def test_every_net_endpoint_is_a_real_port(gs_problem):
    for net in gs_problem.nets:
        src = gs_problem.macros[net.source_macro]
        dst = gs_problem.macros[net.sink_macro]
        assert src.port(net.source_port).direction == "output"
        assert dst.port(net.sink_port).direction == "input"
        assert src.port(net.source_port).item == net.item
        assert dst.port(net.sink_port).item == net.item


def test_each_output_port_serves_one_net(gs_problem):
    used = [(n.source_macro, n.source_port) for n in gs_problem.nets]
    assert len(used) == len(set(used)), "an output port is shared by two nets"


def test_macro_entities_fit_footprint(gs_problem):
    for macro in gs_problem.macros.values():
        for e in macro.entities:
            for (tx, ty) in entity_tiles(e, DB):
                assert 0 <= tx < macro.width, f"{macro.id}: {e.name} x={tx} w={macro.width}"
                assert 0 <= ty < macro.height, f"{macro.id}: {e.name} y={ty} h={macro.height}"


def test_ports_are_inside_footprint_on_their_side(gs_problem):
    for macro in gs_problem.macros.values():
        for p in macro.ports:
            px, py = p.local_position
            assert 0 <= px < macro.width and 0 <= py < macro.height
            if p.side == "west":
                assert px == 0
            elif p.side == "east":
                assert px == macro.width - 1


def test_placed_macro_translates_entities(gs_problem):
    macro = next(m for m in gs_problem.macros.values() if m.kind == "recipe-band")
    placed = PlacedMacro(cell=macro, x=17, y=23)
    ents = placed.entities()
    assert len(ents) == len(macro.entities)
    for local, moved in zip(macro.entities, ents):
        assert moved.position.x == local.position.x + 17
        assert moved.position.y == local.position.y + 23
    # Footprint covers every entity tile.
    fp = placed.footprint_tiles()
    for e in ents:
        assert set(entity_tiles(e, DB)) <= fp


def test_port_access_tile_is_outside_footprint(gs_problem):
    for macro in gs_problem.macros.values():
        placed = PlacedMacro(cell=macro, x=5, y=9)
        fp = placed.footprint_tiles()
        for p in macro.ports:
            assert placed.port_tile(p) in fp
            assert placed.port_access_tile(p) not in fp


def test_macro_internals_validate_cleanly(gs_problem):
    for macro in gs_problem.macros.values():
        placed = PlacedMacro(cell=macro, x=0, y=0)
        report = validate(placed.entities(), DB)
        assert not report.by_kind("overlap"), f"{macro.id}: {report}"


def test_validator_catches_injected_overlap(gs_problem):
    macro = next(m for m in gs_problem.macros.values() if m.kind == "recipe-band")
    ents = PlacedMacro(cell=macro, x=0, y=0).entities()
    clash = next(e for e in ents if e.name in DB.assemblers)
    ents.append(
        Entity(name="transport-belt", position=Position(clash.position.x, clash.position.y),
               direction=EAST)
    )
    report = validate(ents, DB)
    assert report.by_kind("overlap")


def test_validator_bounds():
    ents = [Entity(name="transport-belt", position=Position(10.5, 0.5), direction=EAST)]
    assert validate(ents, DB, bounds=(0, 0, 5, 5)).by_kind("bounds")
    assert validate(ents, DB, bounds=(0, 0, 20, 5)).ok


def test_validator_inserter_targets():
    from factopt.model.blueprint import NORTH

    # Inserter at (1,1) picking from north (1,0), dropping to south (1,2).
    ins = Entity(name="fast-inserter", position=Position(1.5, 1.5), direction=NORTH)
    belt_pick = Entity(name="transport-belt", position=Position(1.5, 0.5), direction=EAST)
    belt_drop = Entity(name="transport-belt", position=Position(1.5, 2.5), direction=EAST)
    assert validate([ins, belt_pick, belt_drop], DB).ok
    assert validate([ins, belt_pick], DB).by_kind("inserter")


def test_validator_flow_paths():
    # Straight EAST belt run from (0,0) to (4,0).
    belts = [
        Entity(name="transport-belt", position=Position(x + 0.5, 0.5), direction=EAST)
        for x in range(5)
    ]
    assert validate(belts, DB, flows=[((0, 0), (4, 0))]).ok
    # Break the middle: no path.
    broken = belts[:2] + belts[3:]
    assert validate(broken, DB, flows=[((0, 0), (4, 0))]).by_kind("flow")


def test_validator_flow_through_underground():
    ents = [
        Entity(name="transport-belt", position=Position(0.5, 0.5), direction=EAST),
        Entity(name="underground-belt", position=Position(1.5, 0.5), direction=EAST,
               extra={"type": "input"}),
        Entity(name="underground-belt", position=Position(5.5, 0.5), direction=EAST,
               extra={"type": "output"}),
        Entity(name="transport-belt", position=Position(6.5, 0.5), direction=EAST),
    ]
    assert validate(ents, DB, flows=[((0, 0), (6, 0))]).ok


def test_fanout_ports_reachable_from_lane(gs_problem):
    """Every output port of a fanned-out macro is belt-reachable from the
    lane's first tile (the splitter cascade actually distributes)."""
    for macro in gs_problem.macros.values():
        outs = [p for p in macro.ports if p.direction == "output"]
        if len(outs) < 2:
            continue
        placed = PlacedMacro(cell=macro, x=0, y=0)
        ents = placed.entities()
        report = validate(ents, DB)
        assert not report.by_kind("overlap"), f"{macro.id}: {report}"
        # Find a source belt tile on the output lane (west end of lane row).
        first = outs[0]
        # Walk backwards: use the leftmost belt tile in the same row region.
        from factopt.validate import BeltGraph

        graph = BeltGraph(ents, DB)
        starts = [t for t in graph.at if t[0] == 0]
        for p in outs:
            tile = placed.port_tile(p)
            assert any(graph.reachable(s, tile) for s in starts), (
                f"{macro.id}: port {p.id} at {tile} unreachable"
            )
