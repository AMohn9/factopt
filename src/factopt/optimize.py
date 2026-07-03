"""Top-level block optimizer: pick the best complete block for a goal.

Given a target item and rate, this runs the general-purpose Benders cut loop
(:func:`factopt.loop.optimize_loop`) in its two flavours, keeps the ones that
are importable and meet the target, and returns the tightest (smallest
footprint). It is the single entrypoint the rest of the pipeline (and
eventually a Factorio-sim-scored search) plugs into.

Strategies:

* ``benders`` -- the CP-SAT master-placement + coarse-routing + detailed-routing
  cut loop. The general strategy with no layout assumptions; slower (a CP-SAT
  master per iteration), so it gets a time budget.
* ``dense`` -- the same loop with ``fuse=True``: a fusable 2-level chain (e.g.
  green circuits) is packed as one dense **direct-insertion** cell (the
  intermediate is inserted machine-to-machine, never belted) with only its raws
  and product routed as block boundary I/O.

Both are thin wrappers over :func:`factopt.loop.optimize_loop` (see
``scripts/steiner_run.py`` for the same call used interactively). The earlier
hand-rolled generators (``compact``/``mvp``, ``bus``, ``line``) and the
interior-only research placers have been removed now that the loop is the
standard place-and-route path.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.data.database import Database
from factopt.ratios.solver import ProductionPlan, solve_ratios

DEFAULT_STRATEGIES = ("benders", "dense")


@dataclass
class Candidate:
    """One strategy's attempt at a block (or why it couldn't produce one)."""

    strategy: str
    ok: bool
    complete: bool = False
    meets_target: bool = False
    width: int = 0
    height: int = 0
    blueprint_string: str = ""
    detail: str = ""

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def usable(self) -> bool:
        return self.ok and self.complete and self.meets_target


@dataclass
class OptimizedBlock:
    target: str
    rate: float
    plan: ProductionPlan
    best: Candidate | None
    candidates: list[Candidate] = field(default_factory=list)

    @property
    def blueprint_string(self) -> str:
        if self.best is None:
            raise ValueError(f"no usable block found for {self.rate:g}/s {self.target}")
        return self.best.blueprint_string

    def summary(self) -> str:
        lines = [f"{self.rate:g}/s {self.target}: {self.plan.total_machines} machines"]
        for c in self.candidates:
            if not c.ok:
                lines.append(f"  [skip] {c.strategy:<8} {c.detail}")
                continue
            mark = "*best*" if c is self.best else "      "
            flags = []
            if not c.complete:
                flags.append("incomplete")
            if not c.meets_target:
                flags.append("under-target")
            tag = f" ({', '.join(flags)})" if flags else ""
            lines.append(
                f"  {mark} {c.strategy:<8} {c.width}x{c.height} = {c.area}t{tag}"
                + (f"  {c.detail}" if c.detail else "")
            )
        if self.best is None:
            lines.append("  -> no complete, target-meeting block found")
        return "\n".join(lines)


def _try_loop(
    strategy: str,
    target: str,
    rate: float,
    db: Database,
    budget_s: float,
    fuse: bool,
    backend: str = "cpsat",
    workers: int | None = None,
) -> Candidate:
    from factopt.loop import optimize_loop

    try:
        res = optimize_loop(
            target, rate, db, time_budget_s=budget_s, master_time_limit_s=15.0,
            fuse=fuse, backend=backend, workers=workers,
        )
    except Exception as exc:
        return Candidate(strategy, ok=False, detail=f"{type(exc).__name__}: {exc}")
    if res.best is None:
        return Candidate(
            strategy,
            ok=True,
            complete=False,
            detail=f"unrouted after {len(res.iterations)} iteration(s), "
            f"{len(res.cuts)} cut(s)",
        )
    best = res.best
    return Candidate(
        strategy=strategy,
        ok=True,
        complete=True,
        # Nets are dedicated belts sized by the ratio plan; a validated,
        # fully-routed block meets the target analytically.
        meets_target=best.validation.ok,
        width=best.width,
        height=best.height,
        blueprint_string=best.blueprint_string,
        detail=f"{len(res.iterations)} iteration(s), {len(res.cuts)} cut(s)",
    )


def optimize(
    target: str,
    rate: float,
    db: Database,
    strategies: tuple[str, ...] = DEFAULT_STRATEGIES,
    benders_budget_s: float = 180.0,
    backend: str = "cpsat",
    workers: int | None = None,
) -> OptimizedBlock:
    """Return the tightest complete, target-meeting block for ``rate``/s of
    ``target``, running the Benders loop in each requested flavour. ``backend``
    selects the master solver engine (``"cpsat"`` or ``"scip"``); ``workers``
    sets the CP-SAT portfolio size (``None`` = all cores)."""
    if rate <= 0:
        raise ValueError("rate must be positive")
    plan = solve_ratios(target, rate, db)

    tries = {
        "benders": lambda: _try_loop(
            "benders", target, rate, db, benders_budget_s, False, backend, workers
        ),
        "dense": lambda: _try_loop(
            "dense", target, rate, db, benders_budget_s, True, backend, workers
        ),
    }
    candidates = [tries[s]() for s in strategies if s in tries]

    usable = [c for c in candidates if c.usable]
    best = min(usable, key=lambda c: c.area) if usable else None
    return OptimizedBlock(
        target=target, rate=rate, plan=plan, best=best, candidates=candidates
    )
