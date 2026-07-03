"""CP-SAT implementation of the master-problem :class:`MasterModel` facade.

A thin passthrough over ``ortools.sat.python.cp_model``: every facade op maps
directly to a native CP-SAT global, so this backend reproduces the original
model exactly (and remains the default).
"""

from __future__ import annotations

from typing import Any, Iterable

from ortools.sat.python import cp_model

from factopt.master.backend.base import Lit, MasterModel, Sense, Solution, Var


class _CpSatSolution(Solution):
    def __init__(self, solver: cp_model.CpSolver, status: str):
        self._solver = solver
        self.status = status

    def value(self, var: Var) -> int:
        return self._solver.value(var)


class CpSatModel(MasterModel):
    def __init__(self) -> None:
        self._m = cp_model.CpModel()

    def new_int_var(self, lo: int, hi: int, name: str) -> Var:
        return self._m.new_int_var(lo, hi, name)

    def new_bool_var(self, name: str) -> Var:
        return self._m.new_bool_var(name)

    def add(self, constraint: Any) -> None:
        self._m.add(constraint)

    def add_exactly_one(self, lits: Iterable[Lit]) -> None:
        self._m.add_exactly_one(list(lits))

    def add_bool_or(self, lits: Iterable[Lit]) -> None:
        self._m.add_bool_or(list(lits))

    def neg(self, lit: Lit) -> Lit:
        return lit.Not()

    def _cons(self, lhs: Any, sense: Sense, rhs: Any):
        if sense == "<=":
            return lhs <= rhs
        if sense == ">=":
            return lhs >= rhs
        if sense == "==":
            return lhs == rhs
        if sense == "!=":
            return lhs != rhs
        raise ValueError(f"bad sense {sense!r}")

    def enforce(self, lit: Lit, lhs: Any, sense: Sense, rhs: Any) -> None:
        self._m.add(self._cons(lhs, sense, rhs)).only_enforce_if(lit)

    def is_ne(self, expr: Any, value: int, name: str) -> Lit:
        b = self._m.new_bool_var(name)
        self._m.add(expr != value).only_enforce_if(b)
        self._m.add(expr == value).only_enforce_if(b.Not())
        return b

    def add_multiplication_equality(self, target: Var, factors: list[Var]) -> None:
        self._m.add_multiplication_equality(target, factors)

    def add_min_equality(self, target: Var, exprs: list[Any]) -> None:
        self._m.add_min_equality(target, exprs)

    def add_max_equality(self, target: Var, exprs: list[Any]) -> None:
        self._m.add_max_equality(target, exprs)

    def add_division_equality(self, target: Var, num: Any, denom: int) -> None:
        self._m.add_division_equality(target, num, denom)

    def add_map_domain(self, idx: Var, lits: list[Lit]) -> None:
        self._m.add_map_domain(idx, lits)

    def add_no_overlap(self, rects: list[tuple[Var, Any, Var, Any]]) -> None:
        xi, yi = [], []
        for i, (x, xs, y, ys) in enumerate(rects):
            xe = self._m.new_int_var(0, cp_model.INT32_MAX // 2, f"xe_{i}")
            ye = self._m.new_int_var(0, cp_model.INT32_MAX // 2, f"ye_{i}")
            self._m.add(xe == x + xs)
            self._m.add(ye == y + ys)
            xi.append(self._m.new_interval_var(x, xs, xe, f"xi_{i}"))
            yi.append(self._m.new_interval_var(y, ys, ye, f"yi_{i}"))
        self._m.add_no_overlap_2d(xi, yi)

    def minimize(self, expr: Any) -> None:
        self._m.minimize(expr)

    def clear_objective(self) -> None:
        self._m.clear_objective()

    def solve(self, time_limit_s: float, workers: int) -> Solution:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_s
        solver.parameters.num_workers = workers
        status = solver.solve(self._m)
        return _CpSatSolution(solver, solver.status_name(status))
