# Markowitz portfolio optimization (ME F320)

Mean–variance optimisation for three commodity proxies: **Gold (GC=F)**, **Silver (SI=F)**, **Copper (HG=F)**.

## Quick start

```bash
cd portfolio_optimization
pip install -r requirements.txt
python main.py
```

Open `outputs/report.html` in a browser for tables and graphs.

## Layout

- `src/` — data pipeline, optimisers, frontier, MIP, KKT
- `main.py` — full pipeline
- `generate_report.py` — builds `outputs/report.html`
- `data/` / `outputs/` — CSVs and figures (refreshed when you run `main.py`)

## Requirements

Python 3.10+ recommended. See `requirements.txt`.
