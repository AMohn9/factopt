"""Boundary-aware dense placement: a direct-insertion machine row with I/O.

:mod:`factopt.placement.flow` proved the density trick -- couple internal item
flow as machine-to-machine **direct insertion** instead of belts -- but it packs
machines into a *vertical* band grid and leaves raw-in / product-out to a later
pass. That leaves interior bands with no edge to belt their raws in or product
out, so a multi-band pack is never a standalone importable block.

This module takes the complementary, self-contained approach: lay the whole
group out as **one horizontal machine row** and move the internal item sideways
between neighbouring machines through 1-wide inserter columns in the gaps. Every
machine then keeps a clear top and bottom edge, so the block's boundary items
ride straight full-width belt lanes (raws enter west, product leaves east) --
exactly the verified geometry of :mod:`factopt.mvp`, minus the shared
intermediate lane the direct insertion replaces.

    copper-plate lane   ─────────────────────────────   (west in)
       [ top inserters ]  cable machines pick plate
    [ C | e | C | e | C | e ... ]  machine row, direct insertion in the
       [ bot inserters ]  gaps (│) between a cable machine and its EC neighbour
    electronic-circuit lane ─────────────────────────   (east out)
    iron-plate lane     ─────────────────────────────   (west in)

Scope: a 2-level single-internal-item chain (product = one intermediate + raws;
intermediate = raws), e.g. green circuits. This is the placeable primitive the
fusion planner wraps as a :class:`~factopt.macros.cell.MacroCell`; multi-row
packing (denser at high rate, at the cost of interior I/O routing) is a later
milestone. Inserter facing follows the in-game-verified pickup convention
(``direction`` points at the tile picked up from).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from factopt.data.database import Database
from factopt.model.blueprint import EAST, NORTH, SOUTH, WEST, Blueprint, Entity, Position
from factopt.ratios.solver import ItemFlow, ProductionPlan

_BAND_H = 3          # assembler footprint (3x3 in vanilla)
_UNIT = 1000         # flow scale: 1 item/s == 1000 units (keeps the ILP integral)
_INSERTERS_PER_GAP = 3  # inserter slots in one 3-tall gap column

# Row offsets within the block (top to bottom).
_Y_TOP_LANE = 0      # producer raw lane (e.g. copper-plate), flows east
_Y_TOP_INS = 1       # producers pick their raw off the top lane
_Y_MACHINE = 2       # machine row occupies rows 2..4
_Y_BOT_INS = 5       # consumers drop product / pick their raw (long-handed)
_Y_PROD_LANE = 6     # product lane (e.g. electronic-circuit), flows east
_Y_RAW2_LANE = 7     # consumer raw lane (e.g. iron-plate), flows east
_HEIGHT = 8


@dataclass(frozen=True)
class DenseBoundaryPort:
    """A block-boundary belt tile where a raw enters (west) or the product
    leaves (east). ``local_position`` is the lane-end tile inside the footprint;
    ``flow_dir`` is the belt direction across the boundary (always EAST here)."""

    item: str
    direction: str          # "input" | "output"
    side: str               # "west" | "east"
    local_position: tuple[int, int]
    flow_dir: int


@dataclass
class DensePlacement:
    plan: ProductionPlan
    internal_item: str
    producer_recipe: str
    consumer_recipe: str
    belt: str
    width: int
    height: int
    machines: list[Entity] = field(default_factory=list)
    belts: list[Entity] = field(default_factory=list)
    inserters: list[Entity] = field(default_factory=list)
    ports: list[DenseBoundaryPort] = field(default_factory=list)
    status: str = ""

    @property
    def area(self) -> int:
        return self.width * self.height

    def entities(self) -> list[Entity]:
        return list(self.machines) + list(self.belts) + list(self.inserters)

    def to_blueprint(self, label: str | None = None) -> Blueprint:
        return Blueprint(label=label, entities=self.entities())


def _roles(plan: ProductionPlan, db: Database) -> tuple[str, str, str]:
    """Return (internal_item, producer_recipe, consumer_recipe) for a single-
    interior 2-level chain. Raises if the plan is not that shape."""
    produced: dict[str, str] = {}
    consumed: dict[str, list[str]] = {}
    for line in plan.lines:
        recipe = db.recipes[line.recipe]
        for item in recipe.products:
            produced[item] = line.recipe
        for item in recipe.ingredients:
            consumed.setdefault(item, []).append(line.recipe)
    internal = sorted(set(produced) & set(consumed))
    if len(internal) != 1:
        raise ValueError(
            f"dense row handles a single interior item; got {internal} "
            "(multi-lane / multi-row layouts are a later milestone)"
        )
    item = internal[0]
    consumers = consumed[item]
    if len(consumers) != 1:
        raise ValueError(f"interior item {item!r} has multiple consumers {consumers}")
    return item, produced[item], consumers[0]


def subplan_for_group(
    plan: ProductionPlan, db: Database, group: set[str]
) -> ProductionPlan:
    """Restrict ``plan`` to the recipes in ``group`` as a standalone plan.

    The group's *external product* (produced inside the group but not consumed
    there) becomes the sub-plan target; flows are recomputed over just the
    group's crafts so :func:`place_dense_row` can size lanes and per-machine
    rates from a self-consistent plan.
    """
    lines = [ln for ln in plan.lines if ln.recipe in group]
    crafts = {ln.recipe: ln.crafts_per_sec for ln in lines}
    produced: dict[str, float] = {}
    consumed: dict[str, float] = {}
    for ln in lines:
        r = db.recipes[ln.recipe]
        for it, c in r.products.items():
            produced[it] = produced.get(it, 0.0) + c * crafts[ln.recipe]
        for it, c in r.ingredients.items():
            consumed[it] = consumed.get(it, 0.0) + c * crafts[ln.recipe]
    items = set(produced) | set(consumed)
    flows = {
        it: ItemFlow(
            item=it,
            produced_per_sec=produced.get(it, 0.0),
            consumed_per_sec=consumed.get(it, 0.0),
            is_raw=db.is_raw(it),
        )
        for it in items
    }
    externals = sorted(
        it
        for it in produced
        if produced[it] - consumed.get(it, 0.0) > 1e-9 and not db.is_raw(it)
    )
    target = externals[0] if externals else next(iter(produced))
    rate = produced[target] - consumed.get(target, 0.0)
    return ProductionPlan(
        target=target, rate=rate, assembler=plan.assembler, lines=lines, flows=flows
    )


def plan_fusions(plan: ProductionPlan, db: Database) -> list[set[str]]:
    """Pick non-overlapping producer/consumer pairs to pack as dense
    direct-insertion cells.

    A pair ``{P, C}`` qualifies when some internal item has **exactly one**
    producer recipe ``P`` and **exactly one** consumer recipe ``C``, and the
    resulting 2-recipe sub-plan is a shape :func:`place_dense_row` can build
    (validated by trying). For green science this yields exactly the
    copper-cable -> electronic-circuit pair; gears (two consumers) stay belted.
    """
    produced: dict[str, list[str]] = {}
    consumed: dict[str, list[str]] = {}
    for ln in plan.lines:
        for it in db.recipes[ln.recipe].products:
            produced.setdefault(it, []).append(ln.recipe)
        for it in db.recipes[ln.recipe].ingredients:
            consumed.setdefault(it, []).append(ln.recipe)

    groups: list[set[str]] = []
    used: set[str] = set()
    for item in sorted(set(produced) & set(consumed)):
        prods, cons = produced[item], consumed[item]
        if len(prods) != 1 or len(cons) != 1:
            continue
        p, c = prods[0], cons[0]
        if p == c or p in used or c in used:
            continue
        group = {p, c}
        try:
            place_dense_row(subplan_for_group(plan, db, group), db)
        except (ValueError, RuntimeError):
            continue
        groups.append(group)
        used |= group
    return groups


def fusable_chain(plan: ProductionPlan, db: Database) -> tuple[str, str, str] | None:
    """If ``plan`` is a whole 2-level single-internal-item chain that
    :func:`place_dense_row` can pack (e.g. green circuits), return
    ``(internal_item, producer_recipe, consumer_recipe)``; else ``None``.

    Conservative on purpose: the consumer's product must be the plan target (so
    the dense cell's only external output feeds the block output), and the chain
    must have exactly one internal item with a single consumer. Deeper trees
    (partial sub-chain fusion) are a later milestone.
    """
    try:
        item, prod_r, cons_r = _roles(plan, db)
    except ValueError:
        return None
    cons_products = list(db.recipes[cons_r].products)
    if len(cons_products) != 1 or cons_products[0] != plan.target:
        return None
    return item, prod_r, cons_r


def _select_belt(flow: float, db: Database, belt: str | None) -> str:
    tiers = [belt] if belt else sorted(db.belts, key=lambda b: db.belts[b].throughput)
    for name in tiers:
        if name not in db.belts:
            raise ValueError(f"unknown belt {name!r}")
        if db.belts[name].throughput >= flow - 1e-9:
            return name
    raise ValueError(
        f"a boundary flow of {flow:g}/s exceeds a single {tiers[-1]} lane; "
        "multi-lane boundary I/O is not supported by the dense row yet"
    )


def _order_row(
    n_prod: int,
    n_cons: int,
    prod_out: int,
    cons_in: int,
    gap_cap: int,
    time_limit_s: float,
    workers: int,
) -> tuple[list[str], dict[int, int], dict[int, int]]:
    """Order the ``n_prod + n_cons`` machines in a single row so every consumer
    is fully fed by its (left/right) producer neighbours via direct insertion.

    Returns ``(kinds, flow_right, flow_left)`` where ``kinds[i]`` is ``"P"`` or
    ``"C"`` and ``flow_right[i]`` / ``flow_left[i]`` are the scaled internal-item
    units crossing the gap between slots ``i`` and ``i+1`` (rightward / leftward).
    Raises if no fully-fed ordering exists in a single row.
    """
    n = n_prod + n_cons
    m = cp_model.CpModel()

    is_p = [m.new_bool_var(f"p_{i}") for i in range(n)]  # producer at slot i
    m.add(sum(is_p) == n_prod)  # the rest are consumers (row is fully packed)

    # Directed internal-item flow across each interior gap.
    fr = {i: m.new_int_var(0, gap_cap, f"fr_{i}") for i in range(n - 1)}  # i -> i+1
    fl = {i: m.new_int_var(0, gap_cap, f"fl_{i}") for i in range(n - 1)}  # i+1 -> i
    for i in range(n - 1):
        # A rightward edge is only a producer(i) -> consumer(i+1) transfer.
        m.add(fr[i] <= gap_cap).only_enforce_if(is_p[i])
        m.add(fr[i] == 0).only_enforce_if(is_p[i].negated())
        m.add(fr[i] == 0).only_enforce_if(is_p[i + 1])  # sink must be a consumer
        # A leftward edge is producer(i+1) -> consumer(i).
        m.add(fl[i] == 0).only_enforce_if(is_p[i + 1].negated())
        m.add(fl[i] == 0).only_enforce_if(is_p[i])      # sink must be a consumer
        # Each 3-tall gap column shares a single inserter budget.
        m.add(fr[i] + fl[i] <= gap_cap)

    for i in range(n):
        into = []
        outof = []
        if i > 0:
            into.append(fr[i - 1])   # from the left neighbour
            outof.append(fl[i - 1])  # to the left neighbour
        if i < n - 1:
            into.append(fl[i])       # from the right neighbour
            outof.append(fr[i])      # to the right neighbour
        # Consumers must be fully fed; producers ship at most their output.
        m.add(sum(into) == cons_in).only_enforce_if(is_p[i].negated())
        m.add(sum(into) == 0).only_enforce_if(is_p[i])
        m.add(sum(outof) <= prod_out).only_enforce_if(is_p[i])
        m.add(sum(outof) == 0).only_enforce_if(is_p[i].negated())

    # Prefer short transfers (keeps inserter columns lightly loaded).
    m.minimize(sum(fr.values()) + sum(fl.values()))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = workers
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            "no single-row direct-insertion ordering fully feeds every consumer "
            f"({solver.status_name(status)}); this chain needs multi-row packing"
        )

    kinds = ["P" if solver.value(is_p[i]) else "C" for i in range(n)]
    flow_right = {i: int(solver.value(fr[i])) for i in range(n - 1)}
    flow_left = {i: int(solver.value(fl[i])) for i in range(n - 1)}
    return kinds, flow_right, flow_left


def place_dense_row(
    plan: ProductionPlan,
    db: Database,
    inserter: str = "fast-inserter",
    long_inserter: str = "long-handed-inserter",
    belt: str | None = None,
    time_limit_s: float = 20.0,
    workers: int = 8,
) -> DensePlacement:
    """Place a 2-level single-internal-item chain as one direct-insertion row
    with full boundary I/O (raws in west, product out east).

    The internal item never touches a belt: producer machines inject it straight
    into their consumer neighbours through inserter columns in the gaps. Raws and
    the product ride straight full-width belt lanes above and below the row.
    """
    item, prod_recipe, cons_recipe = _roles(plan, db)
    counts = {ln.recipe: ln.machines for ln in plan.lines}
    n_prod, n_cons = counts[prod_recipe], counts[cons_recipe]

    prod = db.recipes[prod_recipe]
    cons = db.recipes[cons_recipe]
    ins_rate = db.inserters[inserter].rate
    long_rate = db.inserters[long_inserter].rate

    # Per-machine crafts/s is the plan's *actual* throughput (evenly shared over a
    # line's machines), NOT the machine's nameplate: counts are rounded up, so
    # nameplate intake exceeds demand and would make the flow balance infeasible
    # whenever there is rounding slack (see factopt.placement.flow).
    def per_machine(recipe_name: str) -> float:
        line = next(ln for ln in plan.lines if ln.recipe == recipe_name)
        return line.crafts_per_sec / line.machines

    pmc_prod = per_machine(prod_recipe)
    pmc_cons = per_machine(cons_recipe)

    # Per-machine internal-item throughput (scaled), and the gap inserter budget.
    prod_out = round(prod.products[item] * pmc_prod * _UNIT)
    cons_in = round(cons.ingredients[item] * pmc_cons * _UNIT)
    ins_cap = round(ins_rate * _UNIT)
    gap_cap = _INSERTERS_PER_GAP * ins_cap

    kinds, flow_right, flow_left = _order_row(
        n_prod, n_cons, prod_out, cons_in, gap_cap, time_limit_s, workers
    )
    n = len(kinds)

    # Boundary items: the producer's raws (fed from the top lane) and the
    # consumer's raws besides the internal item (fed from the bottom raw lane),
    # plus the product (dropped onto the product lane). This milestone supports
    # one raw per machine side, matching the verified 2-level chain shape.
    prod_raws = [i for i in prod.ingredients if db.is_raw(i)]
    cons_raws = [i for i in cons.ingredients if db.is_raw(i) and i != item]
    products = [i for i in cons.products]
    # Both machines' only non-raw input must be the direct-inserted item; any
    # other intermediate (e.g. the inserter's gear) has no lane here and would be
    # silently starved, so such a group is not a valid dense row.
    prod_nonraw = [i for i in prod.ingredients if not db.is_raw(i)]
    cons_nonraw = [i for i in cons.ingredients if not db.is_raw(i) and i != item]
    if prod_nonraw or cons_nonraw:
        raise ValueError(
            "dense row requires the only non-raw input of both machines to be "
            f"the direct-inserted item {item!r}; extra intermediates "
            f"{sorted(set(prod_nonraw) | set(cons_nonraw))} would be unfed"
        )
    if len(prod_raws) != 1 or len(cons_raws) != 1 or len(products) != 1:
        raise ValueError(
            "dense row supports one raw per machine side and one product; got "
            f"producer raws={prod_raws}, consumer raws={cons_raws}, products={products}"
        )
    top_raw, bot_raw, product = prod_raws[0], cons_raws[0], products[0]

    max_flow = max(
        max(f.produced_per_sec, f.consumed_per_sec)
        for it, f in plan.flows.items()
        if it in (top_raw, bot_raw, product)
    )
    belt_name = _select_belt(max_flow, db, belt)

    def n_ins(count: float, pmc: float, rate_: float) -> int:
        return max(1, math.ceil(count * pmc / rate_ - 1e-9))

    n_top_in = n_ins(prod.ingredients[top_raw], pmc_prod, ins_rate)     # raw -> producer
    n_prod_out = n_ins(cons.products[product], pmc_cons, ins_rate)      # product -> lane
    n_bot_in = n_ins(cons.ingredients[bot_raw], pmc_cons, long_rate)    # raw -> consumer (long)
    if n_top_in > _INSERTERS_PER_GAP or n_prod_out + n_bot_in > _INSERTERS_PER_GAP:
        raise ValueError(
            "a machine side needs more than 3 boundary inserters at this rate; "
            "tile into lower-rate sub-blocks (not supported by the dense row yet)"
        )

    # Column geometry: machine i occupies x in [4i, 4i+2]; gap column at 4i+3.
    def machine_x(i: int) -> int:
        return 4 * i

    def gap_x(i: int) -> int:
        return 4 * i + 3

    width = 4 * n - 1  # last machine ends at 4(n-1)+2; no trailing gap
    placement = DensePlacement(
        plan=plan,
        internal_item=item,
        producer_recipe=prod_recipe,
        consumer_recipe=cons_recipe,
        belt=belt_name,
        width=width,
        height=_HEIGHT,
        status="OPTIMAL",
    )

    def belt_tile(x: int, y: int) -> None:
        placement.belts.append(
            Entity(name=belt_name, position=Position(x + 0.5, y + 0.5), direction=EAST)
        )

    def ins(x: int, y: int, pickup: int, name: str = inserter) -> None:
        placement.inserters.append(
            Entity(name=name, position=Position(x + 0.5, y + 0.5), direction=pickup)
        )

    # Full-width boundary lanes (all flow east).
    for x in range(width):
        belt_tile(x, _Y_TOP_LANE)   # producer raw in (west)
        belt_tile(x, _Y_PROD_LANE)  # product out (east)
        belt_tile(x, _Y_RAW2_LANE)  # consumer raw in (west)

    # Machines + their boundary inserters.
    for i, kind in enumerate(kinds):
        mx = machine_x(i)
        recipe = prod_recipe if kind == "P" else cons_recipe
        placement.machines.append(
            Entity(
                name=plan.assembler,
                position=Position(mx + 1.5, _Y_MACHINE + 1.5),
                recipe=recipe,
            )
        )
        if kind == "P":
            # Producer: pick its raw off the top lane (inserter faces NORTH -> the
            # lane above, drops into the machine below).
            for k in range(n_top_in):
                ins(mx + k, _Y_TOP_INS, NORTH)
        else:
            # Consumer: product out (normal, drops onto the product lane below) and
            # its raw in (long-handed, reaching the raw lane past the product lane).
            slot = 0
            for _ in range(n_prod_out):
                ins(mx + slot, _Y_BOT_INS, NORTH)   # pick machine, drop product lane
                slot += 1
            for _ in range(n_bot_in):
                ins(mx + slot, _Y_BOT_INS, SOUTH, name=long_inserter)  # pick raw lane
                slot += 1

    # Direct-insertion inserters in the gap columns (machine rows 2..4). A
    # rightward flow means producer(i) -> consumer(i+1): the inserter sits in the
    # gap and faces WEST to pick the producer on its left; a leftward flow faces
    # EAST to pick the producer on its right.
    for i in range(n - 1):
        fr, fl = flow_right[i], flow_left[i]
        if fr <= 0 and fl <= 0:
            continue
        units = fr if fr > 0 else fl
        facing = WEST if fr > 0 else EAST
        n_gap = math.ceil(units / ins_cap)
        for k in range(n_gap):
            ins(gap_x(i), _Y_MACHINE + k, facing)

    placement.ports = [
        DenseBoundaryPort(top_raw, "input", "west", (0, _Y_TOP_LANE), EAST),
        DenseBoundaryPort(bot_raw, "input", "west", (0, _Y_RAW2_LANE), EAST),
        DenseBoundaryPort(product, "output", "east", (width - 1, _Y_PROD_LANE), EAST),
    ]
    return placement
