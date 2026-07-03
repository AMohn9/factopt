"""Solver-backend facade for the master problem.

The master model (:mod:`factopt.master.model`, :mod:`.coarse`, :mod:`.cuts`)
is built against this thin interface instead of a concrete solver, so the same
model can be solved with either CP-SAT (:class:`~factopt.master.backend.cpsat.CpSatModel`,
the default) or SCIP (:class:`~factopt.master.backend.scip.ScipModel`).

The op set below is exactly what the three master modules use. Constructs that
CP-SAT expresses as native globals (no-overlap, min/max/division equality,
reified constraints, boolean products) are linearized inside the SCIP backend,
so the model-building code stays solver-agnostic.

Expressions are built with native operators on the variables a backend hands
out (``+``, ``-``, ``*`` by a constant, ``sum(...)``, and comparisons), which
both CP-SAT and PySCIPOpt support. The two operations that do *not* map to a
neutral operator -- reified enforcement and integer ``!=`` -- have dedicated
methods (:meth:`MasterModel.enforce`, :meth:`MasterModel.is_ne`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, Literal

# A "variable" or "expression" is whatever the concrete backend produces; the
# shared model code only ever combines them with native Python operators.
Var = Any
Expr = Any
# A boolean literal: a backend bool var, or its negation via :meth:`neg`.
Lit = Any
Sense = Literal["==", "<=", ">=", "!="]


@dataclass
class NegLit:
    """A negated boolean literal (used by backends without native negation)."""

    var: Any


class Solution(ABC):
    """Read-only view of one solve's result (snapshotted so two lexicographic
    solves can each be inspected independently)."""

    status: str  # "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "UNKNOWN" | ...

    @property
    def ok(self) -> bool:
        return self.status in ("OPTIMAL", "FEASIBLE")

    @abstractmethod
    def value(self, var: Var) -> int:
        """Integer value of ``var`` in this solution."""


class MasterModel(ABC):
    """Facade over a MILP/CP solver for the master placement problem."""

    # -- variables ---------------------------------------------------------
    @abstractmethod
    def new_int_var(self, lo: int, hi: int, name: str) -> Var: ...

    @abstractmethod
    def new_bool_var(self, name: str) -> Var: ...

    # -- linear constraints ------------------------------------------------
    @abstractmethod
    def add(self, constraint: Any) -> None:
        """Add an unconditional constraint built with native operators
        (``<=``, ``>=``, ``==``)."""

    @abstractmethod
    def add_exactly_one(self, lits: Iterable[Lit]) -> None: ...

    @abstractmethod
    def add_bool_or(self, lits: Iterable[Lit]) -> None: ...

    # -- literals ----------------------------------------------------------
    @abstractmethod
    def neg(self, lit: Lit) -> Lit:
        """The negation of a boolean literal."""

    # -- reified / conditional --------------------------------------------
    @abstractmethod
    def enforce(self, lit: Lit, lhs: Expr, sense: Sense, rhs: Expr) -> None:
        """Enforce ``lhs sense rhs`` only when ``lit`` is true."""

    @abstractmethod
    def is_ne(self, expr: Expr, value: int, name: str) -> Lit:
        """A fresh boolean that is true iff ``expr != value``."""

    # -- non-linear / global helpers --------------------------------------
    @abstractmethod
    def add_multiplication_equality(self, target: Var, factors: list[Var]) -> None:
        """``target == factors[0] * factors[1]`` (bool*bool, bool*int, or the
        bilinear int*int used for the bounding-box area objective)."""

    @abstractmethod
    def add_min_equality(self, target: Var, exprs: list[Expr]) -> None: ...

    @abstractmethod
    def add_max_equality(self, target: Var, exprs: list[Expr]) -> None: ...

    @abstractmethod
    def add_division_equality(self, target: Var, num: Expr, denom: int) -> None:
        """``target == num // denom`` for a positive constant ``denom``."""

    @abstractmethod
    def add_map_domain(self, idx: Var, lits: list[Lit]) -> None:
        """``lits[i]`` is true iff ``idx == i`` (an indicator channel)."""

    @abstractmethod
    def add_no_overlap(self, rects: list[tuple[Var, Expr, Var, Expr]]) -> None:
        """Pairwise 2D no-overlap of ``(x, x_size, y, y_size)`` rectangles.
        Sizes already include any routing margin."""

    # -- objective + solve -------------------------------------------------
    @abstractmethod
    def minimize(self, expr: Expr) -> None: ...

    @abstractmethod
    def clear_objective(self) -> None: ...

    @abstractmethod
    def solve(self, time_limit_s: float, workers: int) -> Solution: ...
