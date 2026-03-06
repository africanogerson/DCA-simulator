from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from ticker_config import TICKERS

DB_PATH = "./dca_cache.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT,
            date   TEXT,
            open   REAL,
            high   REAL,
            low    REAL,
            close  REAL,
            PRIMARY KEY (ticker, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fetch_log (
            ticker       TEXT PRIMARY KEY,
            last_fetched TEXT
        )
    """)
    conn.commit()
    return conn


def _is_fresh(conn: sqlite3.Connection, ticker: str) -> bool:
    row = conn.execute(
        "SELECT last_fetched FROM fetch_log WHERE ticker = ?", (ticker,)
    ).fetchone()
    if row is None:
        return False
    return datetime.utcnow() - datetime.fromisoformat(row[0]) < timedelta(hours=24)


def _read_cached(conn: sqlite3.Connection, ticker: str, start: str, end: str) -> pd.DataFrame:
    rows = conn.execute(
        "SELECT date, open, high, low, close FROM prices "
        "WHERE ticker = ? AND date >= ? AND date <= ? ORDER BY date",
        (ticker, start, end),
    ).fetchall()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close"])
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)
    return df


def _upsert(conn: sqlite3.Connection, ticker: str, df: pd.DataFrame) -> None:
    rows = [
        (ticker, str(idx.date()), row["Open"], row["High"], row["Low"], row["Close"])
        for idx, row in df.iterrows()
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO prices (ticker, date, open, high, low, close) VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.execute(
        "INSERT OR REPLACE INTO fetch_log (ticker, last_fetched) VALUES (?, ?)",
        (ticker, datetime.utcnow().isoformat()),
    )
    conn.commit()


def get_or_fetch(ticker: str, start_year: int, end_year: int, window_years: int) -> pd.DataFrame:
    """Return OHLCV DataFrame for ticker, using SQLite cache when fresh.

    Always fetches from the ticker's min_year so the cache is fully populated
    regardless of the user's selected start_year. The returned DataFrame is
    filtered to the requested date range.
    """
    min_year = TICKERS[ticker]["min_year"]
    cache_start = f"{min_year}-01-01"
    filter_start = f"{start_year}-01-01"
    filter_end = f"{end_year + window_years}-12-31"

    conn = _get_conn()
    try:
        if _is_fresh(conn, ticker):
            df = _read_cached(conn, ticker, filter_start, filter_end)
            if not df.empty:
                return df

        df: pd.DataFrame = yf.download(
            ticker,
            start=cache_start,
            end="2099-12-31",
            multi_level_index=False,
            auto_adjust=False,
        )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        _upsert(conn, ticker, df)
        return _read_cached(conn, ticker, filter_start, filter_end)
    finally:
        conn.close()
