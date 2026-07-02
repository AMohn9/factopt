"""Top-level block optimizer: pick the best complete block for a goal.

Given a target item and rate, this tries every applicable *complete-block*
generator, keeps the ones that are importable and meet the target, and returns
the tightest (smallest footprint). It is the single entrypoint the rest of the
pipeline (and eventually a Factorio-sim-scored search) plugs into.

Current strategies, in rough preference order:

* ``compact`` -- :func:`factopt.mvp.synthesize`, the tight shared-lane generator.
  Small footprint but only handles 2-level single-lane chains (green circuits,
  red science).
* ``line`` -- :func:`factopt.placement.line.synthesize_line`, ordering-driven
  band stacking with the tightest routable gaps.
* ``bus`` -- :func:`factopt.bus.synthesize_bus`, the general band+A*-router
  generator. Handles arbitrary trees (e.g. green science) and always emits a
  complete block, but is looser.
* ``benders`` -- :func:`factopt.loop.optimize_loop`, the general-purpose
  master-placement + coarse-routing + detailed-routing cut loop. The most
  general strategy; slower (CP-SAT master per iteration), so it gets a time
  budget.
* ``dense`` -- the same Benders loop with ``fuse=True``: a fusable 2-level chain
  (e.g. green circuits) is packed as one dense **direct-insertion** cell (the
  intermediate is inserted machine-to-machine, never belted) with only its raws
  and product routed as block boundary I/O. This is the first strategy that
  emits direct insertion inside the general place-and-route pipeline.

The remaining dense flow-coupled placers (:mod:`factopt.placement.flow` /
``belt``) are still not candidates here: they produce tight *interior*
placements but do not route block boundary I/O, so they aren't importable
factories on their own.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from factopt.bus import synthesize_bus
from factopt.data.database import Database
from factopt.mvp import synthesize as _mvp_synthesize
from factopt.placement.line import synthesize_line
from factopt.ratios.solver import ProductionPlan, solve_ratios

DEFAULT_STRATEGIES = ("compact", "line", "bus", "benders", "dense")


@dataclass
class Candidate:
    """One generator's attempt at a block (or why it couldn't produce one)."""

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


def _try_compact(target: str, rate: float, db: Database) -> Candidate:
    try:
        res = _mvp_synthesize(rate, db, target=target)
    except Exception as exc:
        return Candidate("compact", ok=False, detail=f"{type(exc).__name__}: {exc}")
    return Candidate(
        strategy="compact",
        ok=True,
        complete=True,
        meets_target=res.validation.meets_target,
        width=res.width,
        height=res.height,
        blueprint_string=res.blueprint_string,
        detail=f"{res.blocks} sub-block(s)",
    )


def _try_line(target: str, rate: float, db: Database) -> Candidate:
    try:
        res = synthesize_line(rate, db, target=target)
    except Exception as exc:
        return Candidate("line", ok=False, detail=f"{type(exc).__name__}: {exc}")
    return Candidate(
        strategy="line",
        ok=True,
        complete=res.complete,
        meets_target=res.complete,
        width=res.width,
        height=res.height,
        blueprint_string=res.blueprint_string,
        detail=f"unrouted={len(res.unrouted)}" if res.unrouted else "",
    )


def _try_bus(target: str, rate: float, db: Database) -> Candidate:
    try:
        res = synthesize_bus(rate, db, target=target)
    except Exception as exc:
        return Candidate("bus", ok=False, detail=f"{type(exc).__name__}: {exc}")
    return Candidate(
        strategy="bus",
        ok=True,
        complete=res.complete,
        # A fully-routed bus block belts every flow sized to the plan, so it meets
        # the target analytically; unrouted nets mean it does not.
        meets_target=res.complete,
        width=res.width,
        height=res.height,
        blueprint_string=res.blueprint_string,
        detail=f"unrouted={len(res.unrouted)}" if res.unrouted else "",
    )


def _try_loop(
    strategy: str, target: str, rate: float, db: Database, budget_s: float, fuse: bool
) -> Candidate:
    from factopt.loop import optimize_loop

    try:
        res = optimize_loop(
            target, rate, db, time_budget_s=budget_s, master_time_limit_s=15.0, fuse=fuse
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
) -> OptimizedBlock:
    """Return the tightest complete, target-meeting block for ``rate``/s of
    ``target``, trying every applicable generator."""
    if rate <= 0:
        raise ValueError("rate must be positive")
    plan = solve_ratios(target, rate, db)

    tries = {
        "compact": lambda: _try_compact(target, rate, db),
        "line": lambda: _try_line(target, rate, db),
        "bus": lambda: _try_bus(target, rate, db),
        "benders": lambda: _try_loop("benders", target, rate, db, benders_budget_s, False),
        "dense": lambda: _try_loop("dense", target, rate, db, benders_budget_s, True),
    }
    candidates = [tries[s]() for s in strategies if s in tries]

    usable = [c for c in candidates if c.usable]
    best = min(usable, key=lambda c: c.area) if usable else None
    return OptimizedBlock(
        target=target, rate=rate, plan=plan, best=best, candidates=candidates
    )
