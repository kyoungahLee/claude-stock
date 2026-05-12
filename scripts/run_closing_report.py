#!/usr/bin/env python3
"""장 마감 후 마감가를 반영하고, 오전 전망 대비 정확도를 계산하는 마감 리포트를 생성한다."""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date

from src.config import get_stock_watchlist, ROOT_DIR
from src.data.yahoo_client import fetch_ticker_data
from src.analysis.technical import get_latest_signals


def _load_forecast_for_ticker(symbol: str, report_date: str) -> dict | None:
    """오전에 생성된 전망 리포트에서 예측 정보를 추출한다."""
    safe_symbol = symbol.replace(".", "_")
    report_path = ROOT_DIR / "reports" / "stocks" / f"{report_date}_{safe_symbol}.md"
    if not report_path.exists():
        return None

    content = report_path.read_text(encoding="utf-8")

    direction = "FLAT"
    confidence = 0.0
    price_low = 0.0
    price_high = 0.0

    # Extract daily direction from English section (first occurrence)
    if "🔴 DOWN" in content[:600]:
        direction = "DOWN"
    elif "🟢 UP" in content[:600]:
        direction = "UP"

    # Extract daily confidence
    m = re.search(r"Daily \(Next Day\).*?(\d+)%", content[:1000])
    if m:
        confidence = int(m.group(1)) / 100

    # Extract daily price range
    m = re.search(r"Daily \(Next Day\).*?[\$₩]([\d,.]+)\s*~\s*[\$₩]([\d,.]+)", content[:1000])
    if m:
        price_low = float(m.group(1).replace(",", ""))
        price_high = float(m.group(2).replace(",", ""))

    return {
        "direction": direction,
        "confidence": confidence,
        "price_range": {"low": price_low, "high": price_high},
    }


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

    print(f"[1/4] Fetching closing prices for {len(tickers)} stocks...")

    today_str = datetime.now().strftime("%Y-%m-%d")
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

        # Determine actual direction
        if change_pct > 0.1:
            actual_direction = "UP"
        elif change_pct < -0.1:
            actual_direction = "DOWN"
        else:
            actual_direction = "FLAT"

        results.append({
            "symbol": symbol,
            "name": name,
            "market": market,
            "close": close_price,
            "change_pct": change_pct,
            "actual_direction": actual_direction,
            "high": high,
            "low": low,
            "volume": volume,
            "rsi": rsi,
        })
        print(f"       {symbol} ({name}): {close_price:,.2f} ({change_pct:+.2f}%)")

    # Compare with morning forecast
    print(f"\n[2/4] Comparing with morning forecasts...")
    comparisons = []
    correct = 0
    total_compared = 0
    price_in_range = 0

    for r in results:
        forecast = _load_forecast_for_ticker(r["symbol"], today_str)
        if not forecast:
            comparisons.append({**r, "forecast": None, "correct": None, "in_range": None})
            continue

        total_compared += 1
        direction_correct = forecast["direction"] == r["actual_direction"]
        if direction_correct:
            correct += 1

        in_range = False
        pr = forecast["price_range"]
        if pr["low"] > 0 and pr["high"] > 0:
            in_range = pr["low"] <= r["close"] <= pr["high"]
            if in_range:
                price_in_range += 1

        comparisons.append({
            **r,
            "forecast": forecast,
            "correct": direction_correct,
            "in_range": in_range,
        })
        status = "✅" if direction_correct else "❌"
        print(f"       {status} {r['symbol']}: predicted={forecast['direction']}, actual={r['actual_direction']} ({r['change_pct']:+.2f}%)")

    accuracy = (correct / total_compared * 100) if total_compared > 0 else 0
    range_accuracy = (price_in_range / total_compared * 100) if total_compared > 0 else 0

    # Generate closing report
    print(f"\n[3/4] Generating closing report...")
    currency = lambda m: "₩" if m == "korea" else "$"

    report_lines = []
    report_lines.append("# Daily Closing Report / 일일 마감 리포트")
    report_lines.append("")
    report_lines.append(f"**Date / 날짜**: {today_str}")
    report_lines.append(f"**Market / 시장**: {market_filter.upper()}")
    report_lines.append(f"**Generated / 생성시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Prediction Accuracy Section
    report_lines.append("## 📊 Forecast Accuracy / 전망 정확도")
    report_lines.append("")
    report_lines.append("| Metric / 지표 | Value / 값 |")
    report_lines.append("|------|------|")
    report_lines.append(f"| Direction Accuracy / 방향 적중률 | **{accuracy:.1f}%** ({correct}/{total_compared}) |")
    report_lines.append(f"| Price Range Accuracy / 가격 범위 적중률 | **{range_accuracy:.1f}%** ({price_in_range}/{total_compared}) |")
    report_lines.append(f"| Total Compared / 비교 종목 | {total_compared} |")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Detailed Comparison Table
    report_lines.append("## 📋 Forecast vs Actual / 전망 vs 실제 비교")
    report_lines.append("")
    report_lines.append("| Ticker / 종목 | Predicted / 전망 | Actual / 실제 | Close / 종가 | Change / 변동 | Price Range / 가격 범위 | Result / 결과 |")
    report_lines.append("|------|------|------|------|------|------|------|")

    for c in sorted(comparisons, key=lambda x: x.get("correct") is True, reverse=True):
        cur = currency(c["market"])
        if c["forecast"]:
            pred_dir = c["forecast"]["direction"]
            pred_emoji = "🟢" if pred_dir == "UP" else "🔴" if pred_dir == "DOWN" else "⚪"
            actual_emoji = "🟢" if c["actual_direction"] == "UP" else "🔴" if c["actual_direction"] == "DOWN" else "⚪"
            result_emoji = "✅" if c["correct"] else "❌"
            range_str = f"{cur}{c['forecast']['price_range']['low']:,.2f}~{cur}{c['forecast']['price_range']['high']:,.2f}"
            range_result = "✅" if c["in_range"] else "❌"
            report_lines.append(
                f"| {c['name']} ({c['symbol']}) | {pred_emoji} {pred_dir} | {actual_emoji} {c['actual_direction']} | {cur}{c['close']:,.2f} | {c['change_pct']:+.2f}% | {range_str} {range_result} | {result_emoji} |"
            )
        else:
            actual_emoji = "🟢" if c["actual_direction"] == "UP" else "🔴" if c["actual_direction"] == "DOWN" else "⚪"
            report_lines.append(
                f"| {c['name']} ({c['symbol']}) | - | {actual_emoji} {c['actual_direction']} | {cur}{c['close']:,.2f} | {c['change_pct']:+.2f}% | - | ⚠️ No forecast |"
            )

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Closing Summary
    report_lines.append("## 📈 Closing Summary / 마감 요약")
    report_lines.append("")
    report_lines.append("| Ticker / 종목 | Close / 종가 | Change / 변동 | High / 고가 | Low / 저가 | Volume / 거래량 | RSI |")
    report_lines.append("|------|-------|--------|------|------|---------|-----|")

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

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Top movers
    report_lines.append("## Top Gainers / 상승 상위")
    for r in gainers[:5]:
        c = currency(r["market"])
        report_lines.append(f"- 🟢 **{r['name']}** ({r['symbol']}): {c}{r['close']:,.2f} ({r['change_pct']:+.2f}%)")

    report_lines.append("")
    report_lines.append("## Top Losers / 하락 상위")
    for r in sorted(losers, key=lambda x: x["change_pct"])[:5]:
        c = currency(r["market"])
        report_lines.append(f"- 🔴 **{r['name']}** ({r['symbol']}): {c}{r['close']:,.2f} ({r['change_pct']:+.2f}%)")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Market stats
    avg_change = sum(r["change_pct"] for r in results) / len(results) if results else 0
    up_count = len(gainers)
    down_count = len(losers)
    flat_count = len(results) - up_count - down_count

    report_lines.append("## Market Stats / 시장 통계")
    report_lines.append("")
    report_lines.append("| Metric / 지표 | Value / 값 |")
    report_lines.append("|------|------|")
    report_lines.append(f"| Total Stocks / 총 종목 | {len(results)} |")
    report_lines.append(f"| Gainers / 상승 | {up_count} 🟢 |")
    report_lines.append(f"| Losers / 하락 | {down_count} 🔴 |")
    report_lines.append(f"| Flat / 보합 | {flat_count} ⚪ |")
    report_lines.append(f"| Avg Change / 평균 변동 | {avg_change:+.2f}% |")
    report_lines.append(f"| **Direction Accuracy / 방향 적중률** | **{accuracy:.1f}%** |")
    report_lines.append(f"| **Price Range Accuracy / 가격 범위 적중률** | **{range_accuracy:.1f}%** |")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Generated by Stock Forecast Platform*")

    # Save report
    output_dir = ROOT_DIR / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{today_str}_closing_{market_filter}.md"
    output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"       -> Saved: {output_path}")

    # Update DB with actual results
    print(f"\n[4/4] Updating DB with actual results...")
    try:
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import Session
        from src.db.models import Base, Prediction

        engine = create_engine(f"sqlite:///{ROOT_DIR}/data/stock_forecast.db")
        with Session(engine) as session:
            updated = 0
            for c in comparisons:
                stmt = (
                    update(Prediction)
                    .where(Prediction.ticker == c["symbol"], Prediction.date == date.today())
                    .values(
                        last_price=c["close"],
                        change_pct=c["change_pct"],
                        actual_direction=c["actual_direction"],
                        actual_change=c["change_pct"],
                    )
                )
                result_obj = session.execute(stmt)
                updated += result_obj.rowcount
            session.commit()
            print(f"       -> Updated {updated} predictions with actual results")
    except Exception as e:
        print(f"       -> DB update failed: {e}")

    # Final summary
    print(f"\n{'='*60}")
    print(f"  Closing Report Complete!")
    print(f"  Stocks: {len(results)} | Up: {up_count} | Down: {down_count} | Flat: {flat_count}")
    print(f"  Avg Change: {avg_change:+.2f}%")
    print(f"  Direction Accuracy: {accuracy:.1f}% ({correct}/{total_compared})")
    print(f"  Price Range Accuracy: {range_accuracy:.1f}% ({price_in_range}/{total_compared})")
    print(f"  Report: {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
