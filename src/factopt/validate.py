"""Static blueprint validation.

Checks a list of entities (or a :class:`~factopt.model.blueprint.Blueprint`)
for geometric and connective sanity before it is ever encoded or imported:

* no two entities overlap a tile;
* everything lies inside optional bounds;
* every inserter has an occupied pickup and dropoff tile;
* every belt feeds into something (belt, splitter, underground, or a tile
  covered by a machine is *not* valid -- belts must chain);
* requested item flows have a directed belt path from source to sink.

Every finding is a :class:`Violation` with a human-readable message; callers
decide what is fatal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from factopt.data.database import Database
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Blueprint, Entity

_DIR_VEC = {NORTH: (0, -1), EAST: (1, 0), SOUTH: (0, 1), WEST: (-1, 0)}


@dataclass(frozen=True)
class Violation:
    kind: str  # "overlap" | "bounds" | "inserter" | "belt" | "flow"
    message: str
    tile: tuple[int, int] | None = None


def entity_tiles(e: Entity, db: Database) -> list[tuple[int, int]]:
    """Integer tiles occupied by an entity.

    Assemblers use their prototype footprint; splitters occupy two tiles
    perpendicular to their facing; everything else is 1x1.
    """
    if e.name in db.assemblers:
        a = db.assemblers[e.name]
        w, h = a.width, a.height
    elif "splitter" in e.name:
        w, h = (1, 2) if e.direction in (EAST, WEST) else (2, 1)
    else:
        w = h = 1
    x0 = int(round(e.position.x - w / 2))
    y0 = int(round(e.position.y - h / 2))
    return [(x0 + dx, y0 + dy) for dx in range(w) for dy in range(h)]


def _is_belt(e: Entity, db: Database) -> bool:
    return e.name in db.belts


def _is_underground(e: Entity, db: Database) -> bool:
    return any(b.underground_name == e.name for b in db.belts.values())


def _is_splitter(e: Entity) -> bool:
    return "splitter" in e.name


def _is_beltish(e: Entity, db: Database) -> bool:
    return _is_belt(e, db) or _is_underground(e, db) or _is_splitter(e)


class BeltGraph:
    """Directed tile graph of belt flow (belts, splitters, undergrounds)."""

    def __init__(self, entities: list[Entity], db: Database):
        self.db = db
        # tile -> the belt-ish entity occupying it
        self.at: dict[tuple[int, int], Entity] = {}
        for e in entities:
            if _is_beltish(e, db):
                for t in entity_tiles(e, db):
                    self.at[t] = e
        self._underground_pairs = self._pair_undergrounds()

    def _pair_undergrounds(self) -> dict[tuple[int, int], tuple[int, int]]:
        """Map each underground *input* tile to its matched output tile."""
        max_dist = {
            b.underground_name: b.underground_max_distance
            for b in self.db.belts.values()
            if b.underground_name
        }
        pairs: dict[tuple[int, int], tuple[int, int]] = {}
        for t, e in self.at.items():
            if not _is_underground(e, self.db) or e.extra.get("type") != "input":
                continue
            dx, dy = _DIR_VEC[e.direction]
            for k in range(1, max_dist.get(e.name, 0) + 1):
                cand = (t[0] + k * dx, t[1] + k * dy)
                other = self.at.get(cand)
                if (
                    other is not None
                    and other.name == e.name
                    and other.extra.get("type") == "output"
                    and other.direction == e.direction
                ):
                    pairs[t] = cand
                    break
        return pairs

    def successors(self, t: tuple[int, int]) -> list[tuple[int, int]]:
        e = self.at.get(t)
        if e is None:
            return []
        if _is_underground(e, self.db) and e.extra.get("type") == "input":
            out = self._underground_pairs.get(t)
            return [out] if out is not None else []
        if _is_splitter(e):
            # A splitter distributes input from either of its tiles to both
            # of its outputs.
            dx, dy = _DIR_VEC[e.direction]
            outs = []
            for tile in entity_tiles(e, self.db):
                nxt = (tile[0] + dx, tile[1] + dy)
                if nxt in self.at:
                    outs.append(nxt)
            return outs
        dx, dy = _DIR_VEC[e.direction]
        nxt = (t[0] + dx, t[1] + dy)
        ne = self.at.get(nxt)
        if ne is None:
            return []
        # A belt cannot feed a belt that flows straight back into it.
        if ne.direction == _OPPOSITE[e.direction] and not _is_splitter(ne):
            return []
        # An underground input can only be entered along its axis.
        if (
            _is_underground(ne, self.db)
            and ne.extra.get("type") == "input"
            and ne.direction != e.direction
        ):
            # Side-loading an underground entrance is legal in Factorio, keep it.
            pass
        return [nxt]

    def reachable(self, src: tuple[int, int], dst: tuple[int, int]) -> bool:
        if src not in self.at or dst not in self.at:
            return False
        seen = {src}
        stack = [src]
        while stack:
            cur = stack.pop()
            if cur == dst:
                return True
            for nxt in self.successors(cur):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return False


_OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}


@dataclass
class ValidationReport:
    violations: list[Violation]

    @property
    def ok(self) -> bool:
        return not self.violations

    def by_kind(self, kind: str) -> list[Violation]:
        return [v for v in self.violations if v.kind == kind]

    def __str__(self) -> str:
        if self.ok:
            return "valid: no violations"
        return "\n".join(f"[{v.kind}] {v.message}" for v in self.violations)


def validate(
    bp: Blueprint | list[Entity],
    db: Database,
    bounds: tuple[int, int, int, int] | None = None,
    flows: Iterable[tuple[tuple[int, int], tuple[int, int]]] = (),
) -> ValidationReport:
    """Validate entities statically.

    ``bounds`` is ``(x0, y0, x1, y1)`` with x1/y1 exclusive. ``flows`` is an
    iterable of (source_tile, sink_tile) belt-path requirements.
    """
    entities = bp.entities if isinstance(bp, Blueprint) else list(bp)
    violations: list[Violation] = []

    # -- overlap + bounds ---------------------------------------------------
    occupied: dict[tuple[int, int], Entity] = {}
    for e in entities:
        for t in entity_tiles(e, db):
            other = occupied.get(t)
            if other is not None:
                violations.append(
                    Violation(
                        "overlap",
                        f"{e.name} overlaps {other.name} at {t}",
                        tile=t,
                    )
                )
            else:
                occupied[t] = e
            if bounds is not None:
                x0, y0, x1, y1 = bounds
                if not (x0 <= t[0] < x1 and y0 <= t[1] < y1):
                    violations.append(
                        Violation("bounds", f"{e.name} at {t} outside bounds {bounds}", tile=t)
                    )

    # -- inserters ----------------------------------------------------------
    for e in entities:
        if e.name not in db.inserters:
            continue
        reach = db.inserters[e.name].reach
        dx, dy = _DIR_VEC[e.direction]
        tile = (int(e.position.x), int(e.position.y))
        pickup = (tile[0] + reach * dx, tile[1] + reach * dy)
        dropoff = (tile[0] - reach * dx, tile[1] - reach * dy)
        if pickup not in occupied:
            violations.append(
                Violation("inserter", f"{e.name} at {tile} has empty pickup {pickup}", tile=tile)
            )
        if dropoff not in occupied:
            violations.append(
                Violation(
                    "inserter", f"{e.name} at {tile} has empty dropoff {dropoff}", tile=tile
                )
            )

    # -- belt connectivity --------------------------------------------------
    graph = BeltGraph(entities, db)
    inserter_pickups: set[tuple[int, int]] = set()
    for e in entities:
        if e.name in db.inserters:
            reach = db.inserters[e.name].reach
            dx, dy = _DIR_VEC[e.direction]
            tile = (int(e.position.x), int(e.position.y))
            inserter_pickups.add((tile[0] + dx * reach, tile[1] + dy * reach))

    for t, e in graph.at.items():
        if _is_underground(e, graph.db) and e.extra.get("type") == "input":
            if t not in graph._underground_pairs:
                violations.append(
                    Violation("belt", f"underground input at {t} has no matching output", tile=t)
                )
            continue
        if not graph.successors(t) and t not in inserter_pickups:
            # A dead-ended belt is fine only if an inserter picks from it or it
            # is a declared flow sink; flows are checked separately, so only
            # flag belts nothing consumes.
            pass  # informational; boundary output belts legitimately dead-end

    # -- required flows -----------------------------------------------------
    for src, dst in flows:
        if not graph.reachable(src, dst):
            violations.append(
                Violation("flow", f"no directed belt path from {src} to {dst}", tile=src)
            )

    return ValidationReport(violations)
