"""Steiner-tree belt router: one net, one source, many sinks.

Grows a belt **tree** instead of a point-to-point path. The trunk is routed
source -> first sink with the same direction-aware A* as
:func:`factopt.routing.astar.route_belt`; every later sink is routed from
*any tile of the existing tree* by seeding one multi-source A* search with a
candidate **splitter junction** per straight tree belt, so the search itself
picks the cheapest tap point (VLSI-style Steiner growth).

Junction geometry (Factorio): a splitter facing ``d`` occupies two tiles
side-by-side perpendicular to ``d``, takes input on both back tiles and
ejects forward from both front tiles. Tapping a tree belt at tile ``T``
(flowing ``d``, arrival direction also ``d``) therefore means:

* replace the belt at ``T`` with a splitter covering ``T`` and ``T + p``
  (``p`` one of the two perpendicular offsets, which must be a free tile);
* the old continuation at ``T + d`` keeps being fed by the first half;
* the branch starts at ``T + p + d`` moving ``d``, fed by the second half.

Corners (arrival != exit), underground endpoints, the source mouth, and sink
mouths can never be junctions. A belt already converted to a splitter cannot
be tapped again (a splitter has exactly two outputs).

Rates are the caller's contract: a trunk's *total* demand must fit one belt
(the multi-trunk partition upstream guarantees this), so every tree edge --
which carries the demand of the sinks below it -- fits too.

Fidelity notes (same level as the point-to-point router): side-loading onto
foreign belts and merge-feeding a splitter's second input from an adjacent
own branch are not modeled; validate in-game for exotic layouts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.data.database import Database
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Entity, Position
from factopt.routing.astar import (
    _DIR_VEC,
    _OPP,
    _UG_OF,
    Grid,
    PlacedBelt,
    _run_astar,
    ug_span_tiles,
)

_SPLITTER_OF = {
    "transport-belt": "splitter",
    "fast-transport-belt": "fast-splitter",
    "express-transport-belt": "express-splitter",
}

# Perpendicular offsets for a splitter facing a given direction: the two
# tiles a second splitter half may occupy relative to the tapped belt.
_PERP: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {
    NORTH: ((-1, 0), (1, 0)),
    SOUTH: ((-1, 0), (1, 0)),
    EAST: ((0, -1), (0, 1)),
    WEST: ((0, -1), (0, 1)),
}


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass(frozen=True)
class PlacedSplitter:
    """A splitter junction. ``tile`` is the tapped trunk tile (first half),
    ``other`` the second half one tile perpendicular; both face ``direction``."""

    name: str
    tile: tuple[int, int]
    other: tuple[int, int]
    direction: int

    def tiles(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return (self.tile, self.other)

    def to_entity(self) -> Entity:
        cx = (self.tile[0] + self.other[0]) / 2 + 0.5
        cy = (self.tile[1] + self.other[1]) / 2 + 0.5
        return Entity(name=self.name, position=Position(cx, cy), direction=self.direction)


@dataclass
class BeltTree:
    """A routed multi-sink net: belts + splitter junctions forming one tree."""

    belts: dict[tuple[int, int], PlacedBelt]
    splitters: list[PlacedSplitter]
    undergrounds: int
    ug_spans: list[tuple[tuple[int, int], tuple[int, int], int]] = field(default_factory=list)
    # Tiles placed twice during construction (self-crossing branch). A tree
    # with conflicts is not physically buildable; the caller must retry.
    conflicts: list[tuple[int, int]] = field(default_factory=list)
    # Per-sink tile paths in construction order (trunk first), for debug/SVG.
    branch_paths: list[list[tuple[int, int]]] = field(default_factory=list)

    def tiles(self) -> set[tuple[int, int]]:
        out = set(self.belts)
        for s in self.splitters:
            out.update(s.tiles())
        return out

    @property
    def length(self) -> int:
        return len(self.tiles())

    def ug_span_tiles(self) -> set[tuple[int, int, str]]:
        return ug_span_tiles(self.ug_spans)

    def to_entities(self) -> list[Entity]:
        return [b.to_entity() for b in self.belts.values()] + [
            s.to_entity() for s in self.splitters
        ]


class _TreeState:
    """Mutable tree under construction: belts, junction candidates, splitters."""

    def __init__(self, belt_name: str, splitter_name: str, no_tap: set[tuple[int, int]]):
        self.belt_name = belt_name
        self.splitter_name = splitter_name
        self.belts: dict[tuple[int, int], PlacedBelt] = {}
        self.splitter_at: dict[tuple[int, int], PlacedSplitter] = {}
        self.splitters: list[PlacedSplitter] = []
        # Straight surface belts (arrival dir == exit dir) that may be tapped.
        self.junctions: dict[tuple[int, int], int] = {}
        self.ug_spans: list[tuple[tuple[int, int], tuple[int, int], int]] = []
        self.conflicts: list[tuple[int, int]] = []
        self.no_tap = no_tap  # source mouth + every sink mouth
        self.paths: dict[int, list[tuple[int, int]]] = {}

    def tiles(self) -> set[tuple[int, int]]:
        return set(self.belts) | set(self.splitter_at)

    def _check(self, t: tuple[int, int]) -> None:
        if t in self.belts or t in self.splitter_at:
            self.conflicts.append(t)

    def place_belt(self, t: tuple[int, int], out_dir: int, arrive: int | None) -> None:
        self._check(t)
        self.belts[t] = PlacedBelt(self.belt_name, t[0], t[1], out_dir)
        if arrive == out_dir and t not in self.no_tap:
            self.junctions[t] = out_dir
        else:
            self.junctions.pop(t, None)

    def place_ug(
        self, tin: tuple[int, int], tout: tuple[int, int], d: int, ug_name: str
    ) -> None:
        for t, kind in ((tin, "input"), (tout, "output")):
            self._check(t)
            self.belts[t] = PlacedBelt(
                ug_name, t[0], t[1], d, underground=True, underground_type=kind
            )
            self.junctions.pop(t, None)
        self.ug_spans.append((tin, tout, d))

    def split(self, T: tuple[int, int], p: tuple[int, int], d: int) -> None:
        half = (T[0] + p[0], T[1] + p[1])
        self._check(half)
        del self.belts[T]
        self.junctions.pop(T, None)
        sp = PlacedSplitter(self.splitter_name, T, half, d)
        self.splitters.append(sp)
        self.splitter_at[T] = sp
        self.splitter_at[half] = sp

    def replay(self, actions: list[tuple], sink_idx: int, arrive0: int | None, ug_name: str) -> list[object]:
        """Materialize ``actions`` into the tree. Returns the tags of any sinks
        served inline by a pass-through lane along the way (``"lane"`` actions)."""
        arrive = arrive0
        path: list[tuple[int, int]] = []
        threaded: list[object] = []
        for act in actions:
            if act[0] == "belt":
                _, t, od = act
                self.place_belt(t, od, arrive)
                path.append(t)
                arrive = od
            elif act[0] == "ug":
                _, tin, tout, d = act
                self.place_ug(tin, tout, d, ug_name)
                path.extend([tin, tout])
                arrive = d
            elif act[0] == "lane":  # run the belt through a consumer's lane
                _, entry, belt_dir, _exit_tile, exit_dir, tag = act
                self.place_belt(entry, belt_dir, arrive)
                path.append(entry)
                arrive = exit_dir
                threaded.append(tag)
            else:  # ("split", trunk_tile, perp_offset, dir)
                _, T, p, d = act
                self.split(T, p, d)
                path.append((T[0] + p[0], T[1] + p[1]))
                arrive = d
        self.paths[sink_idx] = path
        return threaded

    def freeze(self, n_sinks: int) -> BeltTree:
        return BeltTree(
            belts=self.belts,
            splitters=self.splitters,
            undergrounds=len(self.ug_spans),
            ug_spans=self.ug_spans,
            conflicts=self.conflicts,
            branch_paths=[self.paths.get(i, []) for i in range(n_sinks)],
        )


def route_tree(
    grid: Grid,
    start: tuple[int, int],
    sinks: list[tuple[tuple[int, int], int | None]],
    db: Database,
    belt: str = "transport-belt",
    allow_underground: bool = True,
    underground_penalty: float = 2.0,
    start_dir: int | None = None,
    turn_penalty: float = 0.0,
    tile_cost=None,
    ug_blocked: set | None = None,
    splitter_cost: float = 2.0,
    sink_exits: list[tuple[tuple[int, int], int] | None] | None = None,
    through_cost: float = 0.5,
) -> tuple[BeltTree | None, int | None]:
    """Route a belt tree from ``start`` to every ``(goal, goal_dir)`` sink.

    The trunk is routed to the **farthest** sink first (so it spans the net
    and later sinks tap it with short branches); the remaining sinks connect
    Prim-style, nearest-to-tree next, each branch seeded from every valid
    junction of the tree so far. If some sink cannot be reached under that
    order, alternate trunk targets are retried (each sink once) before the
    net is declared unroutable -- a trunk squeezed through a 1-wide corridor
    can make junctions impossible for one order but not another.

    Returns ``(tree, None)`` on success or ``(None, failed_sink_index)`` when
    every order fails (the failing sink of the first, preferred order; the
    partial tree is discarded -- a net is all-or-nothing).

    ``tile_cost``/``ug_blocked`` have :func:`route_belt` semantics and apply
    to every branch. While one sink is being routed, the other sinks' goal
    tiles and all existing tree tiles are hard obstacles (a branch may only
    leave the tree through a splitter).

    ``sink_exits[i]``, when given, is ``(exit_access_tile, exit_dir)`` for a
    sink whose consumer lane can be run *through*: the belt reaching that sink
    may continue out the far side toward later sinks, so the consumer is served
    inline (it picks off the passing belt) with no splitter. A sink served this
    way costs ``through_cost`` instead of ``splitter_cost`` -- the router thus
    strings roughly-colinear consumers onto one pass-by run and only branches
    with a splitter where geometry actually diverges. Sinks with no exit (or
    when ``sink_exits`` is ``None``) route exactly as before (splitter tree).
    """
    if belt not in db.belts:
        raise ValueError(f"unknown belt {belt!r}")
    if not grid.is_free(*start):
        raise ValueError(f"start {start} is not a free tile")
    for i, (gtile, _gd) in enumerate(sinks):
        if not grid.is_free(*gtile):
            raise ValueError(f"sink {i} goal {gtile} is not a free tile")
    if not sinks:
        raise ValueError("route_tree needs at least one sink")

    proto = db.belts[belt]
    belt_name = proto.name
    max_dist = proto.underground_max_distance if allow_underground else 0
    ug_name = proto.underground_name
    ug_entity = ug_name or _UG_OF.get(belt_name, belt_name)
    splitter_name = _SPLITTER_OF.get(belt_name, "splitter")

    no_tap = {start} | {g for g, _ in sinks}

    def extra(t: tuple[int, int]) -> float:
        return tile_cost(t) if tile_cost is not None else 0.0

    def attempt(trunk_sink: int) -> tuple[BeltTree | None, int | None]:
        """Grow one tree: trunk to ``trunk_sink``, then Prim for the rest."""
        state = _TreeState(belt_name, splitter_name, no_tap)
        remaining = list(range(len(sinks)))
        while remaining:
            tree_tiles = state.tiles()
            first_branch = not tree_tiles
            if first_branch:
                i = trunk_sink
            else:
                i = min(
                    remaining,
                    key=lambda j: (min(_manhattan(t, sinks[j][0]) for t in tree_tiles), j),
                )
            goal, goal_dir = sinks[i]

            if first_branch and start == goal:
                out = goal_dir if goal_dir is not None else (
                    start_dir if start_dir is not None else EAST
                )
                state.place_belt(start, out, arrive=None)
                state.paths[i] = [start]
                remaining.remove(i)
                continue

            blocked = set(grid.blocked) | tree_tiles
            blocked |= {sinks[j][0] for j in remaining if j != i}
            blocked.discard(goal)
            g2 = Grid(width=grid.width, height=grid.height, blocked=blocked)

            ugb = set(ug_blocked) if ug_blocked is not None else set()
            ugb |= ug_span_tiles(state.ug_spans)

            # Pass-through lanes for the other pending sinks: the search may run
            # the belt through them (serving them inline) instead of branching.
            lane_edges: dict[tuple[int, int], tuple[int, tuple[int, int], int, int]] = {}
            if sink_exits is not None:
                for j in remaining:
                    if j == i or sink_exits[j] is None:
                        continue
                    entry, gdir = sinks[j]
                    exit_tile, exit_dir = sink_exits[j]
                    lane_edges[entry] = (
                        gdir if gdir is not None else exit_dir,
                        exit_tile,
                        exit_dir,
                        j,
                    )

            seeds: list[tuple[tuple[int, int, int], float, tuple]] = []
            if first_branch:
                for od, (dx, dy) in _DIR_VEC.items():
                    if start_dir is not None and od == _OPP[start_dir]:
                        continue
                    nxt = (start[0] + dx, start[1] + dy)
                    if nxt == goal or g2.is_free(*nxt):
                        seeds.append(
                            ((nxt[0], nxt[1], od), 1.0 + extra(start), ("belt", start, od))
                        )
            else:
                for T, d in state.junctions.items():
                    dx, dy = _DIR_VEC[d]
                    for p in _PERP[d]:
                        half = (T[0] + p[0], T[1] + p[1])
                        if not g2.is_free(*half):
                            continue
                        nxt = (half[0] + dx, half[1] + dy)
                        if not (nxt == goal or g2.is_free(*nxt)):
                            continue
                        seeds.append(
                            (
                                (nxt[0], nxt[1], d),
                                splitter_cost + extra(T) + extra(half),
                                ("split", T, p, d),
                            )
                        )
            if not seeds:
                return None, i

            actions = _run_astar(
                g2,
                goal,
                seeds,
                ug_name=ug_name,
                max_dist=max_dist,
                goal_dir=goal_dir,
                turn_penalty=turn_penalty,
                underground_penalty=underground_penalty,
                tile_cost=tile_cost,
                ug_blocked=ugb,
                lane_edges=lane_edges,
                through_cost=through_cost,
            )
            if actions is None:
                return None, i
            threaded = state.replay(
                actions, i, arrive0=start_dir if first_branch else None, ug_name=ug_entity
            )
            remaining.remove(i)
            for j in threaded:  # consumers served inline by a pass-through lane
                if j in remaining:
                    remaining.remove(j)

        return state.freeze(len(sinks)), None

    # Trunk-target order: farthest sink first (long trunk, short taps), then
    # every other sink as a fallback, nearest last.
    by_dist = sorted(
        range(len(sinks)), key=lambda i: (-_manhattan(start, sinks[i][0]), i)
    )
    first_failure: int | None = None
    for trunk_sink in by_dist:
        tree, failed = attempt(trunk_sink)
        if tree is not None:
            return tree, None
        if first_failure is None:
            first_failure = failed
    return None, first_failure
