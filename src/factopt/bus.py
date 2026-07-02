"""Assemble a complete multi-recipe block by wiring recipe bands with a bus.

Strategy (deliberately loose, correctness-first):

* One :class:`~factopt.band.Band` per recipe, stacked vertically with gaps.
* **Raws** (iron-plate, copper-plate, ...) are belted in each band straight from
  the left edge -- the block consumes them externally, so no internal routing.
* **Intermediates** flow producer -> consumer: a tap inserter lifts the item off
  the producer's output lane onto a spur, the A* router (with undergrounds)
  carries it to the consumer, and a west-running lane feeds it across the
  consumer's machines. Multiple consumers each get their own tap, so 1->N needs
  no splitters.

This is not tight, but it is general (any tree) and geometry-verified. Tightening
toward direct insertion / a packed bus is a later step.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.band import Band, build_band
from factopt.codec import encode
from factopt.data.database import Database
from factopt.model.blueprint import EAST, NORTH, SOUTH, Blueprint, Entity, Position
from factopt.ratios.solver import ProductionPlan, solve_ratios
from factopt.routing import Grid, route_belt

_ASSEMBLER = "assembling-machine-2"
_HGAP = 4  # horizontal gap between bands in a shelf (routing room)
_VGAP = 5  # vertical gap between shelves (routing room)
_TOP = 3  # top margin reserved for raw input sources
_LEFT = 3  # left margin: input lanes are fed at their west end


@dataclass
class BusResult:
    plan: ProductionPlan
    blueprint: Blueprint
    blueprint_string: str
    width: int
    height: int
    connections: list[tuple[str, str, str]] = field(default_factory=list)  # item,prod,cons
    unrouted: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.unrouted


def _offset(e: Entity, dx: int, dy: int) -> Entity:
    return Entity(
        name=e.name,
        position=Position(e.position.x + dx, e.position.y + dy),
        direction=e.direction,
        recipe=e.recipe,
        extra=dict(e.extra),
    )


def synthesize_bus(
    rate: float,
    db: Database,
    target: str,
    belt: str = "transport-belt",
    inserter: str = "fast-inserter",
    label: str | None = None,
    order: list[str] | None = None,
    hgap: int | None = None,
    vgap: int | None = None,
) -> BusResult:
    plan = solve_ratios(target, rate, db, assembler=_ASSEMBLER)
    counts = {ln.recipe: ln.machines for ln in plan.lines}

    hgap = _HGAP if hgap is None else hgap
    vgap = _VGAP if vgap is None else vgap

    # Producer recipe for each item (by primary product).
    producer_of: dict[str, str] = {}
    for r in counts:
        for prod in db.recipes[r].products:
            producer_of[prod] = r

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def depth(item: str) -> int:
        if item not in producer_of:
            return 0
        ings = db.recipes[producer_of[item]].ingredients
        return 1 + max((depth(i) for i in ings), default=0)

    # Band order: caller-supplied (e.g. the consumer-adjacency optimizer) or, by
    # default, topological depth (raws -> ... -> product).
    if order is None:
        order = sorted(counts, key=lambda r: max(depth(p) for p in db.recipes[r].products))

    # Build a band per recipe (all lanes belted; all inputs flow west, fed from
    # the east by the bus router).
    bands: dict[str, Band] = {}
    for r in order:
        bands[r] = build_band(
            r,
            counts[r],
            db,
            inserter=inserter,
            with_lane_belts=True,
            belt_items=None,
            belt_name=belt,
        )

    # Shelf-pack the bands left-to-right (new shelf when the target width is
    # exceeded) so narrow bands don't waste the width beside wide ones.
    target_w = max(b.width for b in bands.values())
    placed: dict[str, tuple[int, int]] = {}
    x, y, shelf_h = _LEFT, _TOP, 0
    for r in order:
        bw = bands[r].width
        if x > _LEFT and x + bw > _LEFT + target_w:
            y += shelf_h + vgap
            x, shelf_h = _LEFT, 0
        placed[r] = (x, y)
        x += bw + hgap
        shelf_h = max(shelf_h, bands[r].height)
    total_height = y + shelf_h

    grid_w = _LEFT + target_w + hgap + 12
    grid_h = total_height + vgap + 2

    def lane_y(recipe: str, item: str) -> int | None:
        band = bands[recipe]
        for slot, a in band.lanes.items():
            if a.item == item:
                return placed[recipe][1] + band.lane_row[slot]
        return None

    def lane_westfeed(recipe: str, item: str) -> tuple[int, int] | None:
        ly = lane_y(recipe, item)
        return None if ly is None else (placed[recipe][0] - 1, ly)

    def entity_tiles(e: Entity):
        if e.name == _ASSEMBLER:
            x0, y0 = int(e.position.x - 1.5), int(e.position.y - 1.5)
            return [(x0 + dx, y0 + dy) for dx in range(3) for dy in range(3)]
        return [(int(e.position.x - 0.5), int(e.position.y - 0.5))]

    # Static band entities + their tiles (placement is order-independent).
    band_entities: list[Entity] = []
    band_tiles: set[tuple[int, int]] = set()
    for r in order:
        bx, by = placed[r]
        for e in bands[r].entities:
            oe = _offset(e, bx, by)
            band_entities.append(oe)
            band_tiles.update(entity_tiles(oe))

    # Consumer links (raw or intermediate) + reserved west-feed goals.
    links: list[tuple[str, str | None, str, tuple[int, int]]] = []
    pre_unrouted: list[tuple[str, str, str]] = []
    goals: set[tuple[int, int]] = set()
    all_items: set[str] = set()
    for r in counts:
        all_items |= set(db.recipes[r].ingredients)
    for item in sorted(all_items):
        for cons in [r for r in counts if item in db.recipes[r].ingredients]:
            goal = lane_westfeed(cons, item)
            if goal is None:
                pre_unrouted.append((item, producer_of.get(item) or "raw", cons))
                continue
            links.append((item, producer_of.get(item), cons, goal))
            goals.add(goal)

    def _link_depth(lk) -> int:
        return max(depth(p) for p in db.recipes[lk[2]].products)

    def attempt(link_order) -> tuple[list[Entity], list, list]:
        """Route one ordering on a fresh grid; return (entities, conns, unrouted)."""
        ents = list(band_entities)
        placed_tiles = set(band_tiles)
        grid = Grid(width=grid_w, height=grid_h, blocked=set(band_tiles) | goals)

        def add(e: Entity) -> None:
            ents.append(e)
            for t in entity_tiles(e):
                grid.blocked.add(t)
                placed_tiles.add(t)

        def belt_tile(x, y, direction) -> None:
            add(Entity(name=belt, position=Position(x + 0.5, y + 0.5), direction=direction))

        def route_into(goal, spur) -> bool:
            if spur in placed_tiles or goal in placed_tiles:
                return False
            for t in (spur, goal):
                grid.blocked.discard(t)
            r = route_belt(grid, spur, goal, db, belt=belt, goal_dir=EAST)
            if r is None:
                return False
            for b in r.belts:
                if (b.x, b.y) not in placed_tiles:
                    add(b.to_entity())
            return True

        conns: list = []
        unr: list = list(pre_unrouted)
        for item, prod, cons, goal in link_order:
            if prod is not None:
                out_y = lane_y(prod, item)
                east = placed[prod][0] + bands[prod].width
                below = goal[1] >= out_y
                iy_off = 1 if below else -1
                col = east
                while col < grid_w - 2 and (
                    (col, out_y + iy_off) in placed_tiles
                    or (col, out_y + 2 * iy_off) in placed_tiles
                ):
                    col += 1
                for xx in range(east, col + 1):
                    if (xx, out_y) not in placed_tiles:
                        belt_tile(xx, out_y, EAST)
                add(
                    Entity(
                        name=inserter,
                        position=Position(col + 0.5, out_y + iy_off + 0.5),
                        direction=NORTH if below else SOUTH,
                    )
                )
                ok = route_into(goal, (col, out_y + 2 * iy_off))
            else:
                ok = False
                for dx in (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5):
                    sx = goal[0] + dx
                    if 0 <= sx < grid_w and (sx, 0) not in placed_tiles:
                        if route_into(goal, (sx, 0)):
                            ok = True
                            break
            (conns if ok else unr).append((item, prod or "raw", cons))
        return ents, conns, unr

    # Try several link orderings; keep the most complete.
    orderings = [
        sorted(links, key=lambda lk: (lk[1] is None, -_link_depth(lk))),
        sorted(links, key=lambda lk: (lk[1] is None, _link_depth(lk))),
        sorted(links, key=lambda lk: (lk[1] is not None, -_link_depth(lk))),
        sorted(links, key=lambda lk: (lk[1] is not None, _link_depth(lk))),
    ]
    best: tuple[list[Entity], list, list] | None = None
    for o in orderings:
        res_e, res_c, res_u = attempt(o)
        if best is None or len(res_u) < len(best[2]):
            best = (res_e, res_c, res_u)
        if not res_u:
            break

    # Adaptive retries: route whatever failed first (on empty channels), since
    # shared feed points (e.g. two inputs of one band) box whoever routes second.
    for _ in range(len(links)):
        if not best[2]:
            break
        failed = {(u[0], u[2]) for u in best[2]}
        adaptive = sorted(
            links,
            key=lambda lk: (0 if (lk[0], lk[2]) in failed else 1, lk[1] is None, -_link_depth(lk)),
        )
        res_e, res_c, res_u = attempt(adaptive)
        if len(res_u) < len(best[2]):
            best = (res_e, res_c, res_u)
        else:
            break
    entities, connections, unrouted = best

    label = label or f"{target}-bus-{rate:g}ps"
    bp = Blueprint(label=label, entities=entities)
    return BusResult(
        plan=plan,
        blueprint=bp,
        blueprint_string=encode(bp),
        width=grid_w,
        height=total_height,
        connections=connections,
        unrouted=unrouted,
    )
