from datetime import date, timedelta
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session
from src.db.models import Prediction


class AccuracyScorer:
    def __init__(self, decay_factor: float = 0.95) -> None:
        self.decay_factor = decay_factor

    async def get_accuracy(
        self, ticker: str | None = None, days: int = 30
    ) -> dict[str, Any]:
        cutoff_date = date.today() - timedelta(days=days)

        async with async_session() as session:
            predictions = await self._get_evaluated_predictions(
                session, cutoff_date, ticker
            )

        if not predictions:
            return {
                "directional_accuracy": 0.0,
                "total": 0,
                "correct": 0,
                "weighted_accuracy": 0.0,
                "by_ticker": {},
            }

        total = len(predictions)
        correct = sum(
            1 for p in predictions if p.direction == p.actual_direction
        )
        weighted_accuracy = self._exponentially_weighted_accuracy(predictions)

        by_ticker = self._compute_per_ticker(predictions)

        return {
            "directional_accuracy": round(correct / total, 4) if total > 0 else 0.0,
            "total": total,
            "correct": correct,
            "weighted_accuracy": round(weighted_accuracy, 4),
            "by_ticker": by_ticker,
            "period_days": days,
        }

    def _exponentially_weighted_accuracy(self, predictions: list[Prediction]) -> float:
        sorted_preds = sorted(predictions, key=lambda p: p.date)
        n = len(sorted_preds)
        if n == 0:
            return 0.0

        weights = np.array([self.decay_factor ** (n - 1 - i) for i in range(n)])
        correct = np.array([
            1.0 if p.direction == p.actual_direction else 0.0
            for p in sorted_preds
        ])

        return float(np.average(correct, weights=weights))

    def _compute_per_ticker(self, predictions: list[Prediction]) -> dict[str, Any]:
        ticker_groups: dict[str, list[Prediction]] = {}
        for p in predictions:
            ticker_groups.setdefault(p.ticker, []).append(p)

        by_ticker = {}
        for ticker, preds in ticker_groups.items():
            total = len(preds)
            correct = sum(1 for p in preds if p.direction == p.actual_direction)
            by_ticker[ticker] = {
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total, 4) if total > 0 else 0.0,
                "weighted_accuracy": round(
                    self._exponentially_weighted_accuracy(preds), 4
                ),
            }

        return by_ticker

    async def _get_evaluated_predictions(
        self,
        session: AsyncSession,
        cutoff_date: date,
        ticker: str | None = None,
    ) -> list[Prediction]:
        stmt = select(Prediction).where(
            Prediction.date >= cutoff_date,
            Prediction.actual_direction.isnot(None),
        )
        if ticker:
            stmt = stmt.where(Prediction.ticker == ticker)

        result = await session.execute(stmt)
        return list(result.scalars().all())
