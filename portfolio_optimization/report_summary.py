"""
Console report summarising data, portfolios, frontier, and KKT (reads saved CSVs).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_pipeline import ASSET_LABELS, TRADING_DAYS, RISK_FREE


def _read_prices() -> pd.DataFrame:
    p = os.path.join(ROOT, "data", "adj_close_prices.csv")
    if not os.path.isfile(p):
        raise FileNotFoundError(f"Run main.py first to create {p}")
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return df


def main() -> None:
    out_dir = os.path.join(ROOT, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 60)
    print("ME F320 - Markowitz portfolio optimisation - summary report")
    print("=" * 60)

    prices = _read_prices()
    rets = np.log(prices / prices.shift(1)).dropna()
    mu = (rets.mean() * TRADING_DAYS).values
    cov = (rets.cov() * TRADING_DAYS).values
    vols = np.sqrt(np.diag(cov))

    print("\n--- Data summary ---\n")
    print(f"Tickers: Gold (GC=F), Silver (SI=F), Copper (HG=F)")
    print(f"Date range: {prices.index.min().date()} -> {prices.index.max().date()}")
    for i, name in enumerate(ASSET_LABELS):
        print(
            f"  {name}: ann. return {100 * mu[i]:.2f}%, "
            f"ann. vol {100 * vols[i]:.2f}%, "
            f"Sharpe vs {100 * RISK_FREE:.1f}% rf: {(mu[i] - RISK_FREE) / max(vols[i], 1e-12):.4f}"
        )

    comp_path = os.path.join(out_dir, "portfolio_comparison.csv")
    if os.path.isfile(comp_path):
        print("\n--- Optimal weights (from last run) ---\n")
        comp = pd.read_csv(comp_path)
        print(comp.to_string(index=False))
    else:
        print(f"\n(No {comp_path} yet — run main.py first.)\n")

    frontier_path = os.path.join(out_dir, "efficient_frontier.csv")
    if os.path.isfile(frontier_path):
        fr = pd.read_csv(frontier_path)
        imin = fr["volatility"].idxmin()
        imax = fr["sharpe_ratio"].idxmax()
        print("\n--- Efficient frontier (saved sweep) ---\n")
        print(
            f"Lowest-vol frontier point: return {100 * fr.loc[imin, 'portfolio_return']:.4f}%, "
            f"vol {100 * fr.loc[imin, 'volatility']:.4f}%"
        )
        print(
            f"Max Sharpe on sweep: return {100 * fr.loc[imax, 'portfolio_return']:.4f}%, "
            f"vol {100 * fr.loc[imax, 'volatility']:.4f}%"
        )
    else:
        print(f"\n(No {frontier_path} yet.)\n")

    kkt_png = os.path.join(out_dir, "kkt_verification.png")
    print("\n--- KKT verification ---\n")
    if os.path.isfile(kkt_png):
        print(f"Figure saved: {kkt_png} (see console output from main.py for numeric check).")
    else:
        print("No KKT figure found; run main.py.")

    print("\n--- Takeaway ---\n")
    print(
        "Max Sharpe (long-only) usually offers the best risk-adjusted return vs the risk-free rate; "
        "equal weight is a simple baseline; global minimum variance minimises volatility but may "
        "sacrifice return. The MIP with at most two commodities forces sparsity - useful if you want "
        "to limit exposure to few names, but it may be infeasible or suboptimal at a given "
        "return target."
    )
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
