"""
Download commodity futures proxies, build returns, and annualised moments.
"""

from __future__ import annotations

import os
from typing import Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from tabulate import tabulate

TICKERS = ["GC=F", "SI=F", "HG=F"]
ASSET_LABELS = ["Gold", "Silver", "Copper"]
TRADING_DAYS = 252
RISK_FREE = 0.045


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_cached_prices(data_dir: str) -> pd.DataFrame | None:
    path = os.path.join(data_dir, "adj_close_prices.csv")
    if not os.path.isfile(path):
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = df.reindex(columns=TICKERS)
    df = df.sort_index().ffill().bfill().dropna(how="any")
    return df if len(df) >= 30 else None


def download_and_prepare(
    period: str = "5y",
    data_dir: str | None = None,
) -> Tuple[np.ndarray, np.ndarray, list[str], pd.DataFrame, pd.DataFrame]:
    """
    Download adjusted daily prices, compute log returns, annualise mu and Sigma.

    Returns
    -------
    mu : np.ndarray
        Annualised expected returns (daily mean * 252).
    Sigma : np.ndarray
        Annualised covariance (daily cov * 252).
    asset_names : list of str
        Human-readable names aligned with columns.
    prices : DataFrame
        Cleaned adjusted close prices.
    returns : DataFrame
        Daily log returns.
    """
    if data_dir is None:
        data_dir = os.path.join(_project_root(), "data")
    os.makedirs(data_dir, exist_ok=True)

    print("[data_pipeline] Downloading prices from yfinance...")
    try:
        raw = yf.download(
            TICKERS,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            group_by="column",
        )
    except Exception as exc:
        print(f"[data_pipeline] Download error: {exc}")
        raw = None

    prices: pd.DataFrame | None = None
    if raw is not None and len(raw) > 0:
        if isinstance(raw.columns, pd.MultiIndex):
            if "Adj Close" in raw.columns.get_level_values(0):
                prices = raw["Adj Close"].copy()
            else:
                prices = raw["Close"].copy()
        else:
            if "Adj Close" in raw.columns:
                prices = raw[["Adj Close"]].copy()
            else:
                prices = raw.copy()

        prices.columns = [str(c) for c in prices.columns]
        prices = prices.reindex(columns=TICKERS)
        prices = prices.sort_index()
        print("[data_pipeline] Forward-filling missing prices, then dropping remaining NaNs...")
        prices = prices.ffill().bfill()
        prices = prices.dropna(how="any")

    if prices is None or len(prices) < 30:
        cached = _load_cached_prices(data_dir)
        if cached is not None:
            print("[data_pipeline] Using cached adj_close_prices.csv (download incomplete or offline).")
            prices = cached
        else:
            raise RuntimeError(
                "Insufficient price history after cleaning. Check your network connection "
                "and try again; yfinance must return data for GC=F, SI=F, HG=F."
            )

    returns = np.log(prices / prices.shift(1)).dropna(how="any")

    if returns.shape[0] < 30 or prices.shape[0] < 30:
        raise RuntimeError(
            "Insufficient price history after cleaning. Check your network connection "
            "and try again; yfinance must return data for GC=F, SI=F, HG=F."
        )

    daily_mean = returns.mean()
    daily_cov = returns.cov()
    mu = (daily_mean * TRADING_DAYS).values.astype(float)
    Sigma = (daily_cov * TRADING_DAYS).values.astype(float)
    Sigma = (Sigma + Sigma.T) / 2.0

    if not np.isfinite(mu).all() or not np.isfinite(Sigma).all():
        raise RuntimeError(
            "Non-finite mean or covariance — download likely failed. Retry with a stable connection."
        )

    price_path = os.path.join(data_dir, "adj_close_prices.csv")
    ret_path = os.path.join(data_dir, "daily_log_returns.csv")
    prices.to_csv(price_path)
    returns.to_csv(ret_path)
    print(f"[data_pipeline] Saved prices -> {price_path}")
    print(f"[data_pipeline] Saved returns -> {ret_path}")

    vols = np.sqrt(np.diag(Sigma))
    sharpes = (mu - RISK_FREE) / np.maximum(vols, 1e-12)
    table = []
    for i, name in enumerate(ASSET_LABELS):
        table.append(
            [
                name,
                f"{100 * mu[i]:.2f}",
                f"{100 * vols[i]:.2f}",
                f"{sharpes[i]:.4f}",
            ]
        )
    print("\n[data_pipeline] Per-asset summary (annualised, Sharpe vs 4.5% rf):\n")
    print(
        tabulate(
            table,
            headers=["Ticker", "Ann. return (%)", "Ann. vol (%)", "Sharpe"],
            tablefmt="github",
        )
    )
    print()

    return mu, Sigma, ASSET_LABELS.copy(), prices, returns


def load_data(
    period: str = "5y",
    data_dir: str | None = None,
) -> Tuple[np.ndarray, np.ndarray, list[str]]:
    """Run pipeline and return (mu, Sigma, asset_names) for optimizers."""
    mu, Sigma, names, _, _ = download_and_prepare(period=period, data_dir=data_dir)
    return mu, Sigma, names
