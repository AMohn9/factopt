"""Steiner-tree belt router: trees, splitter junctions, failure attribution."""

import pytest

from factopt.data import vanilla
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST
from factopt.routing import Grid, route_tree
from factopt.validate import validate

DB = vanilla.DB


def _flows_ok(tree, start, sinks):
    report = validate(
        tree.to_entities(), DB, flows=[(start, g) for g, _ in sinks]
    )
    assert not report.by_kind("overlap"), str(report)
    assert not report.by_kind("flow"), str(report)


def test_single_sink_is_a_plain_path():
    grid = Grid(width=10, height=5)
    tree, failed = route_tree(grid, (0, 2), [((8, 2), EAST)], DB)
    assert failed is None
    assert not tree.splitters
    assert tree.length == 9
    _flows_ok(tree, (0, 2), [((8, 2), EAST)])


def test_two_sinks_share_one_trunk_with_one_splitter():
    grid = Grid(width=20, height=12)
    sinks = [((18, 2), EAST), ((18, 10), EAST)]
    tree, failed = route_tree(grid, (0, 6), sinks, DB, start_dir=EAST, turn_penalty=0.3)
    assert failed is None
    assert len(tree.splitters) == 1
    # Sharing beats two disjoint paths: strictly fewer tiles than 2 * L.
    assert tree.length < (19 + 4) + (19 + 4)
    _flows_ok(tree, (0, 6), sinks)


def test_four_sinks_three_splitters():
    grid = Grid(width=30, height=20)
    sinks = [((25, 5), EAST), ((12, 2), EAST), ((12, 12), EAST), ((20, 16), EAST)]
    tree, failed = route_tree(grid, (0, 5), sinks, DB, start_dir=EAST)
    assert failed is None
    assert len(tree.splitters) == 3
    assert not tree.conflicts
    assert len(tree.branch_paths) == 4
    _flows_ok(tree, (0, 5), sinks)


def test_splitter_never_lands_on_a_mouth():
    """Source and sink mouths can never be junction tiles."""
    grid = Grid(width=20, height=12)
    sinks = [((18, 6), EAST), ((10, 1), NORTH), ((10, 11), SOUTH)]
    tree, failed = route_tree(grid, (0, 6), sinks, DB, start_dir=EAST)
    assert failed is None
    mouths = {(0, 6)} | {g for g, _ in sinks}
    for s in tree.splitters:
        assert not (set(s.tiles()) & mouths)


def test_junction_respects_goal_dir():
    """Every sink's terminal belt faces the sink's requested entry direction."""
    grid = Grid(width=20, height=14)
    sinks = [((18, 3), EAST), ((18, 11), SOUTH)]
    tree, failed = route_tree(grid, (0, 7), sinks, DB, start_dir=EAST)
    assert failed is None
    assert tree.belts[(18, 3)].direction == EAST
    assert tree.belts[(18, 11)].direction == SOUTH


def test_branch_can_dive_under_walls():
    """A branch uses undergrounds like the trunk does."""
    grid = Grid(width=24, height=16)
    # Full-width wall between the trunk row and the second sink, 3 tiles
    # thick: no surface detour exists, the branch must dive.
    for x in range(24):
        for y in range(10, 13):
            grid.blocked.add((x, y))
    sinks = [((22, 5), EAST), ((12, 14), SOUTH)]
    tree, failed = route_tree(grid, (0, 5), sinks, DB, start_dir=EAST)
    assert failed is None
    assert tree.undergrounds >= 1
    _flows_ok(tree, (0, 5), sinks)


def test_unreachable_sink_reports_index():
    grid = Grid(width=30, height=20)
    for y in range(20):  # full-height wall too thick to dive under
        for x in range(14, 23):
            grid.blocked.add((x, y))
    sinks = [((10, 5), EAST), ((28, 5), EAST)]
    tree, failed = route_tree(grid, (0, 5), sinks, DB, start_dir=EAST)
    assert tree is None
    assert failed == 1


def test_tight_corridor_leaves_no_junction():
    """A trunk squeezed in a 1-wide corridor cannot host a splitter half, so
    a second sink behind the corridor walls fails (and names itself)."""
    grid = Grid(width=16, height=7)
    for x in range(16):
        for y in (0, 1, 3, 5, 6):
            grid.blocked.add((x, y))
    grid.blocked -= {(0, 1), (15, 5)}  # leave the mouths themselves usable
    sinks = [((15, 2), EAST), ((15, 4), EAST)]
    # Row 2 is the only open corridor to (15,2); row 4 is walled at y=3/5.
    grid.blocked -= {(15, 4)}
    tree, failed = route_tree(grid, (0, 2), sinks, DB, start_dir=EAST)
    assert tree is None
    assert failed == 1


def test_congestion_cost_steers_junction_choice():
    """A tile-cost hotspot on the cheap side pushes the branch's junction and
    path elsewhere."""
    grid = Grid(width=20, height=12)
    sinks = [((18, 6), EAST), ((10, 11), SOUTH)]
    hot = {(x, y) for x in range(4, 12) for y in range(7, 11)}

    def cost(t):
        return 50.0 if t in hot else 0.0

    tree, failed = route_tree(grid, (0, 6), sinks, DB, start_dir=EAST, tile_cost=cost)
    assert failed is None
    assert not (tree.tiles() & hot)


def test_faster_belts_use_matching_splitters():
    grid = Grid(width=20, height=12)
    sinks = [((18, 2), EAST), ((18, 10), EAST)]
    tree, failed = route_tree(
        grid, (0, 6), sinks, DB, belt="express-transport-belt", start_dir=EAST
    )
    assert failed is None
    assert all(s.name == "express-splitter" for s in tree.splitters)
    assert all(
        b.name in ("express-transport-belt", "express-underground-belt")
        for b in tree.belts.values()
    )


def test_codec_roundtrip_with_splitters():
    from factopt.codec import decode, encode
    from factopt.model.blueprint import Blueprint

    grid = Grid(width=20, height=12)
    sinks = [((18, 2), EAST), ((18, 10), EAST), ((10, 1), NORTH)]
    tree, failed = route_tree(grid, (0, 6), sinks, DB, start_dir=EAST)
    assert failed is None
    bp = Blueprint(label="steiner", entities=tree.to_entities())
    back = decode(encode(bp))
    assert len(back.entities) == len(bp.entities)
