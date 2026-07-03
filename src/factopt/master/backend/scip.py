"""SCIP implementation of the master-problem :class:`MasterModel` facade.

CP-SAT expresses this model with native global constraints; SCIP is a
MILP/MINLP solver, so every non-linear op is reformulated here once and the
model-building code stays solver-agnostic:

* **no-overlap** -> pairwise big-M disjunction of the four separations;
* **reified linear** (``enforce``) -> big-M using each expression's known
  integer bounds; ``!=`` uses an auxiliary "side" binary;
* **bool*bool / bool*int products** -> exact McCormick (no big-M needed);
* **bilinear ``area = w*h``** -> a native non-linear constraint (nonconvex
  QCP, solved by SCIP's spatial branch-and-bound);
* **min/max equality** -> selector-binary linearization;
* **division / map_domain** -> exact linear encodings.

Two-stage lexicographic solving re-optimizes the same model: after a solve the
model is in a transformed state, so any further edit calls ``freeTransform``
first. Each :meth:`solve` snapshots variable values, so both stages' solutions
can be read independently (mirroring CP-SAT's two solver objects).
"""

from __future__ import annotations

from typing import Any, Iterable

from pyscipopt import Model, Variable, quicksum

from factopt.master.backend.base import Lit, MasterModel, NegLit, Sense, Solution, Var


class _ScipSolution(Solution):
    def __init__(self, snapshot: dict[str, int], status: str):
        self._snap = snapshot
        self.status = status

    def value(self, var: Var) -> int:
        # PySCIPOpt Variables are unhashable, so snapshots are keyed by name.
        return self._snap.get(var.name, 0)


class ScipModel(MasterModel):
    def __init__(self) -> None:
        self._m = Model()
        self._m.hideOutput(True)
        # PySCIPOpt Variables overload comparison operators and so are
        # unhashable; track everything by the (unique) variable name.
        self._lb: dict[str, float] = {}
        self._ub: dict[str, float] = {}
        self._bool: set[str] = set()
        self._vars: list[Variable] = []
        self._transformed = False
        self._n = 0  # unique-name counter

    # -- infrastructure ----------------------------------------------------
    def _fresh(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}_{self._n}"

    def _editable(self) -> None:
        if self._transformed:
            self._m.freeTransform()
            self._transformed = False

    def _addcons(self, cons: Any) -> None:
        self._editable()
        self._m.addCons(cons)

    def _bounds(self, e: Any) -> tuple[float, float]:
        """Lower/upper bound of a constant, variable, or linear expression,
        from the tracked variable domains."""
        if isinstance(e, (int, float)):
            return float(e), float(e)
        expr = e + 0  # coerce Variable/Expr -> Expr with a .terms mapping
        lo = hi = 0.0
        for term, coef in expr.terms.items():
            vs = term.vartuple
            if not vs:
                lo += coef
                hi += coef
            elif len(vs) == 1:
                a, b = self._lb[vs[0].name], self._ub[vs[0].name]
                if coef >= 0:
                    lo += coef * a
                    hi += coef * b
                else:
                    lo += coef * b
                    hi += coef * a
            else:
                raise ValueError("non-linear expression has no linear bounds")
        return lo, hi

    # -- variables ---------------------------------------------------------
    def new_int_var(self, lo: int, hi: int, name: str) -> Var:
        v = self._m.addVar(name=self._fresh(name), vtype="I", lb=lo, ub=hi)
        self._lb[v.name], self._ub[v.name] = lo, hi
        self._vars.append(v)
        return v

    def new_bool_var(self, name: str) -> Var:
        v = self._m.addVar(name=self._fresh(name), vtype="B", lb=0, ub=1)
        self._lb[v.name], self._ub[v.name] = 0, 1
        self._bool.add(v.name)
        self._vars.append(v)
        return v

    # -- literals ----------------------------------------------------------
    def neg(self, lit: Lit) -> Lit:
        if isinstance(lit, NegLit):
            return lit.var
        return NegLit(lit)

    def _lit_expr(self, lit: Lit) -> Any:
        """A 0/1 expression for a literal."""
        if isinstance(lit, NegLit):
            return 1 - lit.var
        return lit

    # -- linear constraints ------------------------------------------------
    def add(self, constraint: Any) -> None:
        self._addcons(constraint)

    def add_exactly_one(self, lits: Iterable[Lit]) -> None:
        self._addcons(quicksum(self._lit_expr(x) for x in lits) == 1)

    def add_bool_or(self, lits: Iterable[Lit]) -> None:
        self._addcons(quicksum(self._lit_expr(x) for x in lits) >= 1)

    # -- reified / conditional --------------------------------------------
    def enforce(self, lit: Lit, lhs: Any, sense: Sense, rhs: Any) -> None:
        le = self._lit_expr(lit)
        D = lhs - rhs
        dlo, dhi = self._bounds(D)
        if sense == "<=":
            self._addcons(D <= dhi * (1 - le))
        elif sense == ">=":
            self._addcons(D >= dlo * (1 - le))
        elif sense == "==":
            self._addcons(D <= dhi * (1 - le))
            self._addcons(D >= dlo * (1 - le))
        elif sense == "!=":
            self._ne(D, dlo, dhi, le)
        else:
            raise ValueError(f"bad sense {sense!r}")

    def _ne(self, D: Any, dlo: float, dhi: float, le: Any) -> None:
        """Enforce ``D != 0`` when ``le`` (a 0/1 expression) is 1, via a side
        binary picking which strict side (D <= -1 or D >= 1) holds."""
        s = self.new_bool_var("ne_side")
        big1 = max(dhi + 1.0, 1.0)
        big2 = max(1.0 - dlo, 1.0)
        # le=1,s=0 -> D<=-1 ; otherwise relaxed.
        self._addcons(D <= -1 + big1 * ((1 - le) + s))
        # le=1,s=1 -> D>=1 ; otherwise relaxed.
        self._addcons(D >= 1 - big2 * ((1 - le) + (1 - s)))

    def is_ne(self, expr: Any, value: int, name: str) -> Lit:
        b = self.new_bool_var(name)
        D = expr - value
        dlo, dhi = self._bounds(D)
        # b=0 -> D==0.
        self._addcons(D <= dhi * b)
        self._addcons(D >= dlo * b)
        # b=1 -> D!=0.
        self._ne(D, dlo, dhi, b)
        return b

    # -- products ----------------------------------------------------------
    def add_multiplication_equality(self, target: Var, factors: list[Var]) -> None:
        a, b = factors
        a_bool, b_bool = a.name in self._bool, b.name in self._bool
        if a_bool and b_bool:
            self._addcons(target <= a)
            self._addcons(target <= b)
            self._addcons(target >= a + b - 1)
        elif a_bool or b_bool:
            bit, iv = (a, b) if a_bool else (b, a)
            ub = self._ub[iv.name]
            self._addcons(target <= ub * bit)
            self._addcons(target <= iv)
            self._addcons(target >= iv - ub * (1 - bit))
        else:
            # Bilinear: SCIP handles the nonconvex product natively.
            self._addcons(target == a * b)

    # -- min / max ---------------------------------------------------------
    def add_max_equality(self, target: Var, exprs: list[Any]) -> None:
        _, thi = self._bounds(target)
        sels = [self.new_bool_var("maxsel") for _ in exprs]
        self._addcons(quicksum(sels) == 1)
        for e, sel in zip(exprs, sels):
            elo, _ = self._bounds(e)
            m = max(thi - elo, 0.0) + 1.0
            self._addcons(target >= e)
            self._addcons(target <= e + m * (1 - sel))

    def add_min_equality(self, target: Var, exprs: list[Any]) -> None:
        tlo, _ = self._bounds(target)
        sels = [self.new_bool_var("minsel") for _ in exprs]
        self._addcons(quicksum(sels) == 1)
        for e, sel in zip(exprs, sels):
            _, ehi = self._bounds(e)
            m = max(ehi - tlo, 0.0) + 1.0
            self._addcons(target <= e)
            self._addcons(target >= e - m * (1 - sel))

    # -- misc encodings ----------------------------------------------------
    def add_division_equality(self, target: Var, num: Any, denom: int) -> None:
        self._addcons(denom * target <= num)
        self._addcons(num <= denom * target + (denom - 1))

    def add_map_domain(self, idx: Var, lits: list[Lit]) -> None:
        exprs = [self._lit_expr(x) for x in lits]
        self._addcons(quicksum(exprs) == 1)
        self._addcons(idx == quicksum(i * e for i, e in enumerate(exprs)))

    def add_no_overlap(self, rects: list[tuple[Var, Any, Var, Any]]) -> None:
        for i in range(len(rects)):
            xi, xsi, yi, ysi = rects[i]
            for j in range(i + 1, len(rects)):
                xj, xsj, yj, ysj = rects[j]
                b = [self.new_bool_var("sep") for _ in range(4)]
                self._addcons(quicksum(b) >= 1)
                self.enforce(b[0], xi + xsi, "<=", xj)
                self.enforce(b[1], xj + xsj, "<=", xi)
                self.enforce(b[2], yi + ysi, "<=", yj)
                self.enforce(b[3], yj + ysj, "<=", yi)

    # -- objective + solve -------------------------------------------------
    def minimize(self, expr: Any) -> None:
        self._editable()
        self._m.setObjective(expr, "minimize")

    def clear_objective(self) -> None:
        self._editable()
        self._m.setObjective(0.0, "minimize")

    def solve(self, time_limit_s: float, workers: int) -> Solution:
        # SCIP's parallelism is limited (no CP-SAT-style worker portfolio);
        # ``workers`` is intentionally unused. Solve single-threaded.
        self._editable()
        self._m.setParam("limits/time", time_limit_s)
        self._m.optimize()
        self._transformed = True
        status = self._status()
        snap: dict[str, int] = {}
        if self._m.getNSols() > 0:
            best = self._m.getBestSol()
            for v in self._vars:
                snap[v.name] = int(round(self._m.getSolVal(best, v)))
        return _ScipSolution(snap, status)

    def _status(self) -> str:
        st = self._m.getStatus()
        if st == "optimal":
            return "OPTIMAL"
        if st == "infeasible":
            return "INFEASIBLE"
        if self._m.getNSols() > 0:
            return "FEASIBLE"
        return "UNKNOWN"
