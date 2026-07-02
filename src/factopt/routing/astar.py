"""A* belt router with underground-belt support.

Routes a single belt line from a start tile to a goal tile on a grid of
obstacles. Two move types:

* **Surface step** — advance one tile to a free orthogonal neighbor (cost 1),
  placing a transport belt that points at the next tile.
* **Underground jump** — dive under up to ``underground_max_distance - 1``
  obstacle tiles: place an underground "input" at the current tile and an
  "output" ``L`` tiles away in the same direction, where the intermediate tiles
  may be blocked. Only the two end tiles must be free. This is what makes
  layouts feasible when a surface detour is impossible.

A small penalty is charged per underground pair so the router prefers plain
belts unless diving actually helps.

Scope / fidelity notes (v1):

* This routes one commodity point-to-point. Merging/splitting multiple
  sources or sinks for the same item needs splitters (or side-loading) and is
  deferred; this router is the primitive the multi-net manager will call.
* Belt *directions* are emitted to point along the path. Fine-grained belt
  mechanics (side-loading, lane balancing, turning immediately after an
  underground output) are not modeled and should be validated in-game.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from factopt.data.database import Database
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Entity, Position

# Direction unit vectors in grid space (y increases downward).
_DIR_VEC: dict[int, tuple[int, int]] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}


@dataclass
class Grid:
    width: int
    height: int
    blocked: set[tuple[int, int]] = field(default_factory=set)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and (x, y) not in self.blocked

    def block_all(self, tiles) -> None:
        self.blocked.update(tiles)


@dataclass(frozen=True)
class PlacedBelt:
    name: str
    x: int
    y: int
    direction: int
    underground: bool = False
    underground_type: str | None = None  # "input" | "output" | None

    def center(self) -> Position:
        return Position(self.x + 0.5, self.y + 0.5)

    def to_entity(self) -> Entity:
        extra = {"type": self.underground_type} if self.underground_type else {}
        return Entity(
            name=self.name,
            position=self.center(),
            direction=self.direction,
            extra=extra,
        )


@dataclass
class BeltRoute:
    belts: list[PlacedBelt]
    length: int  # number of surface + underground tiles occupied
    undergrounds: int  # number of underground pairs used
    # (entrance, exit, direction) per underground pair; needed to keep other
    # routes' undergrounds from breaking the connection.
    ug_spans: list[tuple[tuple[int, int], tuple[int, int], int]] = field(default_factory=list)
    # Tiles the reconstruction placed twice (self-crossing path). A route with
    # conflicts is not physically buildable; the caller must retry.
    conflicts: list[tuple[int, int]] = field(default_factory=list)

    def tiles(self) -> set[tuple[int, int]]:
        return {(b.x, b.y) for b in self.belts}

    def ug_span_tiles(self) -> set[tuple[int, int, str]]:
        """All (x, y, axis) covered by underground spans, endpoints included."""
        out: set[tuple[int, int, str]] = set()
        for (ix, iy), (ox, oy), d in self.ug_spans:
            axis = "h" if d in (EAST, WEST) else "v"
            dx, dy = _DIR_VEC[d]
            steps = max(abs(ox - ix), abs(oy - iy))
            for k in range(steps + 1):
                out.add((ix + k * dx, iy + k * dy, axis))
        return out

    def to_entities(self) -> list[Entity]:
        return [b.to_entity() for b in self.belts]


_OPP = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}

# An action records what to place at a tile when reconstructing:
#   ("belt", (x, y), out_dir)
#   ("ug", (entrance), (exit), dir)
_Action = tuple


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def route_belt(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
    db: Database,
    belt: str = "transport-belt",
    allow_underground: bool = True,
    underground_penalty: float = 2.0,
    goal_dir: int | None = None,
    start_dir: int | None = None,
    turn_penalty: float = 0.0,
    tile_cost=None,
    ug_blocked: set | None = None,
) -> BeltRoute | None:
    """Route a directed belt from ``start`` to ``goal``; ``None`` if unreachable.

    The search is **direction-aware**: a node is (tile, travel-direction). Belts
    may turn between tiles (corners), but an underground preserves its direction
    and cannot turn at its exit (the exit ejects straight, so the next belt is one
    tile beyond it). ``goal_dir``, if given, forces the final belt's output
    direction (e.g. to feed a west-running consumer lane). ``start_dir``, if
    given, is the direction items arrive at ``start`` with (the first belt may
    not point back at the feeder). ``tile_cost``, if given, maps a tile to an
    extra non-negative cost charged whenever a belt/underground end is placed
    on it -- the hook for congestion-negotiated multi-net routing.

    ``start``/``goal`` must be free tiles.
    """
    if belt not in db.belts:
        raise ValueError(f"unknown belt {belt!r}")
    if not grid.is_free(*start):
        raise ValueError(f"start {start} is not a free tile")
    if not grid.is_free(*goal):
        raise ValueError(f"goal {goal} is not a free tile")

    belt_proto = db.belts[belt]
    belt_name = belt_proto.name
    max_dist = belt_proto.underground_max_distance if allow_underground else 0
    ug_name = belt_proto.underground_name

    if start == goal:
        out = goal_dir if goal_dir is not None else (start_dir if start_dir is not None else EAST)
        return BeltRoute(
            belts=[PlacedBelt(belt_name, start[0], start[1], out)], length=1, undergrounds=0
        )

    def placeable(t: tuple[int, int]) -> bool:
        return t == goal or grid.is_free(*t)

    def extra(t: tuple[int, int]) -> float:
        return tile_cost(t) if tile_cost is not None else 0.0

    # Node = (x, y, d): about to place an entity at (x,y), items arrive moving d.
    came: dict[tuple, tuple] = {}
    g: dict[tuple, float] = {}
    seq = [0]
    open_heap: list[tuple[float, int, tuple]] = []

    def push(node, gv, parent, action) -> None:
        if gv < g.get(node, float("inf")):
            g[node] = gv
            came[node] = (parent, action)
            seq[0] += 1
            heapq.heappush(open_heap, (gv + _manhattan(node[:2], goal), seq[0], node))

    # Seed: place a belt at ``start`` outputting each direction (fed externally).
    for od, (dx, dy) in _DIR_VEC.items():
        if start_dir is not None and od == _OPP[start_dir]:
            continue
        nxt = (start[0] + dx, start[1] + dy)
        if placeable(nxt):
            push((nxt[0], nxt[1], od), 1.0 + extra(start), None, ("belt", start, od))

    closed: set[tuple] = set()
    while open_heap:
        _f, _c, node = heapq.heappop(open_heap)
        if node in closed:
            continue
        closed.add(node)
        x, y, d = node
        tile = (x, y)

        if tile == goal:
            out = goal_dir if goal_dir is not None else d
            if out != _OPP[d]:  # a belt can't reverse on a single tile
                return _reconstruct(came, node, goal, out, belt_name)
            continue

        # Surface belt at ``tile`` (must be free) turning to any non-reverse dir.
        if grid.is_free(*tile):
            for od, (dx, dy) in _DIR_VEC.items():
                if od == _OPP[d]:
                    continue
                nxt = (x + dx, y + dy)
                if placeable(nxt):
                    step = 1.0 + extra(tile) + (turn_penalty if od != d else 0.0)
                    push((nxt[0], nxt[1], od), g[node] + step, node, ("belt", tile, od))

        # Underground continuing straight (dir d), skipping blocked tiles.
        if max_dist >= 2 and ug_name is not None and grid.is_free(*tile):
            dx, dy = _DIR_VEC[d]
            axis = "h" if d in (EAST, WEST) else "v"
            for sep in range(2, max_dist + 1):
                ex, ey = x + dx * sep, y + dy * sep
                if not grid.in_bounds(ex, ey):
                    break
                if ug_blocked is not None and any(
                    (x + dx * k, y + dy * k, axis) in ug_blocked for k in range(sep + 1)
                ):
                    break  # span would cross a foreign underground: cross-capture
                if (ex, ey) in grid.blocked:
                    continue  # exit must be free
                after = (ex + dx, ey + dy)  # exit ejects one tile further, dir d
                if placeable(after):
                    span_cost = sum(extra((x + dx * k, y + dy * k)) for k in range(1, sep))
                    push(
                        (after[0], after[1], d),
                        g[node]
                        + sep
                        + underground_penalty
                        + extra(tile)
                        + extra((ex, ey))
                        + span_cost,
                        node,
                        ("ug", tile, (ex, ey), d),
                    )

    return None


def _reconstruct(came, end_node, goal, goal_out, belt_name) -> BeltRoute:
    actions: list[_Action] = []
    node = end_node
    while node is not None:
        parent, action = came[node]
        actions.append(action)
        node = parent
    actions.reverse()

    occupied: dict[tuple[int, int], PlacedBelt] = {}
    undergrounds = 0
    ug_spans: list[tuple[tuple[int, int], tuple[int, int], int]] = []
    conflicts: list[tuple[int, int]] = []

    def place(b: PlacedBelt) -> None:
        if (b.x, b.y) in occupied:
            conflicts.append((b.x, b.y))
        occupied[(b.x, b.y)] = b

    for action in actions:
        if action[0] == "belt":
            _, (bx, by), od = action
            place(PlacedBelt(belt_name, bx, by, od))
        else:  # underground
            _, (ix, iy), (ox, oy), dd = action
            ug = belt_name  # caller passes the surface name; map below
            place(
                PlacedBelt(
                    _UG_OF.get(belt_name, ug),
                    ix,
                    iy,
                    dd,
                    underground=True,
                    underground_type="input",
                )
            )
            place(
                PlacedBelt(
                    _UG_OF.get(belt_name, ug),
                    ox,
                    oy,
                    dd,
                    underground=True,
                    underground_type="output",
                )
            )
            ug_spans.append(((ix, iy), (ox, oy), dd))
            undergrounds += 1

    # Final belt at the goal tile, output ``goal_out`` (feeds the target lane).
    place(PlacedBelt(belt_name, goal[0], goal[1], goal_out))

    belts = list(occupied.values())
    return BeltRoute(
        belts=belts,
        length=len(belts),
        undergrounds=undergrounds,
        ug_spans=ug_spans,
        conflicts=conflicts,
    )


# Surface belt name -> underground belt name (filled from the DB at call time via
# a module-level cache so _reconstruct stays simple).
_UG_OF: dict[str, str] = {
    "transport-belt": "underground-belt",
    "fast-transport-belt": "fast-underground-belt",
    "express-transport-belt": "express-underground-belt",
}
