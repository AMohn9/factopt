"""Lightweight, solver-facing blueprint DTO.

These dataclasses are the in-memory representation the placement/routing stages
build and manipulate with plain integer-tile math. Serialization to and from
Factorio blueprint strings is handled entirely by Draftsman in
:mod:`factopt.codec` -- this module deliberately no longer knows about the wire
format, version stamps, or entity numbering.

Directions use Factorio's 2.0 16-way enum (N=0, E=4, S=8, W=12), matching
Draftsman's internal representation so the codec needs no conversion. Only the
cardinal subset is used by belts/inserters/machines.
"""

from __future__ import annotations

from dataclasses import dataclass, field

NORTH = 0
EAST = 4
SOUTH = 8
WEST = 12


@dataclass(frozen=True)
class Position:
    """Tile position of an entity's center. Factorio centers entities, so
    odd-footprint entities sit on half-tile offsets (a 3x3 assembler centered at
    x.5, y.5)."""

    x: float
    y: float


@dataclass
class Entity:
    """A single placed entity.

    ``extra`` carries any fields the DTO doesn't model first-class (e.g. an
    underground belt's ``type``, or a decoded blueprint's ``control_behavior``).
    """

    name: str
    position: Position
    direction: int = NORTH
    recipe: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class Blueprint:
    entities: list[Entity] = field(default_factory=list)
    label: str | None = None
