"""Efficient frontier generation and plots."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.optimizer import RISK_FREE_DEFAULT, solve_min_variance_qp, solve_min_variance_unconstrained

COLOR_GOLD = "#FFD700"
COLOR_SILVER = "#C0C0C0"
COLOR_COPPER = "#B87333"
ASSET_COLORS = [COLOR_GOLD, COLOR_SILVER, COLOR_COPPER]


def _apply_plot_style() -> None:
    for style in ("seaborn-v0_8-whitegrid", "seaborn-whitegrid", "ggplot"):
        try:
            plt.style.use(style)
            return
        except OSError:
            continue
    plt.style.use("default")


def _weight_column_names(asset_names: List[str]) -> List[str]:
    mapping = {"Gold": "w_Gold", "Silver": "w_Silver", "Copper": "w_Copper"}
    return [mapping.get(n, f"w_{n}") for n in asset_names]


def generate_efficient_frontier(
    mu: np.ndarray,
    Sigma: np.ndarray,
    asset_names: List[str],
    n_points: int = 150,
    rf: float = RISK_FREE_DEFAULT,
) -> pd.DataFrame:
    """
    Sweep target returns between global min-variance return and max asset return;
    solve min-variance QP at each point.
    """
    mv = solve_min_variance_unconstrained(mu, Sigma, rf=rf)
    if mv is None:
        raise RuntimeError("Could not solve global minimum variance portfolio.")
    r_min = float(mv["portfolio_return"])
    r_max = float(np.max(mu))
    if r_max <= r_min + 1e-10:
        r_max = r_min + 1e-6

    targets = np.linspace(r_min, r_max, n_points)
    rows = []
    for tr in targets:
        sol = solve_min_variance_qp(mu, Sigma, target_return=float(tr), allow_short=False, rf=rf)
        if sol is None:
            continue
        w = sol["weights"]
        row = {
            "volatility": sol["portfolio_volatility"],
            "portfolio_return": sol["portfolio_return"],
            "sharpe_ratio": sol["sharpe_ratio"],
        }
        wcols = _weight_column_names(asset_names)
        for i, wc in enumerate(wcols):
            row[wc] = float(w[i])
        rows.append(row)
    return pd.DataFrame(rows)


def plot_efficient_frontier(
    frontier_df: pd.DataFrame,
    special_portfolios: Dict[str, Any],
    asset_names: List[str],
    mu: np.ndarray,
    Sigma: np.ndarray,
    save_path: str,
    rf: float = RISK_FREE_DEFAULT,
) -> None:
    """
    Plot efficient frontier coloured by Sharpe, assets, special portfolios, and CML.
    """
    _apply_plot_style()
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(
        frontier_df["volatility"] * 100,
        frontier_df["portfolio_return"] * 100,
        c=frontier_df["sharpe_ratio"],
        cmap="viridis",
        s=28,
        zorder=2,
        label="Efficient frontier",
    )
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("Sharpe ratio")

    vols = np.sqrt(np.diag(Sigma))
    for i, name in enumerate(asset_names):
        ax.scatter(
            vols[i] * 100,
            mu[i] * 100,
            color=ASSET_COLORS[i % len(ASSET_COLORS)],
            s=80,
            marker="o",
            edgecolors="black",
            linewidths=0.5,
            zorder=4,
            label=name,
        )

    markers = {
        "min_variance": ("*", "blue", "Min variance"),
        "max_sharpe": ("*", "gold", "Max Sharpe"),
        "equal_weight": ("D", "green", "Equal weight"),
        "mip": ("s", "red", "MIP (≤2 assets)"),
    }
    for key, (mk, col, lab) in markers.items():
        if key not in special_portfolios or special_portfolios[key] is None:
            continue
        sp = special_portfolios[key]
        ax.scatter(
            sp["portfolio_volatility"] * 100,
            sp["portfolio_return"] * 100,
            marker=mk,
            color=col,
            s=160,
            edgecolors="black",
            linewidths=0.6,
            zorder=5,
            label=lab,
        )

    ms = special_portfolios.get("max_sharpe")
    if ms is not None:
        sig = float(ms["portfolio_volatility"])
        rp = float(ms["portfolio_return"])
        if sig > 1e-12:
            slope = (rp - rf) / sig
            v_line = np.linspace(0, max(frontier_df["volatility"].max(), sig) * 1.15, 100)
            r_line = rf + slope * v_line
            ax.plot(v_line * 100, r_line * 100, "k--", linewidth=1.2, label="Capital market line", zorder=1)
        ax.scatter([0], [rf * 100], color="black", marker="o", s=40, zorder=5, label="Risk-free (4.5%)")

    ax.set_xlabel("Annualised volatility (%)")
    ax.set_ylabel("Annualised expected return (%)")
    ax.set_title("Mean–variance efficient frontier (Gold, Silver, Copper)")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def plot_weight_composition(
    frontier_df: pd.DataFrame,
    asset_names: List[str],
    save_path: str,
) -> None:
    """Stacked area of frontier weights vs portfolio return."""
    _apply_plot_style()
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    wcols = _weight_column_names(asset_names)
    x = frontier_df["portfolio_return"].values * 100
    fig, ax = plt.subplots(figsize=(9, 5))
    ys = [frontier_df[c].values for c in wcols]
    ax.stackplot(x, ys, labels=asset_names, colors=[ASSET_COLORS[i % 3] for i in range(len(asset_names))], alpha=0.9)
    ax.set_xlabel("Target portfolio return (%, annualised)")
    ax.set_ylabel("Weight")
    ax.set_title("Frontier portfolio composition vs target return")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
