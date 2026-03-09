# DCA Simulator

An interactive Streamlit app that simulates **Dollar Cost Averaging (DCA)** across multiple assets and sliding investment windows, helping you visualize historical outcomes for different investment periods.

## What it does

Given a total investment amount, an asset, and a year range, the simulator:

1. Splits the capital into equal monthly installments over the selected investment period
2. Buys the asset at the **first trading day's open** each month
3. Values the portfolio at the **last trading day's close** each month
4. Repeats this for every starting year in the selected range (one window per year)
5. Aggregates all windows to show the **min/median/max band** of possible outcomes

### Charts

| Chart | Description |
|---|---|
| % Variation Band | Return % vs. invested capital across all windows |
| Dollar Value Band | Portfolio value vs. invested capital in dollars |
| Final Return by Start Year | Bar chart of each window's return after the selected period |

A raw data table is also available via an expandable section.

## Getting started

### Prerequisites

- Python 3.10+

### Installation

```bash
git clone https://github.com/africanogerson/DCA-simulator.git
cd DCA-simulator
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

## Usage

Use the **sidebar** to configure:

| Parameter | Description |
|---|---|
| Asset | The asset to simulate (see supported assets below) |
| Total Investment ($) | Capital to spread over the investment period (≥ $1,000) |
| Start Year | First window starts in January of this year |
| End Year | Last window starts in January of this year − 1 (max 2025) |
| Investment Period (years) | Duration of each DCA window (1–10 years) |
| Fixed Income Annual Rate (%) | Benchmark rate for the fixed income comparison |

The app automatically calculates the monthly installment and runs all simulations.

### Supported assets

| Ticker | Asset | Min Start Year |
|---|---|---|
| SPY | S&P 500 ETF | 1994 |
| QQQ | Nasdaq 100 ETF | 2000 |
| GLD | Gold ETF | 2005 |
| BTC-USD | Bitcoin | 2015 |
| EEM | Emerging Markets ETF | 2003 |

The **min start year** is the first full calendar year covered by the asset's historical data. For example, the earliest Bitcoin record available via yfinance is September 17, 2014 — so data is considered from January 1, 2015 to ensure every simulation window starts with a complete calendar year.

## Project structure

```
dca-spy-simulator/
├── app.py             # Streamlit UI and charts
├── simulation.py      # Simulation logic and aggregation
├── data_cache.py      # SQLite-backed price cache (refreshed every 24h)
├── ticker_config.py   # Asset metadata (name, min start year, default start year)
├── requirements.txt   # Python dependencies
└── .gitignore
```

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `yfinance` | Asset price history |
| `pandas` | Data manipulation |
| `plotly` | Interactive charts |
| `sqlite3` | Built-in price cache (no extra install needed) |

## Disclaimer

This tool is for **educational and informational purposes only**. Past performance of any asset does not guarantee future results. Nothing here constitutes financial advice.
