"""Pluggable solver backends for the master problem.

``make_model("cpsat")`` (the default) returns the CP-SAT passthrough;
``make_model("scip")`` returns the PySCIPOpt implementation. Both satisfy the
:class:`~factopt.master.backend.base.MasterModel` facade, so the placement,
coarse-routing, and cut model is written once and solved by either engine.
"""

from __future__ import annotations

from factopt.master.backend.base import MasterModel, NegLit, Solution

Backend = str  # "cpsat" | "scip"


def make_model(backend: Backend = "cpsat") -> MasterModel:
    if backend == "cpsat":
        from factopt.master.backend.cpsat import CpSatModel

        return CpSatModel()
    if backend == "scip":
        from factopt.master.backend.scip import ScipModel

        return ScipModel()
    raise ValueError(f"unknown master backend {backend!r} (use 'cpsat' or 'scip')")


__all__ = ["MasterModel", "NegLit", "Solution", "make_model", "Backend"]
