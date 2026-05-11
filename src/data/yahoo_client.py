from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from src.config import get_stock_watchlist


def fetch_ticker_data(symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        return pd.DataFrame()
    df["Symbol"] = symbol
    return df


def fetch_all_tickers(market: str | None = None) -> dict[str, pd.DataFrame]:
    watchlist = get_stock_watchlist()
    results = {}

    markets_to_fetch = []
    if market is None or market == "all":
        markets_to_fetch = ["korea", "us"]
    else:
        markets_to_fetch = [market]

    for m in markets_to_fetch:
        if m not in watchlist.get("markets", {}):
            continue
        for stock in watchlist["markets"][m]["tickers"]:
            symbol = stock["symbol"]
            df = fetch_ticker_data(symbol)
            if not df.empty:
                results[symbol] = df

    return results


def get_latest_price(symbol: str) -> dict | None:
    df = fetch_ticker_data(symbol, period="5d")
    if df.empty:
        return None
    last_row = df.iloc[-1]
    return {
        "symbol": symbol,
        "date": str(df.index[-1].date()),
        "open": float(last_row["Open"]),
        "high": float(last_row["High"]),
        "low": float(last_row["Low"]),
        "close": float(last_row["Close"]),
        "volume": int(last_row["Volume"]),
        "change_pct": float((last_row["Close"] - df.iloc[-2]["Close"]) / df.iloc[-2]["Close"] * 100)
        if len(df) >= 2 else 0.0,
    }
