"""Mixed-integer portfolio: limit number of active assets."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, Optional

import cvxpy as cp
import numpy as np

from src.optimizer import RISK_FREE_DEFAULT, _portfolio_metrics, _symmetrize_sigma, solve_min_variance_qp

_SOLVERS_MIP = (cp.GLPK_MI, cp.ECOS_BB)


def _enumerate_mip(
    mu: np.ndarray,
    Sigma: np.ndarray,
    target_return: float,
    max_assets: int,
    rf: float,
) -> Optional[Dict[str, Any]]:
    """
    Exact fallback for n=3: try every subset of size <= max_assets, solve reduced QP.
    """
    n = len(mu)
    best: Optional[Dict[str, Any]] = None
    best_var = float("inf")
    for k in range(1, max_assets + 1):
        for subset in combinations(range(n), k):
            idx = list(subset)
            mu_s = mu[idx]
            Sigma_s = Sigma[np.ix_(idx, idx)]
            sol = solve_min_variance_qp(
                mu_s, Sigma_s, target_return, allow_short=False, rf=rf
            )
            if sol is None:
                continue
            w_full = np.zeros(n, dtype=float)
            w_full[idx] = sol["weights"]
            var = float(w_full @ Sigma @ w_full)
            if var < best_var:
                best_var = var
                out = _portfolio_metrics(w_full, mu, Sigma, rf=rf)
                out["status"] = "optimal_enumeration"
                out["dual_values"] = None
                out["binary_z"] = (np.abs(w_full) > 1e-8).astype(float)
                best = out
    if best is not None:
        selected = [i for i in range(n) if best["binary_z"][i] > 0.5]
        print(f"[mip_optimizer] Enumeration fallback: selected indices: {selected}")
    else:
        print("[mip_optimizer] Enumeration fallback found no feasible subset.")
    return best


def solve_mip_portfolio(
    mu: np.ndarray,
    Sigma: np.ndarray,
    target_return: float,
    max_assets: int = 2,
    rf: float = RISK_FREE_DEFAULT,
) -> Optional[Dict[str, Any]]:
    """
    Minimise variance with at most ``max_assets`` names held (binary selection).

    Tries CVXPY MIP solvers first; if unavailable, uses exact enumeration (feasible for n=3).
    """
    Sigma = _symmetrize_sigma(Sigma)
    n = len(mu)
    w = cp.Variable(n)
    z = cp.Variable(n, boolean=True)
    constraints = [
        cp.sum(w) == 1,
        mu @ w == target_return,
        w >= 0,
        w <= z,
        cp.sum(z) <= max_assets,
    ]
    prob = cp.Problem(cp.Minimize(cp.quad_form(w, Sigma)), constraints)

    last_status = "not_solved"
    solved = False
    for solver in _SOLVERS_MIP:
        try:
            prob.solve(solver=solver, verbose=False)
            last_status = str(prob.status)
            if prob.status in ("optimal", "optimal_inaccurate"):
                solved = True
                break
        except Exception as exc:
            print(f"[mip_optimizer] Solver {solver} failed: {exc}")
            continue

    if (
        solved
        and prob.status in ("optimal", "optimal_inaccurate")
        and w.value is not None
        and z.value is not None
    ):
        wv = np.asarray(w.value, dtype=float).ravel()
        zv = np.asarray(z.value, dtype=float).ravel()
        selected = [i for i in range(n) if zv[i] > 0.5]
        print(f"[mip_optimizer] Selected asset indices (0-based): {selected}")
        out = _portfolio_metrics(wv, mu, Sigma, rf=rf)
        out["status"] = last_status
        out["dual_values"] = None
        out["binary_z"] = zv
        return out

    print("[mip_optimizer] MIP solvers unavailable or failed; using enumeration fallback.")
    return _enumerate_mip(mu, Sigma, target_return, max_assets, rf)
