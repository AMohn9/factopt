"""CP-SAT direct-insertion placement (slot-grid model).

Direct insertion (machine -> machine, no intermediate belt) is the key density
trick, but with free 2D positions the "is A adjacent to B" relation is quadratic
and intractable. We make it tractable with a **slot grid**: machines live in
horizontal bands (rows of 3x3 slots) separated by 1-tile inserter gaps, exactly
the structure real compact builds use. Direct insertion is then a *vertical*
cable flow between a cable slot and the EC slot directly above/below it, carried
by inserters in the gap row.

The model assigns a recipe (or empty) to each slot and routes cable flow on the
vertical edges, minimizing the number of bands used (hence area for a fixed
width). It generalizes to any cable:EC counts; I/O belts (plate in, iron in,
circuit out) are left to a later routing pass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from factopt.data.database import Database
from factopt.model.blueprint import NORTH, SOUTH, Blueprint, Entity, Position
from factopt.ratios.solver import ProductionPlan

_ASSEMBLER = "assembling-machine-2"
_CABLE = "copper-cable"
_EC = "electronic-circuit"
_BAND_H = 3
_GAP = 1
_UNIT = 10  # flow scale: 1 item/s == 10 units (keeps the ILP integral)


@dataclass(frozen=True)
class DirectInserter:
    x: int
    y: int
    direction: int
    item: str
    src_kind: str  # "cable"
    dst_kind: str  # "ec"


@dataclass
class DirectPlacement:
    plan: ProductionPlan
    cols: int
    bands: int
    width: int
    height: int
    machines: list[Entity] = field(default_factory=list)
    inserters: list[DirectInserter] = field(default_factory=list)
    status: str = ""
    # (gap, col) -> scaled cable units injected; populated by the banded solver.
    cable_flow: dict = field(default_factory=dict)

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


def place_direct_banded(
    plan: ProductionPlan,
    db: Database,
    cols: int = 15,
    band_pattern: tuple[str, ...] = ("E", "C", "C", "E"),
    inserter: str = "fast-inserter",
    time_limit_s: float = 20.0,
    workers: int = 8,
) -> DirectPlacement:
    """Place machines in fixed bands with **horizontal** cable spread.

    Unlike :func:`place_direct` (column-aligned vertical flow only, which forces
    the 5-band C/E/C/E/C mirror), this allows cable to move along a transfer gap,
    so a wider cable band can feed a sparser EC band. With ``band_pattern =
    ("E","C","C","E")`` it reproduces the reference's structure: EC on the outer
    edges (free for iron/circuit I/O) and the two cable bands sharing a central
    channel (free for plate I/O). Cable transfer is solved as a 1-D min-flow per
    gap; the objective minimizes horizontal hops (fewer undergrounds).
    """
    counts = {ln.recipe: ln.machines for ln in plan.lines}
    if set(counts) != {_CABLE, _EC}:
        raise ValueError("banded direct placement handles the green-circuit chain only")
    n_cable, n_ec = counts[_CABLE], counts[_EC]

    speed = db.assemblers[_ASSEMBLER].crafting_speed
    cable_out = round(2.0 * (speed / db.recipes[_CABLE].time) * _UNIT)
    ec_in = round(3.0 * (speed / db.recipes[_EC].time) * _UNIT)
    ins_cap = int(db.inserters[inserter].rate * _UNIT)
    col_cap = 3 * ins_cap  # up to 3 inserters per 3-wide column edge
    horiz_cap = 100 * _UNIT

    R, C = len(band_pattern), cols
    m = cp_model.CpModel()
    is_m = {(r, c): m.new_bool_var(f"m_{r}_{c}") for r in range(R) for c in range(C)}

    cable_bands = [r for r in range(R) if band_pattern[r] == "C"]
    ec_bands = [r for r in range(R) if band_pattern[r] == "E"]
    m.add(sum(is_m[r, c] for r in cable_bands for c in range(C)) == n_cable)
    m.add(sum(is_m[r, c] for r in ec_bands for c in range(C)) == n_ec)

    # Per transfer gap (C adjacent to E): 1-D cable flow with vertical inject/
    # extract and horizontal hops.
    sup_used: dict = {}
    hop_r: dict = {}  # flow c -> c+1
    hop_l: dict = {}  # flow c+1 -> c
    objective_terms = []
    for g in range(R - 1):
        a, b = band_pattern[g], band_pattern[g + 1]
        if {a, b} != {"C", "E"}:
            continue
        cable_band = g if a == "C" else g + 1
        ec_band = g + 1 if a == "C" else g
        for c in range(C):
            sup_used[g, c] = m.new_int_var(0, col_cap, f"sup_{g}_{c}")
            m.add(sup_used[g, c] <= cable_out * is_m[cable_band, c])
        for c in range(C - 1):
            hop_r[g, c] = m.new_int_var(0, horiz_cap, f"hr_{g}_{c}")
            hop_l[g, c] = m.new_int_var(0, horiz_cap, f"hl_{g}_{c}")
            objective_terms += [hop_r[g, c], hop_l[g, c]]
        for c in range(C):
            inflow = []
            outflow = []
            if (g, c - 1) in hop_r:
                inflow.append(hop_r[g, c - 1])
            if (g, c) in hop_l:
                inflow.append(hop_l[g, c])
            if (g, c) in hop_r:
                outflow.append(hop_r[g, c])
            if (g, c - 1) in hop_l:
                outflow.append(hop_l[g, c - 1])
            dem = ec_in * is_m[ec_band, c]
            # supply + horizontal-in == demand + horizontal-out
            m.add(sup_used[g, c] + sum(inflow) == dem + sum(outflow))
            # demand met only where an EC machine sits, and within inserter cap.
            m.add(dem <= col_cap)

    if objective_terms:
        m.minimize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = workers
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"banded direct placement unsolved: {solver.status_name(status)} (try more cols)"
        )

    width = C * _BAND_H
    height = R * _BAND_H + (R - 1) * _GAP
    placement = DirectPlacement(
        plan=plan, cols=C, bands=R, width=width, height=height, status=solver.status_name(status)
    )

    def band_y(r):
        return r * (_BAND_H + _GAP)

    for r in range(R):
        recipe = _CABLE if band_pattern[r] == "C" else _EC
        for c in range(C):
            if solver.value(is_m[r, c]):
                x, y = c * _BAND_H, band_y(r)
                placement.machines.append(
                    Entity(name=_ASSEMBLER, position=Position(x + 1.5, y + 1.5), recipe=recipe)
                )

    # Record the solved per-column cable flow for the later tile-level weaver
    # (the surplus-cable distribution that tops EC machines up to 4.5/s).
    placement.cable_flow = {}
    for g in range(R - 1):
        if {band_pattern[g], band_pattern[g + 1]} != {"C", "E"}:
            continue
        for c in range(C):
            placement.cable_flow[(g, c)] = int(solver.value(sup_used[g, c]))

    # Layer 1a: aligned direct-insertion inserters only. Where an EC machine sits
    # directly across a transfer gap from a cable machine, 2 fast inserters move
    # that cable machine's full 3/s straight into the EC machine (no belt). This
    # under-feeds each EC (3/s of 4.5/s needed) on purpose: it is the minimal
    # testable slice to confirm the direct-insertion mechanic and inserter facing
    # in-game before the surplus distribution is woven in (layer 1b).
    n_aligned = math.ceil(cable_out / ins_cap)  # inserters to move one cable machine
    for g in range(R - 1):
        a, b = band_pattern[g], band_pattern[g + 1]
        if {a, b} != {"C", "E"}:
            continue
        cable_above = a == "C"
        cable_band = g if cable_above else g + 1
        ec_band = g + 1 if cable_above else g
        gap_y = band_y(g) + _BAND_H
        direction = SOUTH if not cable_above else NORTH  # points at the cable (pickup)
        for c in range(C):
            if solver.value(is_m[ec_band, c]) and solver.value(is_m[cable_band, c]):
                for k in range(n_aligned):
                    placement.inserters.append(
                        DirectInserter(
                            x=c * _BAND_H + k,
                            y=gap_y,
                            direction=direction,
                            item=_CABLE,
                            src_kind="cable",
                            dst_kind="ec",
                        )
                    )

    return placement


def place_direct(
    plan: ProductionPlan,
    db: Database,
    cols: int,
    inserter: str = "fast-inserter",
    max_bands: int | None = None,
    time_limit_s: float = 20.0,
    workers: int = 8,
) -> DirectPlacement:
    """Pack cable + EC machines into a slot grid with cable direct insertion.

    ``cols`` fixes the grid width (in machine columns); the number of bands is
    minimized. Raises if no feasible assignment is found.
    """
    counts = {ln.recipe: ln.machines for ln in plan.lines}
    if set(counts) != {_CABLE, _EC}:
        raise ValueError(
            f"direct placement handles the green-circuit chain only, got {set(counts)}"
        )
    n_cable, n_ec = counts[_CABLE], counts[_EC]
    if cols < 1:
        raise ValueError("cols must be >= 1")

    speed = db.assemblers[_ASSEMBLER].crafting_speed
    cable_out = round(2.0 * (speed / db.recipes[_CABLE].time) * _UNIT)  # per cable machine
    ec_in = round(3.0 * (speed / db.recipes[_EC].time) * _UNIT)  # per EC machine
    ins_cap = int(db.inserters[inserter].rate * _UNIT)  # per inserter
    edge_cap = 3 * ins_cap  # up to 3 inserters across a 3-wide column gap

    if max_bands is None:
        max_bands = (n_cable + n_ec) // cols + 5

    m = cp_model.CpModel()
    R, C = max_bands, cols

    is_cable = {(r, c): m.new_bool_var(f"cab_{r}_{c}") for r in range(R) for c in range(C)}
    is_ec = {(r, c): m.new_bool_var(f"ec_{r}_{c}") for r in range(R) for c in range(C)}
    for r in range(R):
        for c in range(C):
            m.add(is_cable[r, c] + is_ec[r, c] <= 1)

    m.add(sum(is_cable.values()) == n_cable)
    m.add(sum(is_ec.values()) == n_ec)

    # Vertical cable-flow edges between band r and r+1 at column c.
    down = {
        (r, c): m.new_int_var(0, edge_cap, f"dn_{r}_{c}") for r in range(R - 1) for c in range(C)
    }
    up = {(r, c): m.new_int_var(0, edge_cap, f"up_{r}_{c}") for r in range(R - 1) for c in range(C)}
    for r in range(R - 1):
        for c in range(C):
            # down: cable(r,c) -> ec(r+1,c)
            m.add(down[r, c] <= edge_cap * is_cable[r, c])
            m.add(down[r, c] <= edge_cap * is_ec[r + 1, c])
            # up: cable(r+1,c) -> ec(r,c)
            m.add(up[r, c] <= edge_cap * is_cable[r + 1, c])
            m.add(up[r, c] <= edge_cap * is_ec[r, c])

    def out_of(r, c):
        terms = []
        if r < R - 1:
            terms.append(down[r, c])  # to the band below
        if r > 0:
            terms.append(up[r - 1, c])  # to the band above
        return terms

    def into(r, c):
        terms = []
        if r > 0:
            terms.append(down[r - 1, c])  # from the band above
        if r < R - 1:
            terms.append(up[r, c])  # from the band below
        return terms

    for r in range(R):
        for c in range(C):
            # Cable machines may ship up to their full output (surplus capacity ok).
            m.add(sum(out_of(r, c)) <= cable_out * is_cable[r, c])
            # EC machines must be fully fed.
            m.add(sum(into(r, c)) == ec_in * is_ec[r, c])

    # Band usage: contiguous from the top, minimized.
    used = [m.new_bool_var(f"used_{r}") for r in range(R)]
    for r in range(R):
        for c in range(C):
            m.add(is_cable[r, c] <= used[r])
            m.add(is_ec[r, c] <= used[r])
    for r in range(R - 1):
        m.add(used[r] >= used[r + 1])
    m.minimize(sum(used))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = workers
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"direct placement infeasible/unsolved: {solver.status_name(status)} (try more cols)"
        )

    bands = int(sum(solver.value(used[r]) for r in range(R)))
    width = C * _BAND_H
    height = bands * _BAND_H + max(bands - 1, 0) * _GAP

    placement = DirectPlacement(
        plan=plan,
        cols=C,
        bands=bands,
        width=width,
        height=height,
        status=solver.status_name(status),
    )

    def band_y(r):
        return r * (_BAND_H + _GAP)

    for r in range(R):
        for c in range(C):
            if solver.value(is_cable[r, c]):
                recipe = _CABLE
            elif solver.value(is_ec[r, c]):
                recipe = _EC
            else:
                continue
            x, y = c * _BAND_H, band_y(r)
            placement.machines.append(
                Entity(name=_ASSEMBLER, position=Position(x + 1.5, y + 1.5), recipe=recipe)
            )

    # Inserters in each gap, one set per flowing edge.
    for r in range(R - 1):
        gap_y = band_y(r) + _BAND_H  # the single gap row below band r
        for c in range(C):
            d, u = int(solver.value(down[r, c])), int(solver.value(up[r, c]))
            flow = d if d > 0 else u
            if flow <= 0:
                continue
            n = math.ceil(flow / ins_cap)
            # down: cable above (band r) -> EC below; inserter picks up (NORTH).
            # up:   cable below -> EC above; inserter picks down (SOUTH).
            direction = NORTH if d > 0 else SOUTH
            for k in range(n):
                placement.inserters.append(
                    DirectInserter(
                        x=c * _BAND_H + k,
                        y=gap_y,
                        direction=direction,
                        item=_CABLE,
                        src_kind="cable",
                        dst_kind="ec",
                    )
                )

    return placement
