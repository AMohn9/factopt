from factopt.codec import decode, encode
from factopt.data import vanilla
from factopt.model import Blueprint
from factopt.routing import Grid, route_belt

DB = vanilla.DB


def test_straight_path_no_underground():
    grid = Grid(width=8, height=1)
    route = route_belt(grid, (0, 0), (5, 0), DB, belt="transport-belt")
    assert route is not None
    assert route.undergrounds == 0
    # 6 tiles from x=0..5 inclusive.
    assert route.length == 6
    assert all(b.name == "transport-belt" for b in route.belts)
    # Tiles are contiguous along the row.
    xs = sorted(b.x for b in route.belts)
    assert xs == [0, 1, 2, 3, 4, 5]


def test_underground_forced_over_wall():
    # 1-tall corridor with a blocked tile in the middle: the only way across is
    # to dive under it.
    grid = Grid(width=5, height=1, blocked={(2, 0)})
    route = route_belt(grid, (0, 0), (4, 0), DB, belt="transport-belt")
    assert route is not None
    assert route.undergrounds >= 1
    # An underground input and output exist, both of the yellow underground.
    kinds = {(b.underground_type) for b in route.belts if b.underground}
    assert kinds == {"input", "output"}
    assert all(b.name == "underground-belt" for b in route.belts if b.underground)
    # The blocked tile is spanned, not occupied.
    assert (2, 0) not in route.tiles()


def test_no_underground_when_disabled_is_infeasible():
    grid = Grid(width=5, height=1, blocked={(2, 0)})
    route = route_belt(grid, (0, 0), (4, 0), DB, allow_underground=False)
    assert route is None


def test_underground_respects_max_distance():
    # A wall 6 tiles thick exceeds yellow's reach (spans at most 4 tiles), and
    # the corridor is 1 tall so no detour exists -> infeasible.
    blocked = {(x, 0) for x in range(2, 8)}
    grid = Grid(width=12, height=1, blocked=blocked)
    route = route_belt(grid, (0, 0), (11, 0), DB, belt="transport-belt")
    assert route is None
    # Express belts reach further (spans up to 8) -> feasible across the same wall.
    route2 = route_belt(grid, (0, 0), (11, 0), DB, belt="express-transport-belt")
    assert route2 is not None
    assert route2.undergrounds >= 1


def test_detours_around_obstacle_when_room():
    # A wall with headroom: the router can go around without diving.
    grid = Grid(width=6, height=4, blocked={(3, 0), (3, 1)})
    route = route_belt(grid, (0, 0), (5, 0), DB, belt="transport-belt")
    assert route is not None
    assert (3, 0) not in route.tiles() and (3, 1) not in route.tiles()
    for b in route.belts:
        assert grid.in_bounds(b.x, b.y)


def test_route_roundtrips_through_codec():
    grid = Grid(width=5, height=1, blocked={(2, 0)})
    route = route_belt(grid, (0, 0), (4, 0), DB, belt="transport-belt")
    bp = Blueprint(entities=route.to_entities())
    back = decode(encode(bp))
    ug = [e for e in back.entities if e.name == "underground-belt"]
    assert ug, "underground entities should survive roundtrip"
    assert all(e.extra.get("type", "input") in {"input", "output"} for e in ug)
