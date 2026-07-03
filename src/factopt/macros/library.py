"""Build the macro-cell instance for a production plan.

Turns a :class:`~factopt.ratios.solver.ProductionPlan` into:

* one **unit** per recipe -- a recipe band (:func:`factopt.band.build_band`) or,
  with fusion, a dense **direct-insertion** cell covering a producer/consumer
  pair whose internal item is never routed;
* one **input connector** per raw item (pinned to the west edge);
* one **output collector** for the target (pinned to the east edge).

Item transport uses **shared belt trunks**: an item's consumers are partitioned
into trunks that fit one belt lane's throughput, and each trunk becomes one
**multi-sink net** (:class:`FlowNet` with one source port and one
:class:`FlowSink` per consumer). The detailed router realizes a trunk as a
Steiner *tree* -- one belt leaves the source and splitters branch it toward
every sink -- so consumers no longer need pass-through lanes or a fixed visit
order. A splitter cascade at the source appears only when an item genuinely
needs several trunks.

The result (:class:`MacroProblem`) is the master problem's input: macros to
place, nets to route, and edge pins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.band import build_band
from factopt.data.database import Database
from factopt.macros.cell import (
    MacroCell,
    PlacedMacro,
    PortCandidate,
    PortEnd,
    ReversibleLane,
    Side,
)
from factopt.model.blueprint import EAST, WEST, Entity, Position
from factopt.placement.dense import (
    DensePlacement,
    place_dense_row,
    plan_fusions,
    subplan_for_group,
)
from factopt.ratios.solver import ProductionPlan
from factopt.validate import entity_tiles

_SPLITTER_OF = {
    "transport-belt": "splitter",
    "fast-transport-belt": "fast-splitter",
    "express-transport-belt": "express-splitter",
}


@dataclass(frozen=True)
class FlowSink:
    """One consumer of a multi-sink net: a macro input port and its demand."""

    macro: str
    port: str
    rate_per_sec: float


@dataclass(frozen=True)
class FlowNet:
    """One item trunk the detailed router must realize as a belt *tree*:
    a single source port feeding every sink port, with splitters at the
    junctions. ``rate_per_sec`` is the trunk's total demand (the sum over
    sinks), which fits one belt by construction."""

    id: str
    item: str
    source_macro: str
    source_port: str
    sinks: tuple[FlowSink, ...]
    rate_per_sec: float


@dataclass
class MacroProblem:
    plan: ProductionPlan
    macros: dict[str, MacroCell] = field(default_factory=dict)
    nets: list[FlowNet] = field(default_factory=list)
    # Macro id -> blueprint edge it must touch ("west" inputs, "east" output).
    pins: dict[str, Side] = field(default_factory=dict)
    # Trunk structure behind the nets: item -> trunks -> (unit id, demand).
    # Each trunk becomes one multi-sink FlowNet; the router picks the actual
    # branch topology, so the order within a trunk carries no meaning.
    chains: dict[str, list[list[tuple[str, float]]]] = field(default_factory=dict)
    # item -> the macro whose output ports source that item's trunks.
    sources: dict[str, str] = field(default_factory=dict)


def _fanout_east(
    entities: list[Entity],
    belt_name: str,
    feed_col: int,
    row: int,
    k: int,
) -> tuple[list[tuple[int, int]], int, int]:
    """Extend an EAST-flowing lane whose last belt sits at ``(feed_col - 1,
    row)`` into ``k`` separate east-edge branches via a diagonal splitter
    cascade. Appends the new entities and returns
    ``(port_tiles, width_needed, max_row)``.
    """
    if k <= 1:
        return [(feed_col - 1, row)], feed_col, row

    splitter = _SPLITTER_OF.get(belt_name, "splitter")
    end_col = feed_col + 2 * (k - 2) + 1

    def belt(x: int, y: int) -> None:
        entities.append(
            Entity(name=belt_name, position=Position(x + 0.5, y + 0.5), direction=EAST)
        )

    for i in range(k - 1):
        c = feed_col + 2 * i
        # EAST-facing splitter occupying (c, row+i) and (c, row+i+1); its
        # upper input is fed by the lane (i == 0) or the previous bridge belt.
        entities.append(
            Entity(name=splitter, position=Position(c + 0.5, row + i + 1.0), direction=EAST)
        )
        # Upper output: branch i runs east to the macro edge.
        for x in range(c + 1, end_col + 1):
            belt(x, row + i)
        if i < k - 2:
            # Lower output bridges one tile east into the next splitter.
            belt(c + 1, row + i + 1)
        else:
            # Lower output of the last splitter: branch k-1 to the edge.
            for x in range(c + 1, end_col + 1):
                belt(x, row + i + 1)

    ports = [(end_col, row + i) for i in range(k)]
    return ports, end_col + 1, row + k - 1


def _input_lane_port(
    entities: list[Entity],
    belt: str,
    item: str,
    row: int,
    lane_end: int,
    cell_width: int,
    cap: float,
    db: Database,
    port_id: str | None = None,
) -> tuple[PortCandidate, ReversibleLane | None]:
    """Build an input port for a horizontal lane that already spans columns
    ``[0, lane_end)`` at ``row``.

    Machines only *pick* from an input lane, so it can be fed from either end.
    When the lane can be extended east to the cell's edge without hitting any
    other entity, the port becomes **reversible**: the primary end feeds it
    from the west (belts flow EAST), the reverse end from the east (belts flow
    WEST). The extension belts are appended and a :class:`ReversibleLane`
    describing the lane's tiles is returned so emission can flip them. If the
    east edge is blocked (e.g. by an output fanout), the port is west-only.
    """
    pid = port_id or f"{item}-in"
    occupied: set[tuple[int, int]] = set()
    for e in entities:
        occupied.update(entity_tiles(e, db))

    ext_cols = list(range(lane_end, cell_width))
    can_reverse = all((c, row) not in occupied for c in ext_cols)

    port = PortCandidate(
        id=pid,
        item=item,
        direction="input",
        side="west",
        local_position=(0, row),
        flow_entry_dir=EAST,
        max_rate_per_sec=cap,
    )
    if not can_reverse:
        return port, None

    for c in ext_cols:
        entities.append(
            Entity(name=belt, position=Position(c + 0.5, row + 0.5), direction=EAST)
        )
    east_end = cell_width - 1
    port = PortCandidate(
        id=pid,
        item=item,
        direction="input",
        side="west",
        local_position=(0, row),
        flow_entry_dir=EAST,
        max_rate_per_sec=cap,
        reverse=PortEnd(side="east", local_position=(east_end, row), flow_entry_dir=WEST),
    )
    lane = ReversibleLane(
        tiles=tuple((x, row) for x in range(cell_width)),
        forward_dir=EAST,
        reverse_dir=WEST,
    )
    return port, lane


def _band_macro(
    recipe: str,
    n_machines: int,
    n_out: int,
    db: Database,
    belt: str,
    inserter: str,
    long_inserter: str,
    cap: float,
) -> MacroCell:
    """One recipe band as a macro. ``n_out`` is the number of product trunks
    (output ports)."""
    band = build_band(
        recipe,
        n_machines,
        db,
        inserter=inserter,
        long_inserter=long_inserter,
        with_lane_belts=True,
        belt_name=belt,
    )
    entities = list(band.entities)
    ports: list[PortCandidate] = []

    in_slots = [(slot, a) for slot, a in band.lanes.items() if a.flow_dir == "in"]
    out_slot, out_item = None, None
    for slot, a in band.lanes.items():
        if a.flow_dir == "out":
            out_slot, out_item = slot, a.item

    # Output fanout first: it fixes the cell width the input lanes may reverse
    # against (a lane can only be fed from the east if it reaches the edge).
    width, height = band.width, band.height
    if out_slot is not None and n_out >= 1:
        out_row = band.lane_row[out_slot]
        tiles, width_needed, max_row = _fanout_east(
            entities, belt, band.width, out_row, n_out
        )
        width = max(width, width_needed)
        height = max(height, max_row + 1)
        for i, (px, py) in enumerate(tiles):
            ports.append(
                PortCandidate(
                    id=f"{out_item}-out-{i}",
                    item=out_item,
                    direction="output",
                    side="east",
                    local_position=(px, py),
                    flow_entry_dir=EAST,
                    max_rate_per_sec=cap,
                )
            )

    reversible_lanes: dict[str, ReversibleLane] = {}
    for slot, a in in_slots:
        port, lane = _input_lane_port(
            entities, belt, a.item, band.lane_row[slot], band.width, width, cap, db
        )
        ports.append(port)
        if lane is not None:
            reversible_lanes[port.id] = lane

    return MacroCell(
        id=recipe,
        kind="recipe-band",
        width=width,
        height=height,
        entities=tuple(entities),
        ports=tuple(ports),
        reversible_lanes=reversible_lanes,
    )


def _dense_macro(
    macro_id: str,
    placement: DensePlacement,
    n_out: int,
    belt: str,
    cap: float,
    db: Database,
) -> tuple[MacroCell, str]:
    """Wrap a :class:`DensePlacement` as a placeable/routable macro.

    The internal item is direct-inserted, so it is never a port. The producer's
    and consumer's raws become west input ports; the product becomes one east
    output port per trunk.

    Returns ``(cell, product_item)``.
    """
    entities = list(placement.entities())
    ports: list[PortCandidate] = []

    product_port = next(p for p in placement.ports if p.direction == "output")
    in_ports = [p for p in placement.ports if p.direction == "input"]

    # Output fanout first: fixes the cell width the input lanes reverse against.
    width, height = placement.width, placement.height
    product = product_port.item
    out_col, out_row = product_port.local_position
    tiles, width_needed, max_row = _fanout_east(
        entities, belt, out_col + 1, out_row, max(n_out, 1)
    )
    width = max(width, width_needed)
    height = max(height, max_row + 1)
    for i, (px, py) in enumerate(tiles):
        ports.append(
            PortCandidate(
                id=f"{product}-out-{i}",
                item=product,
                direction="output",
                side="east",
                local_position=(px, py),
                flow_entry_dir=EAST,
                max_rate_per_sec=cap,
            )
        )

    reversible_lanes: dict[str, ReversibleLane] = {}
    for p in in_ports:
        row = p.local_position[1]
        port, lane = _input_lane_port(
            entities, belt, p.item, row, placement.width, width, cap, db,
            port_id=f"{p.item}-in",
        )
        ports.append(port)
        if lane is not None:
            reversible_lanes[port.id] = lane

    return (
        MacroCell(
            id=macro_id,
            kind="dense-direct",
            width=width,
            height=height,
            entities=tuple(entities),
            ports=tuple(ports),
            reversible_lanes=reversible_lanes,
        ),
        product,
    )


def _input_connector(item: str, k: int, db: Database, belt: str, cap: float) -> MacroCell:
    """West-edge stub where an infinite input belt of ``item`` enters, fanned
    out into one east-edge port per consuming band."""
    entities: list[Entity] = [
        Entity(name=belt, position=Position(0.5, 0.5), direction=EAST),
    ]
    tiles, width_needed, max_row = _fanout_east(entities, belt, 1, 0, k)
    if k <= 1:
        # Give the stub some body so its port isn't on the same tile as the
        # entry belt.
        entities.append(Entity(name=belt, position=Position(1.5, 0.5), direction=EAST))
        tiles, width_needed = [(1, 0)], 2
    ports = tuple(
        PortCandidate(
            id=f"{item}-out-{i}",
            item=item,
            direction="output",
            side="east",
            local_position=(px, py),
            flow_entry_dir=EAST,
            max_rate_per_sec=cap,
        )
        for i, (px, py) in enumerate(tiles)
    )
    return MacroCell(
        id=f"in-{item}",
        kind="input-connector",
        width=width_needed,
        height=max_row + 1,
        entities=tuple(entities),
        ports=ports,
    )


def _output_collector(item: str, belt: str, cap: float) -> MacroCell:
    entities = tuple(
        Entity(name=belt, position=Position(x + 0.5, 0.5), direction=EAST) for x in range(2)
    )
    port = PortCandidate(
        id=f"{item}-in",
        item=item,
        direction="input",
        side="west",
        local_position=(0, 0),
        flow_entry_dir=EAST,
        max_rate_per_sec=cap,
    )
    return MacroCell(
        id="out",
        kind="output-collector",
        width=2,
        height=1,
        entities=entities,
        ports=(port,),
    )


def _partition_chains(
    entries: list[tuple[str, float]], cap: float
) -> list[list[tuple[str, float]]]:
    """Partition one item's consumers into shared belt trunks.

    Each trunk's total demand fits one lane's throughput ``cap`` (the trunk's
    root edge carries all of it). Consumers are packed heaviest-first
    (first-fit decreasing); within a trunk the order carries no meaning --
    the Steiner router picks the branch topology from the actual geometry.
    """
    ordered = sorted((e for e in entries if e[0] != "out"), key=lambda t: (-t[1], t[0]))
    terminal = [e for e in entries if e[0] == "out"]
    chains: list[list[tuple[str, float]]] = []
    loads: list[float] = []
    for uid, d in ordered + terminal:
        for i, load in enumerate(loads):
            if load + d <= cap + 1e-9:
                chains[i].append((uid, d))
                loads[i] += d
                break
        else:
            chains.append([(uid, d)])
            loads.append(d)
    return chains


def build_problem(
    plan: ProductionPlan,
    db: Database,
    belt: str = "transport-belt",
    inserter: str = "fast-inserter",
    long_inserter: str = "long-handed-inserter",
    fuse: bool = False,
) -> MacroProblem:
    """Construct macros, nets, and pins for ``plan``.

    Recipes are grouped into **units**: an ungrouped recipe is a belt-fed band;
    with ``fuse=True``, a fusable producer/consumer pair (e.g. copper-cable ->
    electronic-circuit) becomes one dense **direct-insertion** cell whose
    internal item is never routed.

    Each item's consumers share **belt trunks**: consumers are partitioned into
    trunks fitting one lane's throughput, and each trunk is one multi-sink
    :class:`FlowNet`. The detailed router grows a Steiner tree per trunk --
    one belt from the source, splitters branching toward every sink -- so the
    branch topology adapts to whatever geometry the master chooses.
    """
    counts = {ln.recipe: ln.machines for ln in plan.lines}
    crafts = {ln.recipe: ln.crafts_per_sec for ln in plan.lines}
    cap = db.belts[belt].throughput

    groups = plan_fusions(plan, db) if fuse else []

    # recipe -> unit id (a band unit is its recipe name; a dense unit gets a
    # synthetic id) and, per dense unit, the items it makes/uses internally.
    recipe_unit: dict[str, str] = {}
    dense_units: dict[str, set[str]] = {}
    unit_internal: dict[str, set[str]] = {}
    for g in groups:
        uid = f"dense-{sorted(g)[0]}"
        dense_units[uid] = g
        made: set[str] = set()
        used: set[str] = set()
        for r in g:
            recipe_unit[r] = uid
            made |= set(db.recipes[r].products)
            used |= set(db.recipes[r].ingredients)
        unit_internal[uid] = made & used
    for r in counts:
        recipe_unit.setdefault(r, r)

    def unit_recipes(uid: str) -> list[str]:
        return sorted(dense_units[uid]) if uid in dense_units else [uid]

    def unit_product(uid: str) -> str:
        internal = unit_internal.get(uid, set())
        products = [
            it for r in unit_recipes(uid) for it in db.recipes[r].products
            if it not in internal
        ]
        return products[0]

    def demand(uid: str, item: str) -> float:
        internal = unit_internal.get(uid, set())
        if item in internal:
            return 0.0
        return sum(
            crafts[r] * db.recipes[r].ingredients.get(item, 0.0)
            for r in unit_recipes(uid)
        )

    # item -> units that consume it externally, deterministic.
    consumers: dict[str, list[str]] = {}
    for r in sorted(counts):
        uid = recipe_unit[r]
        internal = unit_internal.get(uid, set())
        for item in db.recipes[r].ingredients:
            if item in internal:
                continue
            lst = consumers.setdefault(item, [])
            if uid not in lst:
                lst.append(uid)

    # ---- chain plan: shared trunks per item -------------------------------
    chains: dict[str, list[list[tuple[str, float]]]] = {}
    for item in sorted(consumers):
        entries = [(u, demand(u, item)) for u in consumers[item]]
        if item == plan.target:
            entries.append(("out", plan.rate))
        chains[item] = _partition_chains(entries, cap)
    if plan.target not in chains:
        chains[plan.target] = [[("out", plan.rate)]]

    problem = MacroProblem(plan=plan)
    producer_of: dict[str, str] = {}

    # Dense direct-insertion cells.
    for uid, g in sorted(dense_units.items()):
        product = unit_product(uid)
        placement = place_dense_row(
            subplan_for_group(plan, db, g), db,
            inserter=inserter, long_inserter=long_inserter, belt=belt,
        )
        macro, _ = _dense_macro(
            uid, placement, len(chains.get(product, [])), belt, cap, db,
        )
        problem.macros[uid] = macro
        producer_of[product] = uid

    # Belt-fed recipe bands (everything not fused).
    for r in sorted(counts):
        if recipe_unit[r] != r:
            continue
        out_item = next(iter(db.recipes[r].products))
        macro = _band_macro(
            r, counts[r], len(chains.get(out_item, [])),
            db, belt, inserter, long_inserter, cap,
        )
        problem.macros[r] = macro
        producer_of[out_item] = r

    # Raw-item input connectors on the west edge (one port per trunk).
    for item in sorted(c for c in consumers if db.is_raw(c)):
        macro = _input_connector(item, len(chains[item]), db, belt, cap)
        problem.macros[macro.id] = macro
        problem.pins[macro.id] = "west"
        producer_of[item] = macro.id

    # Target output collector on the east edge.
    collector = _output_collector(plan.target, belt, cap)
    problem.macros[collector.id] = collector
    problem.pins[collector.id] = "east"

    problem.chains = chains
    problem.sources = producer_of
    _emit_trunk_nets(problem)

    return problem


def _emit_trunk_nets(problem: MacroProblem) -> None:
    """Build ``problem.nets`` from the trunk structure: one multi-sink net per
    trunk, carrying the trunk's total demand from its source output port to
    every consumer's input port."""
    problem.nets = []
    for item, item_chains in sorted(problem.chains.items()):
        src = problem.sources[item]
        for ci, chain in enumerate(item_chains):
            sinks = tuple(FlowSink(macro=uid, port=f"{item}-in", rate_per_sec=d) for uid, d in chain)
            problem.nets.append(
                FlowNet(
                    id=f"{item}:{src}-t{ci}",
                    item=item,
                    source_macro=src,
                    source_port=f"{item}-out-{ci}",
                    sinks=sinks,
                    rate_per_sec=sum(d for _, d in chain),
                )
            )
