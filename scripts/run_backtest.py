#!/usr/bin/env python3
"""CLI script to run backtesting evaluation, scoring, and auto-tuning."""

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.evaluator import BacktestEvaluator
from src.backtesting.scorer import AccuracyScorer
from src.backtesting.tuner import WeightTuner


async def main() -> None:
    print("=" * 60)
    print(f"  Stock Forecast Backtesting - {date.today()}")
    print("=" * 60)

    # Step 1: Evaluate yesterday's predictions
    evaluator = BacktestEvaluator()
    yesterday = date.today() - timedelta(days=1)
    print(f"\n[1/3] Evaluating predictions for {yesterday}...")

    eval_result = await evaluator.evaluate_day(yesterday)
    _print_evaluation(eval_result)

    # Step 2: Score rolling accuracy
    scorer = AccuracyScorer()
    print("\n[2/3] Computing rolling accuracy (30 days)...")

    accuracy = await scorer.get_accuracy(days=30)
    _print_accuracy(accuracy)

    # Step 3: Auto-tune weights if conditions are met
    tuner = WeightTuner()
    print("\n[3/3] Running auto-tuning...")

    tuning_result = await tuner.run_tuning()
    _print_tuning(tuning_result)

    print("\n" + "=" * 60)
    print("  Backtesting complete.")
    print("=" * 60)


def _print_evaluation(result: dict) -> None:
    if result["status"] == "no_predictions":
        print("  No predictions found for this date.")
        return

    print(f"  Evaluated: {result['evaluated']} predictions")
    print(f"  Correct:   {result['correct']}")
    print(f"  Accuracy:  {result['directional_accuracy']:.1%}")
    print(f"  Avg |Move|: {result['magnitude_error']:.2f}%")

    if result.get("details"):
        print("\n  Details:")
        for d in result["details"]:
            status = "OK" if d["correct"] else "MISS"
            print(
                f"    [{status}] {d['ticker']:8s} "
                f"pred={d['predicted_direction']:4s} "
                f"actual={d['actual_direction']:4s} "
                f"({d['actual_change']:+.2f}%)"
            )


def _print_accuracy(accuracy: dict) -> None:
    if accuracy["total"] == 0:
        print("  No evaluated predictions in period.")
        return

    print(f"  Total predictions: {accuracy['total']}")
    print(f"  Correct:           {accuracy['correct']}")
    print(f"  Directional acc:   {accuracy['directional_accuracy']:.1%}")
    print(f"  Weighted acc:      {accuracy['weighted_accuracy']:.1%}")

    if accuracy.get("by_ticker"):
        print("\n  Per-ticker breakdown:")
        for ticker, stats in accuracy["by_ticker"].items():
            print(
                f"    {ticker:8s}: {stats['accuracy']:.1%} "
                f"({stats['correct']}/{stats['total']})"
            )


def _print_tuning(result: dict) -> None:
    if result["status"] == "skipped":
        print(f"  Skipped: {result['reason']}")
        return

    print(f"  Current accuracy: {result['current_accuracy']:.1%}")
    print(f"  Data days:        {result['data_days']}")
    print(f"  Adjustment:       {result['weight_adjustment']:+.4f}")

    if result.get("new_weights"):
        w = result["new_weights"]
        print(f"  New weights:      ML={w['ml_weight']:.4f}, LLM={w['llm_weight']:.4f}")

    if result.get("emergency_retrain"):
        rt = result["emergency_retrain"]
        print(f"  Emergency retrain: {rt['status']}")


if __name__ == "__main__":
    asyncio.run(main())
