from datetime import date, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.yahoo_client import fetch_ticker_data
from src.db.database import async_session
from src.db.models import Prediction


class BacktestEvaluator:
    async def evaluate_day(self, target_date: date | None = None) -> dict[str, Any]:
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        async with async_session() as session:
            predictions = await self._get_predictions(session, target_date)

            if not predictions:
                return {
                    "date": str(target_date),
                    "status": "no_predictions",
                    "evaluated": 0,
                }

            results = []
            for pred in predictions:
                actual = self._get_actual_movement(pred.ticker, target_date)
                if actual is None:
                    continue

                await self._update_prediction(
                    session, pred.id, actual["direction"], actual["change_pct"]
                )
                correct = pred.direction == actual["direction"]
                results.append({
                    "ticker": pred.ticker,
                    "predicted_direction": pred.direction,
                    "actual_direction": actual["direction"],
                    "actual_change": actual["change_pct"],
                    "correct": correct,
                    "confidence": pred.confidence,
                })

            await session.commit()

        total = len(results)
        correct = sum(1 for r in results if r["correct"])

        return {
            "date": str(target_date),
            "status": "evaluated",
            "evaluated": total,
            "correct": correct,
            "directional_accuracy": round(correct / total, 4) if total > 0 else 0.0,
            "magnitude_error": self._compute_magnitude_error(results),
            "hit_rate": round(correct / total, 4) if total > 0 else 0.0,
            "details": results,
        }

    async def _get_predictions(
        self, session: AsyncSession, target_date: date
    ) -> list[Prediction]:
        stmt = select(Prediction).where(
            Prediction.date == target_date,
            Prediction.actual_direction.is_(None),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _update_prediction(
        self,
        session: AsyncSession,
        prediction_id: int,
        actual_direction: str,
        actual_change: float,
    ) -> None:
        stmt = (
            update(Prediction)
            .where(Prediction.id == prediction_id)
            .values(actual_direction=actual_direction, actual_change=actual_change)
        )
        await session.execute(stmt)

    def _get_actual_movement(self, ticker: str, target_date: date) -> dict[str, Any] | None:
        df = fetch_ticker_data(ticker, period="5d")
        if df.empty or len(df) < 2:
            return None

        dates = df.index.date if hasattr(df.index, "date") else df.index
        target_rows = df[dates == target_date] if hasattr(dates, "__iter__") else df

        if target_rows.empty:
            last = df.iloc[-1]
            prev = df.iloc[-2]
        else:
            idx = df.index.get_loc(target_rows.index[0])
            if idx == 0:
                return None
            last = df.iloc[idx]
            prev = df.iloc[idx - 1]

        change_pct = (last["Close"] - prev["Close"]) / prev["Close"] * 100

        if change_pct > 0.1:
            direction = "UP"
        elif change_pct < -0.1:
            direction = "DOWN"
        else:
            direction = "FLAT"

        return {"direction": direction, "change_pct": round(change_pct, 4)}

    def _compute_magnitude_error(self, results: list[dict[str, Any]]) -> float:
        if not results:
            return 0.0
        errors = [abs(r["actual_change"]) for r in results if r.get("actual_change") is not None]
        return round(sum(errors) / len(errors), 4) if errors else 0.0
