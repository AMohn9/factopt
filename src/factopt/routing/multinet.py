"""Multi-net detailed router (M4).

Given a placed master solution, routes every :class:`FlowNet` as a concrete
belt path using PathFinder-style negotiated congestion:

* each round, every net is ripped up and re-routed with
  :func:`~factopt.routing.astar.route_belt`, where tiles currently used by
  other nets cost extra (present sharing) and tiles that keep being contested
  accumulate a history cost;
* the shared-tile penalty grows each round until no tile is shared;
* a net with no path even on the otherwise-empty grid is a hard
  ``no_path`` failure, and nets still overlapping at the round limit fail
  with ``congestion`` -- both carry enough structure for Benders cuts.

Routes start at the source port's access tile (items arrive along the port's
flow direction) and end at the sink port's access tile facing the sink lane.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.data.database import Database
from factopt.macros.library import FlowNet, MacroProblem
from factopt.master.model import MasterSolution
from factopt.model.blueprint import Entity
from factopt.routing.astar import BeltRoute, Grid, route_belt

_MAX_ROUNDS = 24
_PRESENT_BASE = 6.0  # cost per other-net occupant of a tile, round 0
_PRESENT_GROWTH = 1.5
_HISTORY_INC = 2.0
_MOUTH_COST = 40.0  # foreign port access tiles: strongly discouraged, not walls
_OFF_COARSE_COST = 0.4  # mild pull toward the master's coarse route
_TURN_PENALTY = 0.3


@dataclass(frozen=True)
class RoutingFailure:
    kind: str  # "no_path" | "congestion" | "port_blocked" | "port_conflict"
    net_id: str
    item: str
    source_macro: str
    sink_macro: str
    start: tuple[int, int] | None = None
    goal: tuple[int, int] | None = None
    contested_tiles: frozenset[tuple[int, int]] = frozenset()
    # (macro_id, port_id) pairs involved, e.g. the two ports whose access
    # tiles coincide for a port_conflict.
    ports: tuple[tuple[str, str], ...] = ()

    def __str__(self) -> str:
        return (
            f"[{self.kind}] net {self.net_id} "
            f"({self.source_macro} -> {self.sink_macro}) start={self.start} goal={self.goal}"
        )


@dataclass
class RoutingMetrics:
    total_belt_length: int = 0
    total_undergrounds: int = 0
    total_turns: int = 0
    rounds: int = 0


@dataclass
class RoutingResult:
    feasible: bool
    entities: list[Entity] = field(default_factory=list)
    paths: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    failures: list[RoutingFailure] = field(default_factory=list)
    metrics: RoutingMetrics = field(default_factory=RoutingMetrics)


@dataclass
class _Net:
    net: FlowNet
    start: tuple[int, int]
    start_dir: int
    goal: tuple[int, int]
    goal_dir: int
    route: BeltRoute | None = None

    @property
    def id(self) -> str:
        return self.net.id


def _count_turns(route: BeltRoute) -> int:
    turns = 0
    prev = None
    for b in route.belts:
        if prev is not None and b.direction != prev:
            turns += 1
        prev = b.direction
    return turns


def route_nets(
    problem: MacroProblem,
    solution: MasterSolution,
    db: Database,
    belt: str = "transport-belt",
    max_rounds: int = _MAX_ROUNDS,
) -> RoutingResult:
    width, height = solution.width, solution.height
    static_blocked: set[tuple[int, int]] = set()
    for pm in solution.placements.values():
        static_blocked |= pm.footprint_tiles()

    # Build net endpoints; reserve every access tile so no other route parks
    # on top of a port mouth.
    nets: list[_Net] = []
    failures: list[RoutingFailure] = []
    reserved: set[tuple[int, int]] = set()
    tile_owner: dict[tuple[int, int], tuple[str, str, str]] = {}  # tile -> net, macro, port
    for net in problem.nets:
        src_pm = solution.placements[net.source_macro]
        dst_pm = solution.placements[net.sink_macro]
        sp = src_pm.cell.port(net.source_port)
        dp = dst_pm.cell.port(net.sink_port)
        start = src_pm.port_access_tile(sp)
        goal = dst_pm.port_access_tile(dp)
        record = _Net(
            net=net,
            start=start,
            start_dir=sp.flow_entry_dir,
            goal=goal,
            goal_dir=dp.flow_entry_dir,
        )
        in_bounds = all(0 <= t[0] < width and 0 <= t[1] < height for t in (start, goal))
        if not in_bounds or start in static_blocked or goal in static_blocked:
            failures.append(
                RoutingFailure(
                    kind="port_blocked",
                    net_id=net.id,
                    item=net.item,
                    source_macro=net.source_macro,
                    sink_macro=net.sink_macro,
                    start=start,
                    goal=goal,
                )
            )
            continue
        # Two ports whose access tiles coincide can never both be served.
        conflict = None
        for tile, owner in (
            (start, (net.id, net.source_macro, net.source_port)),
            (goal, (net.id, net.sink_macro, net.sink_port)),
        ):
            if tile in tile_owner and tile_owner[tile][0] != net.id:
                conflict = (tile, tile_owner[tile], owner)
                break
            tile_owner[tile] = owner
        if conflict is not None:
            tile, other, mine = conflict
            failures.append(
                RoutingFailure(
                    kind="port_conflict",
                    net_id=net.id,
                    item=net.item,
                    source_macro=net.source_macro,
                    sink_macro=net.sink_macro,
                    start=start,
                    goal=goal,
                    contested_tiles=frozenset({tile}),
                    ports=((other[1], other[2]), (mine[1], mine[2])),
                )
            )
            continue
        nets.append(record)
        reserved.add(start)
        reserved.add(goal)

    # Difficulty order: heavy flows first, longer nets first.
    nets.sort(key=lambda n: (-n.net.rate_per_sec, -(abs(n.start[0] - n.goal[0]) + abs(n.start[1] - n.goal[1]))))

    coarse_cells: dict[str, set[tuple[int, int]]] = {}
    if solution.coarse is not None:
        for n in nets:
            cells: set[tuple[int, int]] = set()
            for a, b in solution.coarse.routes.get(n.id, []):
                cells.add(a)
                cells.add(b)
            coarse_cells[n.id] = cells

    history: dict[tuple[int, int], float] = {}
    present_cost = _PRESENT_BASE
    rounds_used = 0

    def make_grid(active: _Net) -> Grid:
        # Foreign port mouths hold those nets' fixed endpoint belts: hard
        # obstacles, since negotiation can never move an endpoint.
        blocked = set(static_blocked)
        blocked |= reserved - {active.start, active.goal}
        return Grid(width=width, height=height, blocked=blocked)

    def tile_cost_fn(active: _Net, occupancy: dict[tuple[int, int], int]):
        cell = solution.coarse.cell if solution.coarse is not None else None
        guide = coarse_cells.get(active.id)

        def cost(t: tuple[int, int]) -> float:
            c = occupancy.get(t, 0) * present_cost + history.get(t, 0.0)
            if guide and cell:
                if (t[0] // cell, t[1] // cell) not in guide:
                    c += _OFF_COARSE_COST
            return c

        return cost

    hard_failures: set[str] = set()

    def reroute(n: _Net, hard_block_others: bool) -> None:
        """Re-route ``n`` against the other nets' current routes."""
        occupancy: dict[tuple[int, int], int] = {}
        ug_blocked: set[tuple[int, int, str]] = set()
        hard_tiles: set[tuple[int, int]] = set()
        for other in nets:
            if other is n or other.route is None:
                continue
            for t in other.route.tiles():
                occupancy[t] = occupancy.get(t, 0) + 1
                hard_tiles.add(t)
            ug_blocked |= other.route.ug_span_tiles()
        grid = make_grid(n)
        if hard_block_others:
            grid.blocked |= hard_tiles - {n.start, n.goal}
        n.route = route_belt(
            grid,
            n.start,
            n.goal,
            db,
            belt=belt,
            goal_dir=n.goal_dir,
            start_dir=n.start_dir,
            turn_penalty=_TURN_PENALTY,
            tile_cost=tile_cost_fn(n, occupancy),
            ug_blocked=ug_blocked,
        )

    def contested_nets() -> tuple[set[str], set[tuple[int, int]]]:
        """Nets whose current routes share tiles (or self-cross)."""
        tile_users: dict[tuple[int, int], list[str]] = {}
        bad: set[str] = set()
        tiles: set[tuple[int, int]] = set()
        for n in nets:
            if n.route is None:
                continue
            for t in n.route.tiles():
                tile_users.setdefault(t, []).append(n.id)
            if n.route.conflicts:
                bad.add(n.id)
                tiles.update(n.route.conflicts)
        for t, users in tile_users.items():
            if len(users) > 1:
                bad.update(users)
                tiles.add(t)
        return bad, tiles

    # Round 0: route everyone against soft congestion costs; afterwards only
    # rip up and re-route the nets actually in conflict, so settled routes
    # stay put and pairs cannot swap channels forever.
    for n in nets:
        reroute(n, hard_block_others=False)
        if n.route is None:
            hard_failures.add(n.id)

    for rnd in range(max_rounds):
        rounds_used = rnd + 1
        bad, tiles = contested_nets()
        bad -= hard_failures
        if not bad:
            break
        for t in tiles:
            history[t] = history.get(t, 0.0) + _HISTORY_INC
        present_cost *= _PRESENT_GROWTH
        for n in nets:
            if n.id in bad:
                reroute(n, hard_block_others=False)
                if n.route is None:
                    hard_failures.add(n.id)

    # Hardening fallback: if negotiation stalled, route the stragglers with
    # everything else as hard obstacles (strict sequential completion).
    bad, _ = contested_nets()
    bad -= hard_failures
    if bad:
        for n in nets:
            if n.id in bad:
                n.route = None
        for n in nets:
            if n.id in bad:
                reroute(n, hard_block_others=True)

    # Targeted rip-up: a straggler that still cannot route gets its ideal
    # path (computed on the empty grid), the nets sitting on that path are
    # ripped up, the straggler routes first, and the victims re-route around
    # it -- all with hard blocking so the outcome is conflict-free.
    for n in nets:
        if n.id in hard_failures or n.route is not None:
            continue
        ideal = route_belt(
            make_grid(n),
            n.start,
            n.goal,
            db,
            belt=belt,
            goal_dir=n.goal_dir,
            start_dir=n.start_dir,
        )
        if ideal is None:
            continue  # genuinely walled in; classified below
        victims = [
            o for o in nets if o is not n and o.route is not None
            and o.route.tiles() & ideal.tiles()
        ]
        saved = {o.id: o.route for o in victims}
        for o in victims:
            o.route = None
        reroute(n, hard_block_others=True)
        for o in victims:
            reroute(o, hard_block_others=True)
        if n.route is None or any(o.route is None for o in victims):
            # Rip-up made things worse; restore the previous state.
            n.route = None
            for o in victims:
                o.route = saved[o.id]

    # Classify what is still broken.
    for n in nets:
        if n.id in hard_failures:
            continue
        if n.route is None:
            failures.append(
                RoutingFailure(
                    kind="congestion" if n.id in bad else "no_path",
                    net_id=n.id,
                    item=n.net.item,
                    source_macro=n.net.source_macro,
                    sink_macro=n.net.sink_macro,
                    start=n.start,
                    goal=n.goal,
                )
            )
    for n in nets:
        if n.id in hard_failures:
            failures.append(
                RoutingFailure(
                    kind="no_path",
                    net_id=n.id,
                    item=n.net.item,
                    source_macro=n.net.source_macro,
                    sink_macro=n.net.sink_macro,
                    start=n.start,
                    goal=n.goal,
                )
            )
    remaining, remaining_tiles = contested_nets()
    remaining -= hard_failures
    for n in nets:
        if n.id in remaining:
            failures.append(
                RoutingFailure(
                    kind="congestion",
                    net_id=n.id,
                    item=n.net.item,
                    source_macro=n.net.source_macro,
                    sink_macro=n.net.sink_macro,
                    start=n.start,
                    goal=n.goal,
                    contested_tiles=frozenset(
                        remaining_tiles & (n.route.tiles() if n.route else set())
                    ),
                )
            )
            n.route = None

    metrics = RoutingMetrics(rounds=rounds_used)
    entities: list[Entity] = []
    paths: dict[str, list[tuple[int, int]]] = {}
    for n in nets:
        if n.route is None:
            continue
        entities.extend(n.route.to_entities())
        # Path in start->goal order for visualization.
        paths[n.id] = [(b.x, b.y) for b in n.route.belts]
        metrics.total_belt_length += n.route.length
        metrics.total_undergrounds += n.route.undergrounds
        metrics.total_turns += _count_turns(n.route)

    return RoutingResult(
        feasible=not failures,
        entities=entities,
        paths=paths,
        failures=failures,
        metrics=metrics,
    )
