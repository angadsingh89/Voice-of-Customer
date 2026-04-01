"""KKT stationarity checks for equality-constrained QP portfolios."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate


def _apply_plot_style() -> None:
    for style in ("seaborn-v0_8-whitegrid", "seaborn-whitegrid", "ggplot"):
        try:
            plt.style.use(style)
            return
        except OSError:
            continue
    plt.style.use("default")


def _flatten_dual(d: Any) -> float:
    a = np.asarray(d, dtype=float).ravel()
    if a.size == 0:
        return 0.0
    return float(a.flat[0])


def run_kkt_analysis(
    mu: np.ndarray,
    Sigma: np.ndarray,
    optimal_weights: np.ndarray,
    dual_values: Optional[Dict[str, np.ndarray]],
    threshold: float = 1e-4,
    save_path: str | None = None,
    asset_names: list[str] | None = None,
) -> bool:
    """
    Verify stationarity for min-variance QP: 2 Sigma w ≈ λ μ + ν 1 (sign may follow CVXPY).

    If ``dual_values`` is None, prints a message and returns False.
    """
    if dual_values is None:
        print("[kkt_analysis] No dual values supplied; skipping KKT check.")
        return False

    w = np.asarray(optimal_weights, dtype=float).ravel()
    n = len(w)
    lam = _flatten_dual(dual_values.get("return"))
    nu = _flatten_dual(dual_values.get("budget"))
    ones = np.ones(n)
    gam = dual_values.get("nonneg")
    if gam is not None:
        gam = np.asarray(gam, dtype=float).ravel()
        if gam.size != n:
            gam = None

    lhs = 2 * (Sigma @ w)

    candidates = [
        ("lambda*mu + nu*1", lam * mu + nu * ones),
        ("-(lambda*mu + nu*1)", -(lam * mu + nu * ones)),
        ("-lambda*mu - nu*1", -lam * mu - nu * ones),
    ]
    if gam is not None:
        candidates.extend(
            [
                ("lambda*mu + nu*1 + nonneg", lam * mu + nu * ones + gam),
                ("-(lambda*mu + nu*1 + nonneg)", -(lam * mu + nu * ones + gam)),
                ("lambda*mu + nu*1 - nonneg", lam * mu + nu * ones - gam),
                ("-(lambda*mu + nu*1 - nonneg)", -(lam * mu + nu * ones - gam)),
                ("-(lambda*mu + nu*1) + nonneg", -(lam * mu + nu * ones) + gam),
                ("-(lambda*mu + nu*1) - nonneg", -(lam * mu + nu * ones) - gam),
            ]
        )
    best_label = candidates[0][0]
    best_rhs = candidates[0][1]
    best_res = lhs - best_rhs
    best_max = float(np.max(np.abs(best_res)))
    for label, rhs in candidates[1:]:
        res = lhs - rhs
        m = float(np.max(np.abs(res)))
        if m < best_max:
            best_max = m
            best_label = label
            best_rhs = rhs
            best_res = res

    print("\n[kkt_analysis] Stationarity check (best matching RHS form):", best_label)
    rows = []
    if asset_names is None or len(asset_names) != n:
        names = [f"Asset {i}" for i in range(n)]
    else:
        names = list(asset_names)
    for i in range(n):
        rows.append([names[i], lhs[i], best_rhs[i], best_res[i]])
    print(
        tabulate(
            rows,
            headers=["Asset", "LHS (2*Sigma*w)", "RHS", "Residual"],
            floatfmt=".6f",
            tablefmt="github",
        )
    )
    print(f"\n[kkt_analysis] Max |residual| = {best_max:.6e}")
    kkt_ok = best_max <= threshold
    print(
        f"[kkt_analysis] KKT stationarity (threshold {threshold:g}): "
        f"{'SATISFIED' if kkt_ok else 'NOT SATISFIED'}"
    )

    if save_path is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_path = os.path.join(root, "outputs", "kkt_verification.png")

    _apply_plot_style()
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(n)
    width = 0.35
    ax.bar(x - width / 2, lhs, width, label="LHS (2Σw)")
    ax.bar(x + width / 2, best_rhs, width, label=f"RHS ({best_label})")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("Value")
    ax.set_title("KKT stationarity: LHS vs RHS")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"[kkt_analysis] Saved figure -> {save_path}")

    return kkt_ok
