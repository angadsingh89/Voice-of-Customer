"""
Build a simple HTML report (tables + embedded PNG graphs) for assignment submission.

Run after main.py:
    python generate_report.py

Or it runs automatically at the end of main.py.
"""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Optional

import pandas as pd


def generate_html_report(
    project_root: Optional[Path] = None,
    out_name: str = "report.html",
) -> Path:
    """
    Read outputs/*.csv and outputs/*.png and write outputs/report.html.

    Open report.html in Chrome/Edge/Firefox (double-click in File Explorer works).
    """
    root = project_root or Path(__file__).resolve().parent
    out_dir = root / "outputs"
    data_dir = root / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    comp = out_dir / "portfolio_comparison.csv"
    frontier = out_dir / "efficient_frontier.csv"
    prices = data_dir / "adj_close_prices.csv"

    date_line = "Run main.py first to populate data."
    if prices.is_file():
        try:
            px = pd.read_csv(prices, index_col=0, parse_dates=True)
            date_line = f"{px.index.min().date()} → {px.index.max().date()}"
        except Exception:
            pass

    comp_html = "<p><em>No portfolio_comparison.csv yet — run main.py.</em></p>"
    if comp.is_file():
        df = pd.read_csv(comp)
        rows = []
        for _, row in df.iterrows():
            cells = "".join(f"<td>{html.escape(str(v))}</td>" for v in row)
            rows.append(f"<tr>{cells}</tr>")
        comp_html = (
            '<table class="tbl"><thead><tr>'
            + "".join(f"<th>{html.escape(c)}</th>" for c in df.columns)
            + "</tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )

    frontier_note = ""
    if frontier.is_file():
        fr = pd.read_csv(frontier)
        frontier_note = (
            f"<p class=\"muted\">Efficient frontier sweep: <strong>{len(fr)}</strong> solved points.</p>"
        )

    imgs = [
        ("Efficient frontier & capital market line", "efficient_frontier.png"),
        ("Portfolio weights along the frontier", "weight_composition.png"),
        ("KKT stationarity check (LHS vs RHS)", "kkt_verification.png"),
    ]
    figures_html = []
    for title, fname in imgs:
        p = out_dir / fname
        if p.is_file():
            # Same folder as HTML → relative path works when opening report.html
            figures_html.append(
                f'<figure class="fig"><h3>{html.escape(title)}</h3>'
                f'<img src="{html.escape(fname)}" alt="{html.escape(title)}" loading="lazy"/>'
                f"</figure>"
            )
        else:
            figures_html.append(
                f'<p class="muted"><em>Missing {html.escape(fname)} — run main.py.</em></p>'
            )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ME F320 — Portfolio optimisation report</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --card: #ffffff;
      --text: #1a1a1a;
      --muted: #5c6370;
      --border: #e3e6ef;
      --accent: #2f6fed;
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    .wrap {{
      max-width: 960px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }}
    h1 {{
      font-size: 1.55rem;
      margin: 0 0 8px;
    }}
    .sub {{
      color: var(--muted);
      margin: 0 0 22px;
      font-size: 0.95rem;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px 18px 8px;
      margin: 16px 0;
      box-shadow: 0 8px 24px rgba(20, 24, 40, 0.06);
    }}
    h2 {{
      font-size: 1.1rem;
      margin: 0 0 12px;
      color: var(--accent);
    }}
    .tbl {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}
    .tbl th, .tbl td {{
      border-bottom: 1px solid var(--border);
      padding: 10px 8px;
      text-align: left;
    }}
    .tbl th {{
      background: #f0f3fa;
      font-weight: 600;
    }}
    .tbl tr:nth-child(even) td {{ background: #fafbff; }}
    .fig {{
      margin: 0 0 18px;
    }}
    .fig img {{
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      border: 1px solid var(--border);
    }}
    .fig h3 {{
      font-size: 0.98rem;
      margin: 0 0 10px;
    }}
    .muted {{ color: var(--muted); font-size: 0.92rem; }}
    footer {{
      margin-top: 28px;
      font-size: 0.85rem;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Markowitz mean–variance portfolio optimisation</h1>
    <p class="sub">Commodities: Gold (GC=F), Silver (SI=F), Copper (HG=F) · Sample period: {html.escape(date_line)}</p>

    <div class="card">
      <h2>Portfolio comparison</h2>
      {comp_html}
    </div>

    <div class="card">
      <h2>Graphs</h2>
      {frontier_note}
      {"".join(figures_html)}
    </div>

    <footer>
      Generated from <code>outputs/</code> CSVs and PNGs. Re-run <code>python main.py</code> to refresh.
    </footer>
  </div>
</body>
</html>
"""

    out_path = out_dir / out_name
    out_path.write_text(html_doc, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    p = generate_html_report()
    print(f"[generate_report] Wrote: {p}")
    print("[generate_report] Open this file in your web browser (double-click in File Explorer).")
