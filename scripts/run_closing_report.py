#!/usr/bin/env python3
"""장 마감 후 마감가를 반영한 데일리 클로징 리포트를 생성한다."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date

from src.config import get_stock_watchlist, ROOT_DIR
from src.data.yahoo_client import fetch_ticker_data
from src.analysis.technical import get_latest_signals


def run():
    market_filter = os.environ.get("MARKET_FILTER", "all")

    print(f"{'='*60}")
    print(f"  Stock Forecast Platform - Closing Report")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Market: {market_filter}")
    print(f"{'='*60}\n")

    watchlist = get_stock_watchlist()
    tickers = []
    for market_name, market_data in watchlist.get("markets", {}).items():
        if market_filter != "all" and market_name != market_filter:
            continue
        for stock in market_data.get("tickers", []):
            tickers.append((stock["symbol"], stock["name"], market_name))

    print(f"[1/3] Fetching closing prices for {len(tickers)} stocks...")

    results = []
    for symbol, name, market in tickers:
        df = fetch_ticker_data(symbol, period="5d")
        if df.empty:
            print(f"       {symbol}: no data")
            continue

        last_row = df.iloc[-1]
        prev_close = float(df.iloc[-2]["Close"]) if len(df) >= 2 else float(last_row["Close"])
        close_price = float(last_row["Close"])
        change_pct = round((close_price - prev_close) / prev_close * 100, 2)
        high = float(last_row["High"])
        low = float(last_row["Low"])
        volume = int(last_row["Volume"])

        signals = get_latest_signals(df)
        rsi = signals.get("RSI", {}).get("value", "N/A")

        results.append({
            "symbol": symbol,
            "name": name,
            "market": market,
            "close": close_price,
            "change_pct": change_pct,
            "high": high,
            "low": low,
            "volume": volume,
            "rsi": rsi,
        })
        print(f"       {symbol} ({name}): {close_price:,.2f} ({change_pct:+.2f}%)")

    # Generate closing report
    print(f"\n[2/3] Generating closing report...")
    today = datetime.now().strftime("%Y-%m-%d")
    currency = lambda m: "₩" if m == "korea" else "$"

    report_lines = []
    report_lines.append(f"# Daily Closing Report / 일일 마감 리포트")
    report_lines.append(f"")
    report_lines.append(f"**Date / 날짜**: {today}")
    report_lines.append(f"**Market / 시장**: {market_filter.upper()}")
    report_lines.append(f"**Generated / 생성시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"")
    report_lines.append(f"---")
    report_lines.append(f"")

    # Summary table
    report_lines.append(f"## Closing Summary / 마감 요약")
    report_lines.append(f"")
    report_lines.append(f"| Ticker / 종목 | Close / 종가 | Change / 변동 | High / 고가 | Low / 저가 | Volume / 거래량 | RSI |")
    report_lines.append(f"|------|-------|--------|------|------|---------|-----|")

    gainers = []
    losers = []

    for r in sorted(results, key=lambda x: x["change_pct"], reverse=True):
        c = currency(r["market"])
        emoji = "🟢" if r["change_pct"] > 0 else "🔴" if r["change_pct"] < 0 else "⚪"
        report_lines.append(
            f"| {emoji} {r['name']} ({r['symbol']}) | {c}{r['close']:,.2f} | {r['change_pct']:+.2f}% | {c}{r['high']:,.2f} | {c}{r['low']:,.2f} | {r['volume']:,} | {r['rsi']} |"
        )
        if r["change_pct"] > 0:
            gainers.append(r)
        elif r["change_pct"] < 0:
            losers.append(r)

    report_lines.append(f"")
    report_lines.append(f"---")
    report_lines.append(f"")

    # Top movers
    report_lines.append(f"## Top Gainers / 상승 상위")
    for r in gainers[:5]:
        c = currency(r["market"])
        report_lines.append(f"- 🟢 **{r['name']}** ({r['symbol']}): {c}{r['close']:,.2f} ({r['change_pct']:+.2f}%)")

    report_lines.append(f"")
    report_lines.append(f"## Top Losers / 하락 상위")
    for r in losers[-5:]:
        c = currency(r["market"])
        report_lines.append(f"- 🔴 **{r['name']}** ({r['symbol']}): {c}{r['close']:,.2f} ({r['change_pct']:+.2f}%)")

    report_lines.append(f"")
    report_lines.append(f"---")
    report_lines.append(f"")

    # Market stats
    avg_change = sum(r["change_pct"] for r in results) / len(results) if results else 0
    up_count = len(gainers)
    down_count = len(losers)
    flat_count = len(results) - up_count - down_count

    report_lines.append(f"## Market Stats / 시장 통계")
    report_lines.append(f"")
    report_lines.append(f"| Metric / 지표 | Value / 값 |")
    report_lines.append(f"|------|------|")
    report_lines.append(f"| Total Stocks / 총 종목 | {len(results)} |")
    report_lines.append(f"| Gainers / 상승 | {up_count} 🟢 |")
    report_lines.append(f"| Losers / 하락 | {down_count} 🔴 |")
    report_lines.append(f"| Flat / 보합 | {flat_count} ⚪ |")
    report_lines.append(f"| Avg Change / 평균 변동 | {avg_change:+.2f}% |")
    report_lines.append(f"")
    report_lines.append(f"---")
    report_lines.append(f"*Generated by Stock Forecast Platform*")

    # Save report
    output_dir = ROOT_DIR / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{today}_closing_{market_filter}.md"
    output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"       -> Saved: {output_path}")

    # Update DB with closing prices
    print(f"\n[3/3] Updating DB with closing prices...")
    try:
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import Session
        from src.db.models import Base, Prediction

        engine = create_engine(f"sqlite:///{ROOT_DIR}/data/stock_forecast.db")
        with Session(engine) as session:
            updated = 0
            for r in results:
                stmt = (
                    update(Prediction)
                    .where(Prediction.ticker == r["symbol"], Prediction.date == date.today())
                    .values(last_price=r["close"], change_pct=r["change_pct"])
                )
                result_obj = session.execute(stmt)
                updated += result_obj.rowcount
            session.commit()
            print(f"       -> Updated {updated} predictions with closing prices")
    except Exception as e:
        print(f"       -> DB update failed: {e}")

    # Final summary
    print(f"\n{'='*60}")
    print(f"  Closing Report Complete!")
    print(f"  Stocks: {len(results)} | Up: {up_count} | Down: {down_count} | Flat: {flat_count}")
    print(f"  Avg Change: {avg_change:+.2f}%")
    print(f"  Report: {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
