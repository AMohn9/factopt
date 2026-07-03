"""Multi-net detailed router (M4).

Given a placed master solution, routes every :class:`FlowNet` as a concrete
belt **tree** (one source, every sink, splitters at junctions -- see
:mod:`factopt.routing.steiner`) using PathFinder-style negotiated congestion:

* each round, every contested net is ripped up **whole-tree** and re-grown
  with :func:`~factopt.routing.steiner.route_tree`, where tiles currently
  used by other nets' trees cost extra (present sharing) and tiles that keep
  being contested accumulate a history cost;
* the shared-tile penalty grows each round until no tile is shared;
* a net with no tree even on the otherwise-empty grid is a hard ``no_path``
  failure (attributed to the first unreachable sink), and nets still
  overlapping at the round limit fail with ``congestion`` -- both carry
  enough structure for Benders cuts.

Trees start at the source port's access tile (items arrive along the port's
flow direction) and reach every sink port's access tile facing that sink's
lane.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.data.database import Database
from factopt.macros.library import FlowNet, MacroProblem
from factopt.master.model import MasterSolution
from factopt.model.blueprint import Entity
from factopt.routing.steiner import BeltTree, Grid, route_tree

_MAX_ROUNDS = 24
_PRESENT_BASE = 6.0  # cost per other-net occupant of a tile, round 0
_PRESENT_GROWTH = 1.5
_HISTORY_INC = 2.0
_OFF_COARSE_COST = 0.4  # mild pull toward the master's coarse route
_TURN_PENALTY = 0.3


@dataclass(frozen=True)
class RoutingFailure:
    kind: str  # "no_path" | "congestion" | "port_blocked" | "port_conflict"
    net_id: str
    item: str
    source_macro: str
    sink_macro: str  # for multi-sink nets: the sink the failure is attributed to
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
    total_splitters: int = 0
    total_turns: int = 0
    rounds: int = 0


@dataclass
class RoutingResult:
    feasible: bool
    entities: list[Entity] = field(default_factory=list)
    # net id -> per-sink tile paths (trunk first, then each branch).
    paths: dict[str, list[list[tuple[int, int]]]] = field(default_factory=dict)
    failures: list[RoutingFailure] = field(default_factory=list)
    metrics: RoutingMetrics = field(default_factory=RoutingMetrics)


@dataclass
class _Sink:
    macro: str
    port: str
    goal: tuple[int, int]
    goal_dir: int


@dataclass
class _Net:
    net: FlowNet
    start: tuple[int, int]
    start_dir: int
    sinks: list[_Sink]
    route: BeltTree | None = None
    failed_sink: int | None = None  # index into sinks when routing failed

    @property
    def id(self) -> str:
        return self.net.id

    def endpoints(self) -> set[tuple[int, int]]:
        return {self.start} | {s.goal for s in self.sinks}

    def hpwl(self) -> int:
        xs = [self.start[0]] + [s.goal[0] for s in self.sinks]
        ys = [self.start[1]] + [s.goal[1] for s in self.sinks]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))

    def fail(self, kind: str, **kw) -> RoutingFailure:
        idx = self.failed_sink if self.failed_sink is not None else 0
        s = self.sinks[idx] if self.sinks else None
        return RoutingFailure(
            kind=kind,
            net_id=self.net.id,
            item=self.net.item,
            source_macro=self.net.source_macro,
            sink_macro=s.macro if s else "",
            start=self.start,
            goal=s.goal if s else None,
            **kw,
        )


def _count_turns(tree: BeltTree) -> int:
    turns = 0
    for path in tree.branch_paths:
        prev = None
        for t in path:
            b = tree.belts.get(t)
            if b is None:
                prev = None  # splitter tile: direction preserved, reset
                continue
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
        sp = src_pm.cell.port(net.source_port)
        start = src_pm.port_access_tile(sp)
        sinks: list[_Sink] = []
        for fs in net.sinks:
            dst_pm = solution.placements[fs.macro]
            dp = dst_pm.cell.port(fs.port)
            sinks.append(
                _Sink(macro=fs.macro, port=fs.port, goal=dst_pm.port_access_tile(dp),
                      goal_dir=dst_pm.port_flow_dir(dp))
            )
        record = _Net(net=net, start=start, start_dir=src_pm.port_flow_dir(sp), sinks=sinks)

        bad_tile = None
        for t in [start] + [s.goal for s in sinks]:
            if not (0 <= t[0] < width and 0 <= t[1] < height) or t in static_blocked:
                bad_tile = t
                break
        if bad_tile is not None:
            record.failed_sink = next(
                (i for i, s in enumerate(sinks) if s.goal == bad_tile), 0
            )
            failures.append(record.fail("port_blocked"))
            continue

        # Two ports whose access tiles coincide can never both be served.
        conflict = None
        owners = [(start, (net.id, net.source_macro, net.source_port))]
        owners += [(s.goal, (net.id, s.macro, s.port)) for s in sinks]
        for tile, owner in owners:
            if tile in tile_owner and tile_owner[tile][0] != net.id:
                conflict = (tile, tile_owner[tile], owner)
                break
            if tile in tile_owner and tile_owner[tile] != owner:
                # Two pins of the *same* net share a mouth tile: also fatal.
                conflict = (tile, tile_owner[tile], owner)
                break
            tile_owner[tile] = owner
        if conflict is not None:
            tile, other, mine = conflict
            record.failed_sink = next(
                (i for i, s in enumerate(sinks) if s.goal == tile), 0
            )
            failures.append(
                record.fail(
                    "port_conflict",
                    contested_tiles=frozenset({tile}),
                    ports=((other[1], other[2]), (mine[1], mine[2])),
                )
            )
            continue
        nets.append(record)
        reserved.add(start)
        reserved.update(s.goal for s in sinks)

    # Difficulty order: heavy flows first, then larger pin spread first.
    nets.sort(key=lambda n: (-n.net.rate_per_sec, -n.hpwl()))

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
        # obstacles, since negotiation can never move an endpoint. The active
        # net's own sibling-sink mouths are managed inside route_tree.
        blocked = set(static_blocked)
        blocked |= reserved - active.endpoints()
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
        """Rip up ``n``'s whole tree and re-grow it against the other nets'
        current trees."""
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
            grid.blocked |= hard_tiles - n.endpoints()
        n.route, n.failed_sink = route_tree(
            grid,
            n.start,
            [(s.goal, s.goal_dir) for s in n.sinks],
            db,
            belt=belt,
            start_dir=n.start_dir,
            turn_penalty=_TURN_PENALTY,
            tile_cost=tile_cost_fn(n, occupancy),
            ug_blocked=ug_blocked,
        )

    def contested_nets() -> tuple[set[str], set[tuple[int, int]]]:
        """Nets whose current trees share tiles (or self-cross)."""
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
    # rip up and re-grow the trees actually in conflict, so settled trees
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

    # Hardening fallback: if negotiation stalled, grow the stragglers with
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
    # tree (computed on the empty grid), the nets sitting on that tree are
    # ripped up, the straggler routes first, and the victims re-route around
    # it -- all with hard blocking so the outcome is conflict-free.
    for n in nets:
        if n.id in hard_failures or n.route is not None:
            continue
        ideal, _failed = route_tree(
            make_grid(n),
            n.start,
            [(s.goal, s.goal_dir) for s in n.sinks],
            db,
            belt=belt,
            start_dir=n.start_dir,
        )
        if ideal is None:
            continue  # genuinely walled in; classified below
        victims = [
            o for o in nets if o is not n and o.route is not None
            and o.route.tiles() & ideal.tiles()
        ]
        saved = {o.id: (o.route, o.failed_sink) for o in victims}
        for o in victims:
            o.route = None
        reroute(n, hard_block_others=True)
        for o in victims:
            reroute(o, hard_block_others=True)
        if n.route is None or any(o.route is None for o in victims):
            # Rip-up made things worse; restore the previous state.
            n.route = None
            for o in victims:
                o.route, o.failed_sink = saved[o.id]

    # Classify what is still broken.
    bad, _ = contested_nets()
    bad -= hard_failures
    for n in nets:
        if n.id in hard_failures:
            continue
        if n.route is None:
            failures.append(n.fail("congestion" if n.id in bad else "no_path"))
    for n in nets:
        if n.id in hard_failures:
            failures.append(n.fail("no_path"))
    remaining, remaining_tiles = contested_nets()
    remaining -= hard_failures
    for n in nets:
        if n.id in remaining:
            failures.append(
                n.fail(
                    "congestion",
                    contested_tiles=frozenset(
                        remaining_tiles & (n.route.tiles() if n.route else set())
                    ),
                )
            )
            n.route = None

    metrics = RoutingMetrics(rounds=rounds_used)
    entities: list[Entity] = []
    paths: dict[str, list[list[tuple[int, int]]]] = {}
    for n in nets:
        if n.route is None:
            continue
        entities.extend(n.route.to_entities())
        paths[n.id] = n.route.branch_paths
        metrics.total_belt_length += n.route.length
        metrics.total_undergrounds += n.route.undergrounds
        metrics.total_splitters += len(n.route.splitters)
        metrics.total_turns += _count_turns(n.route)

    return RoutingResult(
        feasible=not failures,
        entities=entities,
        paths=paths,
        failures=failures,
        metrics=metrics,
    )
