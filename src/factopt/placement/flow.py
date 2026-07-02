"""Flow-coupled slot-grid placement (routing-aware, general chains).

This is the generalization of :mod:`factopt.placement.direct` from the hard-coded
green-circuit chain to an arbitrary production plan. It is the "integrated" half
of the two-stage place-and-route idea: instead of packing machines and *hoping*
the router can wire them, the placement model itself carries the inter-machine
item flow, so any layout it returns is directly-insertable by construction.

Model
-----
Machines live in a grid of ``R`` horizontal *bands* (rows of 3x3 slots) separated
by 1-tile *gap* rows, exactly the structure compact belt builds use. The solver:

* assigns a recipe (or empty) to each slot, with per-recipe machine counts fixed
  by the plan;
* for every **internal item** -- one produced by a plan recipe *and* consumed by
  another (e.g. ``copper-cable`` feeding electronic circuits, or
  ``iron-gear-wheel`` feeding red science) -- routes that item as a commodity on
  vertical *direct-insertion* edges between adjacent bands, where a gap-column's
  three inserter slots are the shared capacity;
* requires every consumer machine to be fully fed by adjacent producers, and
  minimizes the number of bands used (hence area at a fixed width).

Raw inputs and the final product are block **boundary I/O** (belted in/out on the
edges) and are intentionally *not* flow-constrained here -- that belt routing is a
separate pass, as it is for :func:`~factopt.placement.direct.place_direct`.

Scope note: internal-item transport is currently vertical (producer directly
above/below its consumer). For the single-internal-commodity chains factopt
targets today (green circuits, red science) this is exact; horizontal spread and
belt-lane fallback for multi-input interior recipes are the next extension.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from factopt.data.database import Database
from factopt.model.blueprint import NORTH, SOUTH, Blueprint, Entity, Position
from factopt.ratios.solver import ProductionPlan

_BAND_H = 3           # machine (assembler) footprint height/width in tiles
_GAP = 1              # inserter/belt channel between bands
_UNIT = 1000          # flow scale: 1 item/s == 1000 units (keeps the ILP integral)
_INSERTERS_PER_EDGE = 3  # inserter slots across one 3-wide column gap


@dataclass(frozen=True)
class FlowInserter:
    """A direct-insertion inserter placed in a gap row."""

    x: int
    y: int
    direction: int
    item: str


@dataclass
class FlowPlacement:
    plan: ProductionPlan
    cols: int
    bands: int
    width: int
    height: int
    machines: list[Entity] = field(default_factory=list)
    inserters: list[FlowInserter] = field(default_factory=list)
    status: str = ""

    @property
    def area(self) -> int:
        return self.width * self.height

    def to_blueprint(self, label: str | None = None) -> Blueprint:
        ents = list(self.machines)
        for ins in self.inserters:
            ents.append(
                Entity(
                    name="fast-inserter",
                    position=Position(ins.x + 0.5, ins.y + 0.5),
                    direction=ins.direction,
                )
            )
        return Blueprint(label=label, entities=ents)


def _internal_items(plan: ProductionPlan, db: Database) -> list[str]:
    """Items produced by one plan recipe and consumed by another (the flows the
    placement must physically satisfy). Raws (consumed only) and the final
    product (produced only) are boundary I/O and excluded."""
    produced: set[str] = set()
    consumed: set[str] = set()
    for line in plan.lines:
        recipe = db.recipes[line.recipe]
        produced.update(recipe.products)
        consumed.update(recipe.ingredients)
    return sorted(produced & consumed)


def place_flow(
    plan: ProductionPlan,
    db: Database,
    cols: int,
    inserter: str = "fast-inserter",
    max_bands: int | None = None,
    time_limit_s: float = 30.0,
    workers: int = 8,
) -> FlowPlacement:
    """Place a plan's machines in a ``cols``-wide slot grid, coupling internal
    item flow as vertical direct insertion and minimizing bands.

    Raises if no feasible layout is found (try more ``cols`` or ``max_bands``).
    """
    if cols < 1:
        raise ValueError("cols must be >= 1")

    counts = {line.recipe: line.machines for line in plan.lines}
    recipe_names = list(counts)
    n_machines = sum(counts.values())
    items = _internal_items(plan, db)

    ins_cap = round(db.inserters[inserter].rate * _UNIT)
    edge_cap = _INSERTERS_PER_EDGE * ins_cap

    # Per-machine flow is the plan's *actual* throughput (evenly shared across a
    # line's machines), NOT the machine's full nameplate capacity: machine counts
    # are rounded up, so nameplate intake exceeds demand and would make feeding
    # every consumer at full speed infeasible whenever there's rounding slack.
    def per_machine(recipe_name: str) -> float:
        line = next(ln for ln in plan.lines if ln.recipe == recipe_name)
        return line.crafts_per_sec / line.machines

    # Scaled per-machine produce/consume rates for each (recipe, internal item).
    produce = {
        (k, i): round(db.recipes[k].products.get(i, 0.0) * per_machine(k) * _UNIT)
        for k in recipe_names
        for i in items
    }
    consume = {
        (k, i): round(db.recipes[k].ingredients.get(i, 0.0) * per_machine(k) * _UNIT)
        for k in recipe_names
        for i in items
    }

    if max_bands is None:
        # A lopsided producer/consumer ratio can force a much taller packing than
        # dense width-first would suggest (a consumer must be column-sandwiched by
        # its producers), so allow generous slack up to the fully-vertical bound.
        max_bands = min(n_machines, math.ceil(n_machines / cols) + 12)
    R, C = max_bands, cols

    m = cp_model.CpModel()

    # slot[r,c,k] == 1 iff a machine crafting recipe k sits at (r, c).
    slot = {
        (r, c, k): m.new_bool_var(f"m_{r}_{c}_{k}")
        for r in range(R)
        for c in range(C)
        for k in recipe_names
    }
    for r in range(R):
        for c in range(C):
            m.add(sum(slot[r, c, k] for k in recipe_names) <= 1)
    for k in recipe_names:
        m.add(sum(slot[r, c, k] for r in range(R) for c in range(C)) == counts[k])

    def producer(i: str, r: int, c: int):
        return sum(slot[r, c, k] * (1 if produce[k, i] > 0 else 0) for k in recipe_names)

    def consumer(i: str, r: int, c: int):
        return sum(slot[r, c, k] * (1 if consume[k, i] > 0 else 0) for k in recipe_names)

    def supply(i: str, r: int, c: int):
        return sum(slot[r, c, k] * produce[k, i] for k in recipe_names)

    def demand(i: str, r: int, c: int):
        return sum(slot[r, c, k] * consume[k, i] for k in recipe_names)

    # Vertical direct-insertion flow edges between band r and r+1 at column c.
    dn = {  # producer in band r  -> consumer in band r+1
        (i, r, c): m.new_int_var(0, edge_cap, f"dn_{i}_{r}_{c}")
        for i in items
        for r in range(R - 1)
        for c in range(C)
    }
    up = {  # producer in band r+1 -> consumer in band r
        (i, r, c): m.new_int_var(0, edge_cap, f"up_{i}_{r}_{c}")
        for i in items
        for r in range(R - 1)
        for c in range(C)
    }

    for i in items:
        for c in range(C):
            for r in range(R - 1):
                m.add(dn[i, r, c] <= edge_cap * producer(i, r, c))
                m.add(dn[i, r, c] <= edge_cap * consumer(i, r + 1, c))
                m.add(up[i, r, c] <= edge_cap * producer(i, r + 1, c))
                m.add(up[i, r, c] <= edge_cap * consumer(i, r, c))

    # Per-slot flow balance for each internal item.
    for i in items:
        for r in range(R):
            for c in range(C):
                incoming = []
                outgoing = []
                if r > 0:
                    incoming.append(dn[i, r - 1, c])  # from the band above
                    outgoing.append(up[i, r - 1, c])  # to the band above
                if r < R - 1:
                    incoming.append(up[i, r, c])      # from the band below
                    outgoing.append(dn[i, r, c])      # to the band below
                m.add(sum(incoming) == demand(i, r, c))   # consumers fully fed
                m.add(sum(outgoing) <= supply(i, r, c))   # producers ship <= output

    # Each gap-column's three inserter slots are shared by all commodities.
    for r in range(R - 1):
        for c in range(C):
            m.add(
                sum(dn[i, r, c] + up[i, r, c] for i in items) <= edge_cap
            )

    # Bands are contiguous from the top; minimize how many are used.
    used = [m.new_bool_var(f"used_{r}") for r in range(R)]
    for r in range(R):
        for c in range(C):
            for k in recipe_names:
                m.add(slot[r, c, k] <= used[r])
    for r in range(R - 1):
        m.add(used[r] >= used[r + 1])
    m.minimize(sum(used))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = workers
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"flow placement infeasible/unsolved: {solver.status_name(status)} "
            f"(try more cols or max_bands)"
        )

    bands = int(sum(solver.value(used[r]) for r in range(R)))
    width = C * _BAND_H
    height = bands * _BAND_H + max(bands - 1, 0) * _GAP
    placement = FlowPlacement(
        plan=plan, cols=C, bands=bands, width=width, height=height,
        status=solver.status_name(status),
    )

    def band_y(r: int) -> int:
        return r * (_BAND_H + _GAP)

    for r in range(R):
        for c in range(C):
            for k in recipe_names:
                if solver.value(slot[r, c, k]):
                    placement.machines.append(
                        Entity(
                            name=plan.assembler,
                            position=Position(c * _BAND_H + 1.5, band_y(r) + 1.5),
                            recipe=k,
                        )
                    )

    # Emit gap inserters per edge. A down-flow inserter picks up from the band
    # above (points NORTH); an up-flow inserter picks from below (points SOUTH).
    for r in range(R - 1):
        gap_y = band_y(r) + _BAND_H
        for c in range(C):
            slot_idx = 0
            for i in items:
                for units, direction in (
                    (int(solver.value(dn[i, r, c])), NORTH),
                    (int(solver.value(up[i, r, c])), SOUTH),
                ):
                    if units <= 0:
                        continue
                    n = math.ceil(units / ins_cap)
                    for _ in range(n):
                        if slot_idx >= _INSERTERS_PER_EDGE:
                            raise RuntimeError(
                                "gap column over-subscribed with inserters "
                                "(multi-commodity packing not yet supported)"
                            )
                        placement.inserters.append(
                            FlowInserter(
                                x=c * _BAND_H + slot_idx,
                                y=gap_y,
                                direction=direction,
                                item=i,
                            )
                        )
                        slot_idx += 1

    return placement
