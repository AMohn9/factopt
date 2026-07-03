#!/usr/bin/env python3
"""Head-to-head master-solver benchmark: CP-SAT vs SCIP.

Runs the Benders loop for a target under each backend at matched budgets and
prints time-to-first-feasible, per-iteration master time, and final footprint.
This is the experiment behind the pluggable master backend
(:mod:`factopt.master.backend`).

Summary of the finding on green science 1/s (see ``--help`` to reproduce):
CP-SAT routes a complete block within a couple of minutes, while SCIP cannot
find even one feasible solution to the coarse-routing master within a 20s
per-solve limit -- the big-M / nonconvex reformulation of CP-SAT's global
constraints (no-overlap, Steiner flows, reified logic) is intractable for
branch-and-cut at this size. SCIP *does* solve placement-only (``--cell 0``),
but slower and only to a feasible (not proven-optimal) point.

Examples
--------
    python scripts/backend_bench.py                        # green science 1/s
    python scripts/backend_bench.py --cell 0               # placement only
    python scripts/backend_bench.py --backends scip --budget 300 --master-s 60
"""

from __future__ import annotations

import argparse
import time

from factopt.data import vanilla
from factopt.loop import optimize_loop


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", default="logistic-science-pack")
    p.add_argument("--rate", type=float, default=1.0)
    p.add_argument("--backends", nargs="+", default=["cpsat", "scip"],
                   choices=("cpsat", "scip"))
    p.add_argument("--master-s", type=float, default=20.0,
                   help="master time limit per solve (seconds)")
    p.add_argument("--budget", type=float, default=150.0,
                   help="total wall-clock budget per backend (seconds)")
    p.add_argument("--iters", type=int, default=6, help="max Benders iterations")
    p.add_argument("--cell", type=int, default=4,
                   help="coarse-routing cell size; 0 disables coarse routing")
    p.add_argument("--workers", type=int, default=None,
                   help="CP-SAT search portfolio size (default: all cores)")
    p.add_argument("--no-fuse", dest="fuse", action="store_false")
    args = p.parse_args()

    coarse_cell = args.cell if args.cell > 0 else None
    for be in args.backends:
        print("=" * 72)
        print(f"BACKEND: {be}   target={args.rate:g}/s {args.target}  "
              f"coarse_cell={coarse_cell}")
        t = time.time()
        res = optimize_loop(
            args.target, args.rate, vanilla.DB, fuse=args.fuse,
            max_iterations=args.iters, master_time_limit_s=args.master_s,
            time_budget_s=args.budget, coarse_cell=coarse_cell, backend=be,
            workers=args.workers,
        )
        elapsed = time.time() - t
        print(f"feasible={res.feasible}  elapsed={elapsed:.0f}s  "
              f"iters={len(res.iterations)}")
        if res.best is not None:
            b = res.best
            print(f"  best: {b.width}x{b.height}={b.area}t  valid={b.validation.ok}")
        print(res.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
