#!/usr/bin/env python3
"""Run the Benders loop (Steiner-tree routing) for a target and write the
candidate blueprint, markdown report, and debug SVG.

A thin, reusable wrapper around :func:`factopt.loop.optimize_loop` for
footprint experiments -- e.g. sweeping the master time limit / iteration count
and comparing bounding boxes across runs.

Examples
--------
    python scripts/steiner_run.py green-science-steiner-1ps
    python scripts/steiner_run.py gs-fast --master-s 30 --iters 20
    python scripts/steiner_run.py red-science --target automation-science-pack
"""

from __future__ import annotations

import argparse
import time

from factopt.data import vanilla
from factopt.loop import optimize_loop
from factopt.report import write_candidate


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("name", help="output basename under --out-dir")
    p.add_argument("--target", default="logistic-science-pack", help="item to produce")
    p.add_argument("--rate", type=float, default=1.0, help="items per second")
    p.add_argument("--master-s", type=float, default=60.0,
                   help="CP-SAT time limit per master solve (seconds)")
    p.add_argument("--iters", type=int, default=15, help="max Benders iterations")
    p.add_argument("--budget", type=float, default=600.0,
                   help="total wall-clock budget (seconds)")
    p.add_argument("--no-fuse", dest="fuse", action="store_false",
                   help="disable dense direct-insertion fusion")
    p.add_argument("--backend", default="cpsat", choices=("cpsat", "scip"),
                   help="master solver engine")
    p.add_argument("--out-dir", default="blueprints/dense", help="artifact directory")
    args = p.parse_args()

    t = time.time()
    res = optimize_loop(
        args.target,
        args.rate,
        vanilla.DB,
        fuse=args.fuse,
        max_iterations=args.iters,
        master_time_limit_s=args.master_s,
        time_budget_s=args.budget,
        label=args.name,
        backend=args.backend,
    )
    print(f"feasible={res.feasible} in {time.time() - t:.0f}s")

    b = res.best
    if b is None:
        print(res.summary())
        return 1

    m = b.routing.metrics
    print(
        f"bbox {b.width}x{b.height}={b.area}t ok={b.validation.ok} "
        f"belts={m.total_belt_length} splitters={m.total_splitters} "
        f"ug={m.total_undergrounds} turns={m.total_turns}"
    )
    reversed_lanes = [
        f"{mid}.{pid}"
        for mid, pm in b.master.placements.items()
        for pid, chosen in pm.port_choice.items()
        if chosen
    ]
    print("reversed input lanes:", ", ".join(reversed_lanes) or "(none)")

    paths = write_candidate(res, args.out_dir, args.name)
    print("wrote:", {k: str(v) for k, v in paths.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
