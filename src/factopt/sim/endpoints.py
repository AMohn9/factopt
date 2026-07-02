"""Find a block's boundary belt endpoints (to help build sim sources/sinks).

A transport belt carries items in its ``direction``. The tile *behind* it (the
upstream neighbour) is where items arrive; if that tile is empty, the belt is an
**input endpoint** on the block boundary. Symmetrically, if the tile *ahead*
(downstream) is empty, it's an **output endpoint**. These are the tiles a sim
harness feeds from infinity chests / drains into sinks.

This only reports geometry -- which belt tiles are open-ended and in which
direction. It does not know *which item* a belt carries (a blueprint doesn't
encode that), so the caller labels endpoints with items when building
:class:`~factopt.sim.harness.Source` entries.
"""

from __future__ import annotations

from dataclasses import dataclass

from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Blueprint

_BELT_NAMES = ("transport-belt", "fast-transport-belt", "express-transport-belt",
               "turbo-transport-belt")
_DIR_VEC: dict[int, tuple[int, int]] = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}


@dataclass(frozen=True)
class Endpoint:
    x: int
    y: int
    direction: int
    kind: str  # "input" | "output"


def _tile(x: float, y: float) -> tuple[int, int]:
    return (int(x - 0.5), int(y - 0.5))


def _occupied_tiles(bp: Blueprint) -> set[tuple[int, int]]:
    tiles: set[tuple[int, int]] = set()
    for e in bp.entities:
        if "assembling-machine" in e.name or e.name.startswith("assembling"):
            x0, y0 = int(e.position.x - 1.5), int(e.position.y - 1.5)
            for dx in range(3):
                for dy in range(3):
                    tiles.add((x0 + dx, y0 + dy))
        else:
            tiles.add(_tile(e.position.x, e.position.y))
    return tiles


def belt_endpoints(bp: Blueprint) -> list[Endpoint]:
    """Return open-ended belt tiles on the block boundary (inputs and outputs)."""
    occupied = _occupied_tiles(bp)
    out: list[Endpoint] = []
    for e in bp.entities:
        if not any(name in e.name for name in _BELT_NAMES):
            continue
        vec = _DIR_VEC.get(e.direction)
        if vec is None:
            continue
        x, y = _tile(e.position.x, e.position.y)
        upstream = (x - vec[0], y - vec[1])
        downstream = (x + vec[0], y + vec[1])
        if upstream not in occupied:
            out.append(Endpoint(x=x, y=y, direction=e.direction, kind="input"))
        if downstream not in occupied:
            out.append(Endpoint(x=x, y=y, direction=e.direction, kind="output"))
    return out
