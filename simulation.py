from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import pandas as pd
import yfinance as yf


# ---------------------------------------------------------------------------
# Data download
# ---------------------------------------------------------------------------

def download_spy_data(start_year: int, end_year: int, window_years: int = 2) -> pd.DataFrame:
    """Download SPY OHLCV data for the given year range.

    The end date is set to Dec 31 of end_year+window_years so that the last
    window starting in end_year-1 has data for its final month.
    """
    df: pd.DataFrame = yf.download(
        "SPY",
        start=f"{start_year}-01-01",
        end=f"{end_year + window_years}-12-31",
        multi_level_index=False,
        auto_adjust=False,
    )

    # Defensive: flatten MultiIndex columns if still present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df


# ---------------------------------------------------------------------------
# Month helpers
# ---------------------------------------------------------------------------

def _generate_month_sequence(start_year: int, n: int = 24) -> List[Tuple[int, int]]:
    """Return n consecutive (year, month) tuples starting from Jan of start_year."""
    months = []
    year = start_year
    month = 1
    for _ in range(n):
        months.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def get_first_trading_day_open(df: pd.DataFrame, year: int, month: int) -> Tuple[pd.Timestamp, float]:
    """Return (date, open_price) for the first trading day of the given month."""
    mask = (df.index.year == year) & (df.index.month == month)
    rows = df.loc[mask]
    if rows.empty:
        raise ValueError(f"No trading data for {year}-{month:02d}")
    date = rows.index[0]
    return date, float(rows.loc[date, "Open"])


def get_last_trading_day_close(df: pd.DataFrame, year: int, month: int) -> Tuple[pd.Timestamp, float]:
    """Return (date, close_price) for the last trading day of the given month."""
    mask = (df.index.year == year) & (df.index.month == month)
    rows = df.loc[mask]
    if rows.empty:
        raise ValueError(f"No trading data for {year}-{month:02d}")
    date = rows.index[-1]
    return date, float(rows.loc[date, "Close"])


def get_monthly_high(df: pd.DataFrame, year: int, month: int) -> float:
    """Return the highest High price across all trading days of the given month."""
    mask = (df.index.year == year) & (df.index.month == month)
    rows = df.loc[mask]
    if rows.empty:
        raise ValueError(f"No trading data for {year}-{month:02d}")
    return float(rows["High"].max())


def get_monthly_low(df: pd.DataFrame, year: int, month: int) -> float:
    """Return the lowest Low price across all trading days of the given month."""
    mask = (df.index.year == year) & (df.index.month == month)
    rows = df.loc[mask]
    if rows.empty:
        raise ValueError(f"No trading data for {year}-{month:02d}")
    return float(rows["Low"].min())


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

@dataclass
class WindowResult:
    start_year: int
    monthly_investment: float
    portfolio_values: List[float] = field(default_factory=list)
    portfolio_values_high: List[float] = field(default_factory=list)
    portfolio_values_low: List[float] = field(default_factory=list)
    invested_capital: List[float] = field(default_factory=list)
    pct_variation: List[float] = field(default_factory=list)
    pct_variation_high: List[float] = field(default_factory=list)
    pct_variation_low: List[float] = field(default_factory=list)
    final_return_pct: float = 0.0


def simulate_window(df: pd.DataFrame, start_year: int, total_aum: float, window_years: int = 2) -> WindowResult:
    """Run a DCA simulation for window_years starting in January of start_year."""
    n_months = window_years * 12
    monthly_investment = total_aum / n_months
    result = WindowResult(start_year=start_year, monthly_investment=monthly_investment)

    total_shares = 0.0
    total_invested = 0.0

    for year, month in _generate_month_sequence(start_year, n=n_months):
        # Buy at open on first trading day
        _, open_price = get_first_trading_day_open(df, year, month)
        total_shares += monthly_investment / open_price
        total_invested += monthly_investment

        # Value at close on last trading day
        _, close_price = get_last_trading_day_close(df, year, month)
        portfolio_value = total_shares * close_price
        pct = (portfolio_value - total_invested) / total_invested * 100

        monthly_high = get_monthly_high(df, year, month)
        monthly_low = get_monthly_low(df, year, month)
        portfolio_value_high = total_shares * monthly_high
        portfolio_value_low = total_shares * monthly_low
        pct_high = (portfolio_value_high - total_invested) / total_invested * 100
        pct_low = (portfolio_value_low - total_invested) / total_invested * 100

        result.portfolio_values.append(portfolio_value)
        result.portfolio_values_high.append(portfolio_value_high)
        result.portfolio_values_low.append(portfolio_value_low)
        result.invested_capital.append(total_invested)
        result.pct_variation.append(pct)
        result.pct_variation_high.append(pct_high)
        result.pct_variation_low.append(pct_low)

    result.final_return_pct = result.pct_variation[-1] if result.pct_variation else 0.0
    return result


def run_all_simulations(
    df: pd.DataFrame,
    start_year: int,
    end_year: int,
    total_aum: float,
    window_years: int = 2,
) -> List[WindowResult]:
    """Simulate all windows from start_year up to (but not including) end_year."""
    results = []
    for window_start in range(start_year, end_year):
        try:
            result = simulate_window(df, window_start, total_aum, window_years)
            results.append(result)
        except ValueError as exc:
            print(f"Warning: skipping window {window_start}: {exc}")
    return results


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_results(results: List[WindowResult]) -> dict:
    """Aggregate per-month statistics across all windows."""
    import statistics

    n_months = len(results[0].portfolio_values)
    months = list(range(1, n_months + 1))

    pct_min, pct_max, pct_median = [], [], []
    value_min, value_max, value_median = [], [], []

    for m_idx in range(n_months):
        pcts = [r.pct_variation[m_idx] for r in results]
        pcts_high = [r.pct_variation_high[m_idx] for r in results]
        pcts_low = [r.pct_variation_low[m_idx] for r in results]
        vals = [r.portfolio_values[m_idx] for r in results]
        vals_high = [r.portfolio_values_high[m_idx] for r in results]
        vals_low = [r.portfolio_values_low[m_idx] for r in results]

        pct_min.append(min(pcts_low))
        pct_max.append(max(pcts_high))
        pct_median.append(statistics.median(pcts))

        value_min.append(min(vals_low))
        value_max.append(max(vals_high))
        value_median.append(statistics.median(vals))

    # Invested capital is the same for all windows (same monthly_investment)
    monthly_inv = results[0].monthly_investment
    invested_line = [monthly_inv * m for m in months]

    return {
        "months": months,
        "pct_min": pct_min,
        "pct_max": pct_max,
        "pct_median": pct_median,
        "value_min": value_min,
        "value_max": value_max,
        "value_median": value_median,
        "invested_line": invested_line,
        "final_returns": [r.final_return_pct for r in results],
        "start_years": [r.start_year for r in results],
    }
