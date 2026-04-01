"""Convex and classical portfolio optimizers."""

from __future__ import annotations

from typing import Any, Dict, Optional

import cvxpy as cp
import numpy as np
from scipy.optimize import minimize

RISK_FREE_DEFAULT = 0.045

_SOLVERS_QP = (cp.OSQP, cp.SCS, cp.ECOS)


def _symmetrize_sigma(Sigma: np.ndarray) -> np.ndarray:
    s = np.asarray(Sigma, dtype=float)
    return (s + s.T) / 2.0


def _portfolio_metrics(
    w: np.ndarray,
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float = RISK_FREE_DEFAULT,
) -> Dict[str, Any]:
    pr = float(mu @ w)
    var = float(w @ Sigma @ w)
    vol = float(np.sqrt(max(var, 0.0)))
    sharpe = (pr - rf) / max(vol, 1e-12)
    return {
        "weights": w,
        "portfolio_return": pr,
        "portfolio_variance": var,
        "portfolio_volatility": vol,
        "sharpe_ratio": sharpe,
    }


def _solve_qp(
    problem: cp.Problem,
    return_constraint: Any,
    budget_constraint: Any,
) -> tuple[str, Optional[Dict[str, np.ndarray]]]:
    last_status = "not_solved"
    dual_values: Optional[Dict[str, np.ndarray]] = None
    for solver in _SOLVERS_QP:
        try:
            problem.solve(solver=solver, verbose=False)
            last_status = str(problem.status)
            if problem.status in ("optimal", "optimal_inaccurate"):
                lam = np.asarray(return_constraint.dual_value).ravel()
                nu = np.asarray(budget_constraint.dual_value).ravel()
                dual_values = {"return": lam, "budget": nu}
                break
        except Exception:
            continue
    return last_status, dual_values


def solve_min_variance_qp(
    mu: np.ndarray,
    Sigma: np.ndarray,
    target_return: float,
    allow_short: bool = False,
    rf: float = RISK_FREE_DEFAULT,
) -> Optional[Dict[str, Any]]:
    """
    Minimise portfolio variance subject to target return and budget (and optional long-only).
    """
    Sigma = _symmetrize_sigma(Sigma)
    n = len(mu)
    w = cp.Variable(n)
    constraints = [
        mu @ w == target_return,
        cp.sum(w) == 1,
    ]
    if not allow_short:
        constraints.append(w >= 0)
    prob = cp.Problem(cp.Minimize(cp.quad_form(w, Sigma)), constraints)
    ret_c, bud_c = constraints[0], constraints[1]
    status, dual_values = _solve_qp(prob, ret_c, bud_c)

    if prob.status not in ("optimal", "optimal_inaccurate") or w.value is None:
        return None

    if dual_values is not None and (not allow_short) and len(constraints) > 2:
        try:
            nn = np.asarray(constraints[2].dual_value, dtype=float).ravel()
            dual_values["nonneg"] = nn
        except Exception:
            dual_values["nonneg"] = None

    wv = np.asarray(w.value).ravel()
    out = _portfolio_metrics(wv, mu, Sigma, rf=rf)
    out["status"] = status
    out["dual_values"] = dual_values
    return out


def solve_max_sharpe(
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float = RISK_FREE_DEFAULT,
) -> Optional[Dict[str, Any]]:
    """
    Maximum Sharpe ratio portfolio (long-only, fully invested) via SLSQP.
    """
    Sigma = _symmetrize_sigma(Sigma)
    n = len(mu)

    def neg_sharpe(wv: np.ndarray) -> float:
        wv = np.asarray(wv, dtype=float)
        pr = float(mu @ wv)
        var = float(wv @ Sigma @ wv)
        vol = float(np.sqrt(max(var, 0.0)))
        return -((pr - rf) / max(vol, 1e-12))

    cons = [{"type": "eq", "fun": lambda wv: float(np.sum(wv) - 1.0)}]
    bounds = [(0.0, 1.0)] * n
    x0 = np.ones(n) / n
    res = minimize(
        neg_sharpe,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 500, "ftol": 1e-12},
    )
    if not res.success or res.x is None:
        return None
    wv = np.asarray(res.x, dtype=float)
    wv = wv / max(np.sum(wv), 1e-12)
    out = _portfolio_metrics(wv, mu, Sigma, rf=rf)
    out["status"] = str(res.message)
    out["dual_values"] = None
    return out


def solve_equal_weight(
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float = RISK_FREE_DEFAULT,
) -> Dict[str, Any]:
    """Equal-weight 1/N portfolio."""
    Sigma = _symmetrize_sigma(Sigma)
    n = len(mu)
    wv = np.ones(n) / n
    out = _portfolio_metrics(wv, mu, Sigma, rf=rf)
    out["status"] = "analytical"
    out["dual_values"] = None
    return out


def solve_min_variance_unconstrained(
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float = RISK_FREE_DEFAULT,
) -> Optional[Dict[str, Any]]:
    """
    Global minimum variance on the simplex (long-only, fully invested).
    """
    Sigma = _symmetrize_sigma(Sigma)
    n = len(mu)
    w = cp.Variable(n)
    constraints = [cp.sum(w) == 1, w >= 0]
    prob = cp.Problem(cp.Minimize(cp.quad_form(w, Sigma)), constraints)
    last_status = "not_solved"
    for solver in _SOLVERS_QP:
        try:
            prob.solve(solver=solver, verbose=False)
            last_status = str(prob.status)
            if prob.status in ("optimal", "optimal_inaccurate"):
                break
        except Exception:
            continue
    if prob.status not in ("optimal", "optimal_inaccurate") or w.value is None:
        return None
    wv = np.asarray(w.value).ravel()
    out = _portfolio_metrics(wv, mu, Sigma, rf=rf)
    out["status"] = last_status
    out["dual_values"] = None
    return out
