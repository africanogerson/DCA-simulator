# DCA SPY Simulator

An interactive Streamlit app that simulates **Dollar Cost Averaging (DCA)** into the SPY ETF across sliding 24-month windows, helping you visualize historical outcomes for different investment periods.

## What it does

Given a total investment amount and a year range, the simulator:

1. Splits the capital into 24 equal monthly installments
2. Buys SPY at the **first trading day's open** each month
3. Values the portfolio at the **last trading day's close** each month
4. Repeats this for every starting year in the selected range (one window per year)
5. Aggregates all windows to show the **min/median/max band** of possible outcomes

### Charts

| Chart | Description |
|---|---|
| % Variation Band | Return % vs. invested capital across all windows |
| Dollar Value Band | Portfolio value vs. invested capital in dollars |
| Final Return by Start Year | Bar chart of each window's 24-month return |

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

| Parameter | Description | Range |
|---|---|---|
| Total Investment ($) | Capital to spread over 24 months | ≥ $1,000 |
| Start Year | First window starts in January of this year | 1993–2023 |
| End Year | Last window starts in January of this year − 1 | Start+1 – 2025 |

The app automatically calculates the monthly installment and runs all simulations.

## Project structure

```
dca-spy-simulator/
├── app.py            # Streamlit UI and charts
├── simulation.py     # Data download, simulation logic, aggregation
├── requirements.txt  # Python dependencies
└── .gitignore
```

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI |
| `yfinance` | SPY historical data |
| `pandas` | Data manipulation |
| `plotly` | Interactive charts |

## Disclaimer

This tool is for **educational and informational purposes only**. Past performance of SPY does not guarantee future results. Nothing here constitutes financial advice.
