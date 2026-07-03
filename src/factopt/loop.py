"""Benders-style optimization loop (M5/M6).

Repeats master -> detailed routing -> cuts. The margin/area-slack schedule
loosens the master when cuts alone are not fixing infeasibility, mirroring
the "minimize infeasibility first" lexicographic intent.

A routed placement does **not** end the loop: it becomes the incumbent, and
the remaining budget keeps searching with the incumbent's area as a hard
master bound (strictly smaller only), at the margin/slack that just
succeeded. The loop therefore uses its whole time budget to tighten, and
returns the best candidate found.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass, field

from factopt.codec import encode
from factopt.data.database import Database
from factopt.macros import MacroProblem, build_problem
from factopt.master.backend import Backend
from factopt.master.cuts import BendersCut
from factopt.master.model import MasterSolution, solve_master
from factopt.model.blueprint import Blueprint
from factopt.ratios.solver import ProductionPlan, solve_ratios
from factopt.routing.explain import explain_failures
from factopt.routing.multinet import RoutingResult, route_nets
from factopt.validate import ValidationReport, validate

# (margin, area_slack) per iteration; repeats the last entry when exhausted.
# Orientation freedom lets the master keep finding fresh tight-but-congested
# layouts at a given margin, so the ladder ends in a roomy fallback.
_SCHEDULE = [
    (1, 0.0),
    (1, 0.15),
    (2, 0.15),
    (2, 0.3),
    (3, 0.3),
    (3, 0.5),
    (4, 0.5),
    (4, 0.7),
]

# Where ``start_loose`` begins. NOT the loosest rung: empirically, starting at
# margin 4 makes the master's stage-1 area minimization intractable within a
# per-solve time limit (the inflated canvas is huge), so the incumbent lands
# bloated and the tightening phase only shaves ~1 tile per solve. A moderately
# roomy rung -- enough spacing to route on the first try, small enough that the
# master still minimizes area well -- gives a fast first incumbent *and* lets
# each tightening solve jump straight to that rung's true minimum. Index 3 is
# (2, 0.3): margin 2 (the rung where the tight results actually appear) with
# generous area slack for routability.
_LOOSE_START = 3


@dataclass
class Iteration:
    index: int
    margin: int
    area_slack: float
    master: MasterSolution
    routing: RoutingResult | None
    new_cuts: list[BendersCut] = field(default_factory=list)
    master_s: float = 0.0  # wall time of the CP-SAT master solve
    routing_s: float = 0.0  # wall time of detailed routing


@dataclass
class Candidate:
    blueprint: Blueprint
    blueprint_string: str
    master: MasterSolution
    routing: RoutingResult
    validation: ValidationReport

    @property
    def width(self) -> int:
        return self.master.width

    @property
    def height(self) -> int:
        return self.master.height

    @property
    def area(self) -> int:
        return self.master.area


@dataclass
class LoopResult:
    problem: MacroProblem
    best: Candidate | None
    iterations: list[Iteration]
    cuts: list[BendersCut]
    # Budgets the loop was given and the wall time it actually used.
    time_budget_s: float = 0.0
    master_time_limit_s: float = 0.0
    max_iterations: int = 0
    elapsed_s: float = 0.0

    @property
    def feasible(self) -> bool:
        return self.best is not None

    def summary(self) -> str:
        lines = []
        if self.max_iterations:
            lines.append(
                f"budget: {self.time_budget_s:g}s total, "
                f"{self.master_time_limit_s:g}s/master solve, "
                f"{self.max_iterations} iteration(s) max; "
                f"used {self.elapsed_s:.0f}s over {len(self.iterations)} iteration(s)"
            )
        for it in self.iterations:
            status = "unsolved"
            if it.master.ok:
                if it.routing is not None and it.routing.feasible:
                    status = "routed"
                else:
                    kinds = (
                        [f.kind for f in it.routing.failures] if it.routing is not None else []
                    )
                    status = f"failed ({', '.join(kinds)})"
            lines.append(
                f"iter {it.index}: margin={it.margin} slack={it.area_slack:g} "
                f"bbox={it.master.width}x{it.master.height} {status}; "
                f"+{len(it.new_cuts)} cuts "
                f"[master {it.master_s:.0f}s, route {it.routing_s:.1f}s]"
            )
        for cut in self.cuts:
            lines.append(f"  cut[{cut.kind}] {cut.explanation}")
        return "\n".join(lines)


def _assemble(
    problem: MacroProblem,
    master: MasterSolution,
    routing: RoutingResult,
    db: Database,
    label: str,
) -> Candidate:
    entities = list(routing.entities)
    for pm in master.placements.values():
        entities.extend(pm.entities())
    flows = [
        (
            master.port_tile(n.source_macro, n.source_port),
            master.port_tile(s.macro, s.port),
        )
        for n in problem.nets
        for s in n.sinks
    ]
    report = validate(entities, db, bounds=(0, 0, master.width, master.height), flows=flows)
    bp = Blueprint(label=label, entities=entities)
    return Candidate(
        blueprint=bp,
        blueprint_string=encode(bp),
        master=master,
        routing=routing,
        validation=report,
    )


def optimize_loop(
    target: str,
    rate: float,
    db: Database,
    plan: ProductionPlan | None = None,
    belt: str = "transport-belt",
    max_iterations: int = 8,
    coarse_cell: int | None = 4,
    master_time_limit_s: float = 20.0,
    time_budget_s: float = 240.0,
    label: str | None = None,
    fuse: bool = False,
    backend: Backend = "cpsat",
    workers: int | None = None,
    inputs: Iterable[str] = (),
    max_w: int | None = None,
    max_h: int | None = None,
    max_area: int | None = None,
    start_loose: bool = False,
) -> LoopResult:
    """Run the Benders loop for ``rate`` items/s of ``target``.

    With ``fuse=True``, a fusable 2-level chain is packed as one dense
    direct-insertion cell (no belt for the internal item) before placement.
    ``backend`` selects the master solver engine (``"cpsat"`` or ``"scip"``).
    ``workers`` is the CP-SAT search portfolio size (``None`` = all cores).

    ``inputs`` names intermediates supplied from outside the block (e.g.
    circuits produced elsewhere in the factory): they are treated as raw
    inputs, so their sub-tree is not built here and each enters through a
    west-edge input connector. This is the lever for keeping deep targets
    (e.g. higher science packs) tractable.

    ``max_w``/``max_h`` cap the canvas (and every macro's placement variables)
    to a fixed side; ``max_area`` is a hard bounding-box-area cap. All three
    apply to *every* master solve, so the loop only ever searches inside the
    given envelope -- e.g. ``max_w=19, max_h=32`` asks "can this route inside
    the 19x32 box the best known solution used?". The area cap is combined
    with the incumbent bound (the tighter of the two wins), so a runtime cap
    never loosens the anytime tightening.

    ``start_loose`` reverses the feasibility phase: instead of starting at the
    tightest margin/slack rung and loosening on routing failure, the loop
    starts at the *roomiest* rung so a routable incumbent appears almost
    immediately, then the tightening phase walks the margin back down under
    the shrinking area bound. This trades a larger first footprint for far
    fewer wasted "tight-but-unroutable" iterations, spending the budget on
    tightening a real solution rather than on finding the first one.
    """
    inputs = frozenset(inputs)
    if target in inputs:
        raise ValueError(f"target {target!r} cannot also be supplied as an input")
    db = db.with_inputs(inputs)
    if plan is None:
        plan = solve_ratios(target, rate, db)
    problem = build_problem(plan, db, belt=belt, fuse=fuse)
    label = label or f"{target}-benders-{rate:g}ps"

    cuts: list[BendersCut] = []
    iterations: list[Iteration] = []
    best: Candidate | None = None
    started = time.monotonic()

    margin, slack = _SCHEDULE[_LOOSE_START] if start_loose else _SCHEDULE[0]
    for i in range(max_iterations):
        if time.monotonic() - started > time_budget_s:
            break
        if best is None and not start_loose:
            # Feasibility phase: walk the loosening schedule from the tight end.
            # (start_loose pins a moderately roomy rung so the first incumbent
            # lands fast and the tightening phase does the margin walk-down.)
            margin, slack = _SCHEDULE[min(i, len(_SCHEDULE) - 1)]
        # Tightening phase: keep the rung that routed, bound the master by
        # the incumbent so only strictly smaller placements come back. Fold in
        # any runtime area cap (the tighter of the two wins).
        area_cap = best.area - 1 if best is not None else None
        if max_area is not None:
            area_cap = max_area if area_cap is None else min(area_cap, max_area)
        t0 = time.monotonic()
        master = solve_master(
            problem,
            cuts=cuts,
            margin=margin,
            area_slack=slack,
            coarse_cell=coarse_cell,
            time_limit_s=master_time_limit_s,
            max_w=max_w,
            max_h=max_h,
            max_area=area_cap,
            backend=backend,
            workers=workers,
        )
        it = Iteration(index=i, margin=margin, area_slack=slack, master=master, routing=None)
        it.master_s = time.monotonic() - t0
        iterations.append(it)
        if not master.ok:
            if best is None:
                # All placements at this margin are cut off; the schedule
                # will loosen next round.
                continue
            # No strictly tighter placement at this margin: retry with less
            # spacing (tighter areas live at smaller margins), stop at 1.
            if margin <= 1:
                break
            margin -= 1
            continue

        t0 = time.monotonic()
        routing = route_nets(problem, master, db, belt=belt)
        it.routing_s = time.monotonic() - t0
        it.routing = routing
        if routing.feasible:
            # New incumbent (the area cap guarantees it is strictly better);
            # keep searching with the remaining budget.
            best = _assemble(problem, master, routing, db, label)
            continue

        new_cuts = explain_failures(problem, master, routing, db, belt=belt)
        it.new_cuts = new_cuts
        cuts.extend(new_cuts)

    return LoopResult(
        problem=problem,
        best=best,
        iterations=iterations,
        cuts=cuts,
        time_budget_s=time_budget_s,
        master_time_limit_s=master_time_limit_s,
        max_iterations=max_iterations,
        elapsed_s=time.monotonic() - started,
    )
