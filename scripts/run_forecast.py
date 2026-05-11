#!/usr/bin/env python3
"""Run a single forecast cycle: fetch data, analyze, generate report."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from src.config import get_stock_watchlist
from src.data.yahoo_client import fetch_ticker_data, get_latest_price
from src.data.news_scraper import fetch_all_news, get_news_summary_text, NewsArticle
from src.analysis.technical import get_latest_signals
from src.analysis.llm_analysis import analyze_with_llm
from src.analysis.combiner import combine_signals
from src.reports.markdown_report import generate_daily_report


def run():
    print(f"{'='*60}")
    print(f"  Stock Forecast Platform - Daily Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 1. Fetch news
    print("[1/4] Fetching news articles...")
    all_news = fetch_all_news(max_per_source=5)
    print(f"       -> {len(all_news)} articles collected")

    news_text = get_news_summary_text(all_news)

    # 2. Fetch price data and compute signals
    print("[2/4] Fetching price data & computing indicators...")
    watchlist = get_stock_watchlist()
    forecasts = []

    all_tickers = []
    for market_name, market_data in watchlist.get("markets", {}).items():
        for stock in market_data.get("tickers", []):
            all_tickers.append((stock["symbol"], stock["name"], market_name))

    for symbol, name, market in all_tickers:
        print(f"       Processing {symbol} ({name})...")

        # Fetch data
        df = fetch_ticker_data(symbol, period="3mo")
        if df.empty:
            print(f"       -> No data for {symbol}, skipping")
            continue

        # Technical signals
        signals = get_latest_signals(df)

        # Recent prices for context
        recent_prices = []
        for i in range(min(5, len(df))):
            idx = -(5 - i) if len(df) >= 5 else -(len(df) - i)
            if abs(idx) <= len(df):
                row = df.iloc[idx]
                prev_close = df.iloc[idx - 1]["Close"] if abs(idx - 1) < len(df) else row["Close"]
                change = (row["Close"] - prev_close) / prev_close * 100 if prev_close else 0
                recent_prices.append({
                    "date": str(df.index[idx].date()),
                    "close": float(row["Close"]),
                    "change_pct": round(change, 2),
                })

        current_price = float(df.iloc[-1]["Close"])

        # 3. LLM Analysis
        print(f"       -> Running LLM analysis...")
        llm_result = analyze_with_llm(
            ticker=symbol,
            ticker_name=name,
            technical_signals=signals,
            news_text=news_text[:3000],
            recent_prices=recent_prices,
            current_price=current_price,
        )

        # 4. Combine signals
        combined = combine_signals(signals, llm_result)

        last_row = df.iloc[-1]
        prev_close = df.iloc[-2]["Close"] if len(df) >= 2 else last_row["Close"]
        change_pct = round((last_row["Close"] - prev_close) / prev_close * 100, 2)

        tech_summary_parts = []
        for indicator, data in signals.items():
            if isinstance(data, dict) and "signal" in data:
                tech_summary_parts.append(f"{indicator}={data['signal']}")

        llm_analysis = combined["llm_analysis"]
        daily_data = llm_analysis.get("daily", {})
        weekly_data = llm_analysis.get("weekly", {})
        monthly_data = llm_analysis.get("monthly", {})

        forecasts.append({
            "symbol": symbol,
            "name": name,
            "market": market,
            "last_close": round(float(last_row["Close"]), 2),
            "change_pct": change_pct,
            "direction": combined["direction"],
            "confidence": combined["confidence"],
            "final_score": combined["final_score"],
            "daily": {
                "direction": daily_data.get("direction", "FLAT"),
                "confidence": daily_data.get("confidence", 0.5),
                "score": combined["final_score"],
                "price_range": daily_data.get("price_range", {}),
                "reasoning": daily_data.get("reasoning", ""),
            },
            "weekly": {
                "direction": weekly_data.get("direction", "FLAT"),
                "confidence": weekly_data.get("confidence", 0.5),
                "score": round(weekly_data.get("confidence", 0.5), 4),
                "price_range": weekly_data.get("price_range", {}),
                "reasoning": weekly_data.get("reasoning", ""),
            },
            "monthly": {
                "direction": monthly_data.get("direction", "FLAT"),
                "confidence": monthly_data.get("confidence", 0.5),
                "score": round(monthly_data.get("confidence", 0.5), 4),
                "price_range": monthly_data.get("price_range", {}),
                "reasoning": monthly_data.get("reasoning", ""),
            },
            "tech_summary": ", ".join(tech_summary_parts) if tech_summary_parts else "N/A",
            "news_summary": llm_analysis.get("news_summary", ""),
            "key_catalysts": llm_analysis.get("key_catalysts", []),
            "key_risks": llm_analysis.get("key_risks", []),
        })

    # 5. Generate reports
    print(f"\n[3/4] Generating reports...")
    from src.reports.stock_report import generate_stock_report

    # Individual stock reports
    for f in forecasts:
        stock_report_path = generate_stock_report(f)
        print(f"       -> Stock report: {stock_report_path}")

    # Daily summary report
    top_news_for_report = [
        {"source": a.source, "title": a.title}
        for a in all_news[:10]
    ]
    report_path = generate_daily_report(
        forecasts=forecasts,
        top_news=top_news_for_report,
    )
    print(f"       -> Daily report saved: {report_path}")

    # Summary
    print(f"\n[4/4] Summary")
    print(f"{'='*60}")
    print(f"  Stocks analyzed: {len(forecasts)}")
    print(f"  UP forecasts:    {sum(1 for f in forecasts if f['direction'] == 'UP')}")
    print(f"  DOWN forecasts:  {sum(1 for f in forecasts if f['direction'] == 'DOWN')}")
    print(f"  FLAT forecasts:  {sum(1 for f in forecasts if f['direction'] == 'FLAT')}")
    print(f"  Report: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
