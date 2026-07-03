"""Macro cells: the placeable/routable unit of the master problem.

A :class:`MacroCell` is a reusable layout block with a rectangular footprint,
pre-baked internal entities (in local tile coordinates, origin at the cell's
top-left tile), and :class:`PortCandidate` s -- the tiles where item flows
enter or leave the cell. Placement decides ``(x, y)`` for each cell; routing
connects ports with belts.

Cells are authored in one canonical orientation (bands: lanes flow EAST,
inserters point N/S); :func:`rotated` produces the quarter-turn variants
(entities, ports, and flow directions all rotate together), and the master
chooses an orientation per macro.

**Reversible lanes.** A belt lane that machines only *pick from* (an input
lane) can be fed from either end -- inserters pick items off it regardless of
which way the belt flows. Such a :class:`PortCandidate` carries a
:class:`PortEnd` ``reverse``: the mirror-image realization on the opposite
side (same lane, belts flipped, port on the far edge). The master picks one
end per reversible port (see ``PlacedMacro.port_choice``); the cell records
each reversible lane's belt tiles (:class:`ReversibleLane`) so entity
emission can flip just that lane's belts when the reverse end is chosen. This
lets the router approach a lane from whichever side is cheaper without
rotating the whole cell.

Coordinate conventions match the rest of factopt: integer tile coords, ``y``
grows downward (SOUTH), entity positions are tile centers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Entity, Position

Side = Literal["north", "south", "east", "west"]

_SIDE_VEC: dict[Side, tuple[int, int]] = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}

# Belt-direction unit vectors (y grows south), for pass-through lane geometry.
_DIR_VEC: dict[int, tuple[int, int]] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}


@dataclass(frozen=True)
class PortEnd:
    """One physical realization of a port: which boundary tile and side the
    flow crosses, and the belt direction it must have there."""

    side: Side
    local_position: tuple[int, int]
    flow_entry_dir: int  # model.blueprint direction the boundary belt must face


@dataclass(frozen=True)
class PortCandidate:
    """A tile on a macro's boundary where one item flow crosses it.

    ``local_position`` is the lane-end tile *inside* the footprint; the router
    connects to the adjacent tile just outside (:meth:`access offset
    <PlacedMacro.port_access_tile>`). ``flow_entry_dir`` is the belt direction
    items must have when crossing the boundary (e.g. EAST for a west-side
    input lane that flows east across the band).

    ``reverse`` (when set) is the alternative end for a **reversible** lane:
    the same lane fed from the opposite side. The master chooses which end is
    used; :attr:`primary_end` is the default (``reverse is None``) realization.
    """

    id: str
    item: str
    direction: Literal["input", "output"]
    side: Side
    local_position: tuple[int, int]
    flow_entry_dir: int  # model.blueprint direction the boundary belt must face
    max_rate_per_sec: float
    reverse: PortEnd | None = None

    @property
    def primary_end(self) -> PortEnd:
        return PortEnd(self.side, self.local_position, self.flow_entry_dir)

    @property
    def reversible(self) -> bool:
        return self.reverse is not None

    def end(self, reversed: bool) -> PortEnd:
        if reversed and self.reverse is not None:
            return self.reverse
        return self.primary_end


@dataclass(frozen=True)
class ReversibleLane:
    """The belt tiles (local coords) of one reversible input lane, plus the
    belt direction for each end. When the primary end feeds the lane its belts
    face ``forward_dir``; when the reverse end feeds it they face
    ``reverse_dir``. Keyed by the owning port's id on the cell."""

    tiles: tuple[tuple[int, int], ...]
    forward_dir: int
    reverse_dir: int


@dataclass(frozen=True)
class MacroCell:
    id: str
    kind: str
    width: int
    height: int
    entities: tuple[Entity, ...]  # local coordinates (lane belts in forward dir)
    ports: tuple[PortCandidate, ...]
    # port id -> the lane's belt tiles + per-end direction, for reversible lanes.
    reversible_lanes: dict[str, ReversibleLane] = field(default_factory=dict)

    @property
    def area(self) -> int:
        return self.width * self.height

    def port(self, port_id: str) -> PortCandidate:
        for p in self.ports:
            if p.id == port_id:
                return p
        raise KeyError(f"macro {self.id!r} has no port {port_id!r}")

    def ports_for(self, item: str, direction: str) -> list[PortCandidate]:
        return [p for p in self.ports if p.item == item and p.direction == direction]


_SIDE_CW: dict[Side, Side] = {
    "north": "east",
    "east": "south",
    "south": "west",
    "west": "north",
}


def _rotate_end(end: PortEnd, h: int) -> PortEnd:
    return PortEnd(
        side=_SIDE_CW[end.side],
        local_position=(h - 1 - end.local_position[1], end.local_position[0]),
        flow_entry_dir=(end.flow_entry_dir + 4) % 16,
    )


def rotated(cell: MacroCell, quarter_turns: int) -> MacroCell:
    """``cell`` rotated ``quarter_turns`` x 90 degrees clockwise.

    Entity centers transform as (px, py) -> (h - py, px) per turn (verified
    for 1x1, WxH machines, and 2-tile splitters); directions advance by 4 in
    Factorio's 16-way enum; port tiles, sides, flow directions, and reversible
    lane geometry rotate in lockstep so the cell stays internally consistent.
    """
    k = quarter_turns % 4
    for _ in range(k):
        h = cell.height
        entities = tuple(
            Entity(
                name=e.name,
                position=Position(h - e.position.y, e.position.x),
                direction=(e.direction + 4) % 16,
                recipe=e.recipe,
                extra=dict(e.extra),
            )
            for e in cell.entities
        )
        ports = tuple(
            PortCandidate(
                id=p.id,
                item=p.item,
                direction=p.direction,
                side=_SIDE_CW[p.side],
                local_position=(h - 1 - p.local_position[1], p.local_position[0]),
                flow_entry_dir=(p.flow_entry_dir + 4) % 16,
                max_rate_per_sec=p.max_rate_per_sec,
                reverse=_rotate_end(p.reverse, h) if p.reverse is not None else None,
            )
            for p in cell.ports
        )
        reversible_lanes = {
            pid: ReversibleLane(
                tiles=tuple((h - 1 - ty, tx) for (tx, ty) in lane.tiles),
                forward_dir=(lane.forward_dir + 4) % 16,
                reverse_dir=(lane.reverse_dir + 4) % 16,
            )
            for pid, lane in cell.reversible_lanes.items()
        }
        cell = MacroCell(
            id=cell.id,
            kind=cell.kind,
            width=cell.height,
            height=cell.width,
            entities=entities,
            ports=ports,
            reversible_lanes=reversible_lanes,
        )
    return cell


@dataclass(frozen=True)
class PlacedMacro:
    cell: MacroCell  # already rotated to ``orientation``
    x: int
    y: int
    orientation: int = 0  # quarter turns clockwise from the authored cell
    # port id -> True when the master chose that reversible port's reverse end.
    port_choice: dict[str, bool] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.cell.id

    @property
    def x2(self) -> int:
        """One past the east edge."""
        return self.x + self.cell.width

    @property
    def y2(self) -> int:
        """One past the south edge."""
        return self.y + self.cell.height

    def _reversed(self, port_id: str) -> bool:
        return bool(self.port_choice.get(port_id, False))

    def resolved_end(self, port: PortCandidate) -> PortEnd:
        """The port end (side/tile/flow dir) chosen for this placement."""
        return port.end(self._reversed(port.id))

    def _flipped_lane_tiles(self) -> dict[tuple[int, int], int]:
        """Local belt tiles whose direction must flip (reverse end chosen),
        mapped to the direction they should face."""
        out: dict[tuple[int, int], int] = {}
        for pid, lane in self.cell.reversible_lanes.items():
            if self._reversed(pid):
                for t in lane.tiles:
                    out[t] = lane.reverse_dir
        return out

    def entities(self) -> list[Entity]:
        """Internal entities translated to global coordinates, with reversed
        input lanes' belts flipped to their reverse direction."""
        flips = self._flipped_lane_tiles()
        out: list[Entity] = []
        for e in self.cell.entities:
            local = (int(e.position.x - 0.5), int(e.position.y - 0.5))
            direction = flips.get(local, e.direction)
            out.append(
                Entity(
                    name=e.name,
                    position=Position(e.position.x + self.x, e.position.y + self.y),
                    direction=direction,
                    recipe=e.recipe,
                    extra=dict(e.extra),
                )
            )
        return out

    def footprint_tiles(self) -> set[tuple[int, int]]:
        """The full w x h rectangle (used as a routing obstacle)."""
        return {
            (self.x + dx, self.y + dy)
            for dx in range((self.cell.width))
            for dy in range(self.cell.height)
        }

    def port_tile(self, port: PortCandidate) -> tuple[int, int]:
        """Global tile of the port's lane end (inside the footprint)."""
        lx, ly = self.resolved_end(port).local_position
        return (self.x + lx, self.y + ly)

    def port_access_tile(self, port: PortCandidate) -> tuple[int, int]:
        """Global tile just outside the footprint where the router connects."""
        px, py = self.port_tile(port)
        dx, dy = _SIDE_VEC[self.resolved_end(port).side]
        return (px + dx, py + dy)

    def port_flow_dir(self, port: PortCandidate) -> int:
        """The belt direction the boundary must have for the chosen end."""
        return self.resolved_end(port).flow_entry_dir

    def port_through_exit(self, port: PortCandidate) -> tuple[tuple[int, int], int] | None:
        """Where a belt fed into this port re-emerges if the lane is run
        *through* the cell (the far end of a full-span reversible input lane).

        A reversible input lane spans the whole cell in ``flow_entry_dir``, so a
        belt entering the chosen end traverses it (machines picking off) and
        exits one tile past the opposite edge, still facing ``flow_entry_dir``.
        Returns ``(exit_access_tile, exit_dir)``, or ``None`` when the port has
        no such through-lane (nothing to run through). This is what lets the
        router pass one belt by several consumers instead of splitting to each.
        """
        lane = self.cell.reversible_lanes.get(port.id)
        if lane is None:
            return None
        flow = self.resolved_end(port).flow_entry_dir
        dx, dy = _DIR_VEC[flow]
        far = max(lane.tiles, key=lambda t: t[0] * dx + t[1] * dy)
        exit_access = (self.x + far[0] + dx, self.y + far[1] + dy)
        return exit_access, flow
