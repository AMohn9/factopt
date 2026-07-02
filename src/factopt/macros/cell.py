"""Macro cells: the placeable/routable unit of the master problem.

A :class:`MacroCell` is a reusable layout block with a rectangular footprint,
pre-baked internal entities (in local tile coordinates, origin at the cell's
top-left tile), and :class:`PortCandidate` s -- the tiles where item flows
enter or leave the cell. Placement decides ``(x, y)`` for each cell; routing
connects ports with belts.

Orientation is deliberately not modeled yet: the first macro library (recipe
bands) is direction-baked (lanes flow EAST, inserters point N/S), so every
macro is placed axis-aligned as authored. The master reserves an orientation
hook for later.

Coordinate conventions match the rest of factopt: integer tile coords, ``y``
grows downward (SOUTH), entity positions are tile centers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from factopt.model.blueprint import Entity, Position

Side = Literal["north", "south", "east", "west"]

_SIDE_VEC: dict[Side, tuple[int, int]] = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
}


@dataclass(frozen=True)
class PortCandidate:
    """A tile on a macro's boundary where one item flow crosses it.

    ``local_position`` is the lane-end tile *inside* the footprint; the router
    connects to the adjacent tile just outside (:meth:`access offset
    <PlacedMacro.port_access_tile>`). ``flow_entry_dir`` is the belt direction
    items must have when crossing the boundary (e.g. EAST for a west-side
    input lane that flows east across the band).
    """

    id: str
    item: str
    direction: Literal["input", "output"]
    side: Side
    local_position: tuple[int, int]
    flow_entry_dir: int  # model.blueprint direction the boundary belt must face
    max_rate_per_sec: float


@dataclass(frozen=True)
class MacroCell:
    id: str
    kind: str
    width: int
    height: int
    entities: tuple[Entity, ...]  # local coordinates
    ports: tuple[PortCandidate, ...]

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


@dataclass(frozen=True)
class PlacedMacro:
    cell: MacroCell
    x: int
    y: int

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

    def entities(self) -> list[Entity]:
        """Internal entities translated to global coordinates."""
        return [
            Entity(
                name=e.name,
                position=Position(e.position.x + self.x, e.position.y + self.y),
                direction=e.direction,
                recipe=e.recipe,
                extra=dict(e.extra),
            )
            for e in self.cell.entities
        ]

    def footprint_tiles(self) -> set[tuple[int, int]]:
        """The full w x h rectangle (used as a routing obstacle)."""
        return {
            (self.x + dx, self.y + dy)
            for dx in range((self.cell.width))
            for dy in range(self.cell.height)
        }

    def port_tile(self, port: PortCandidate) -> tuple[int, int]:
        """Global tile of the port's lane end (inside the footprint)."""
        return (self.x + port.local_position[0], self.y + port.local_position[1])

    def port_access_tile(self, port: PortCandidate) -> tuple[int, int]:
        """Global tile just outside the footprint where the router connects."""
        px, py = self.port_tile(port)
        dx, dy = _SIDE_VEC[port.side]
        return (px + dx, py + dy)
