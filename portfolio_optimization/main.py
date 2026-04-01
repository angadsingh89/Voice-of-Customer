"""
End-to-end Markowitz pipeline: data, frontier, optimisers, KKT, plots, comparison table.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_pipeline import download_and_prepare
from src.frontier import (
    generate_efficient_frontier,
    plot_efficient_frontier,
    plot_weight_composition,
)
from src.kkt_analysis import run_kkt_analysis
from src.mip_optimizer import solve_mip_portfolio
from src.optimizer import (
    RISK_FREE_DEFAULT,
    solve_equal_weight,
    solve_max_sharpe,
    solve_min_variance_qp,
    solve_min_variance_unconstrained,
)

from generate_report import generate_html_report


def main() -> None:
    data_dir = os.path.join(ROOT, "data")
    out_dir = os.path.join(ROOT, "outputs")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    print("=== Step 1: Data pipeline ===\n")
    mu, Sigma, asset_names, prices, _returns = download_and_prepare(data_dir=data_dir)

    print("=== Step 2: Efficient frontier ===\n")
    frontier_df = generate_efficient_frontier(
        mu, Sigma, asset_names=asset_names, n_points=150, rf=RISK_FREE_DEFAULT
    )
    frontier_path = os.path.join(out_dir, "efficient_frontier.csv")
    frontier_df.to_csv(frontier_path, index=False)
    print(f"[main] Saved frontier -> {frontier_path}\n")

    print("=== Step 3: Portfolio optimisations ===\n")
    min_var = solve_min_variance_unconstrained(mu, Sigma, rf=RISK_FREE_DEFAULT)
    max_sharpe = solve_max_sharpe(mu, Sigma, rf=RISK_FREE_DEFAULT)
    equal_w = solve_equal_weight(mu, Sigma, rf=RISK_FREE_DEFAULT)

    if min_var is None or max_sharpe is None:
        raise RuntimeError("Could not solve baseline portfolios.")

    target_mip = float(max_sharpe["portfolio_return"])
    print(f"[main] MIP target return = max-Sharpe return = {100 * target_mip:.4f}%\n")
    mip = solve_mip_portfolio(
        mu,
        Sigma,
        target_return=target_mip,
        max_assets=2,
        rf=RISK_FREE_DEFAULT,
    )

    print("=== Step 4: KKT (QP on efficient frontier at max-Sharpe return) ===\n")
    qp_for_kkt = solve_min_variance_qp(
        mu,
        Sigma,
        target_return=target_mip,
        allow_short=False,
        rf=RISK_FREE_DEFAULT,
    )
    kkt_ok = False
    if qp_for_kkt is not None and qp_for_kkt.get("dual_values"):
        kkt_path = os.path.join(out_dir, "kkt_verification.png")
        kkt_ok = run_kkt_analysis(
            mu,
            Sigma,
            qp_for_kkt["weights"],
            qp_for_kkt["dual_values"],
            save_path=kkt_path,
            asset_names=asset_names,
        )
    else:
        print("[main] Could not obtain QP duals for KKT analysis.")

    print("\n=== Step 5: Plots ===\n")
    special = {
        "min_variance": min_var,
        "max_sharpe": max_sharpe,
        "equal_weight": equal_w,
        "mip": mip,
    }
    frontier_plot = os.path.join(out_dir, "efficient_frontier.png")
    weight_plot = os.path.join(out_dir, "weight_composition.png")
    plot_efficient_frontier(
        frontier_df,
        special,
        asset_names,
        mu,
        Sigma,
        frontier_plot,
        rf=RISK_FREE_DEFAULT,
    )
    plot_weight_composition(frontier_df, asset_names, weight_plot)
    print(f"[main] Saved {frontier_plot}")
    print(f"[main] Saved {weight_plot}\n")

    print("=== Step 6: Comparison table ===\n")

    def fmt_weights(w: np.ndarray) -> str:
        w = np.maximum(np.asarray(w, dtype=float), 0.0)
        return " / ".join(f"{100 * float(x):.2f}" for x in w)

    rows = []
    for label, sol in [
        ("Min variance", min_var),
        ("Max Sharpe", max_sharpe),
        ("Equal weight", equal_w),
        ("MIP (2 assets)", mip),
    ]:
        if sol is None:
            rows.append([label, "—", "—", "—", "—"])
        else:
            rows.append(
                [
                    label,
                    fmt_weights(sol["weights"]),
                    f"{100 * sol['portfolio_return']:.4f}",
                    f"{100 * sol['portfolio_volatility']:.4f}",
                    f"{sol['sharpe_ratio']:.4f}",
                ]
            )

    headers = [
        "Portfolio",
        "Weights (Gold / Silver / Copper %)",
        "Return (%)",
        "Volatility (%)",
        "Sharpe ratio",
    ]
    print(tabulate(rows, headers=headers, tablefmt="github"))
    comp_path = os.path.join(out_dir, "portfolio_comparison.csv")
    pd.DataFrame(rows, columns=headers).to_csv(comp_path, index=False)
    print(f"\n[main] Saved comparison -> {comp_path}")

    meta = {
        "date_range": f"{prices.index.min().date()} -> {prices.index.max().date()}",
        "kkt_satisfied": kkt_ok,
    }
    print("\n[main] Done.", meta)

    html_path = generate_html_report(project_root=ROOT)
    print(f"\n[main] HTML report -> {html_path}")
    print("[main] Tip: open report.html in Chrome/Edge (double-click in outputs/).")


if __name__ == "__main__":
    main()
