from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import BacktestScoresResponse, TickerAccuracy
from src.db.database import get_session
from src.db.models import Prediction

router = APIRouter(prefix="/api/backtests", tags=["backtests"])


def _compute_accuracy(predictions: list[Prediction]) -> tuple[int, int]:
    total = 0
    correct = 0
    for p in predictions:
        if p.actual_direction is not None:
            total += 1
            if p.direction == p.actual_direction:
                correct += 1
    return total, correct


@router.get("/scores", response_model=BacktestScoresResponse)
async def get_overall_scores(session: AsyncSession = Depends(get_session)):
    stmt = select(Prediction).where(Prediction.actual_direction.isnot(None))
    result = await session.execute(stmt)
    predictions = result.scalars().all()

    total, correct = _compute_accuracy(predictions)
    accuracy = correct / total if total > 0 else 0.0

    ticker_map: dict[str, list[Prediction]] = {}
    for p in predictions:
        ticker_map.setdefault(p.ticker, []).append(p)

    by_ticker = []
    for ticker, preds in sorted(ticker_map.items()):
        t, c = _compute_accuracy(preds)
        by_ticker.append(
            TickerAccuracy(
                ticker=ticker,
                total_predictions=t,
                correct_predictions=c,
                accuracy=c / t if t > 0 else 0.0,
            )
        )

    return BacktestScoresResponse(
        overall_accuracy=accuracy,
        total_predictions=total,
        correct_predictions=correct,
        by_ticker=by_ticker,
    )


@router.get("/scores/{ticker}", response_model=TickerAccuracy)
async def get_ticker_scores(ticker: str, session: AsyncSession = Depends(get_session)):
    stmt = select(Prediction).where(
        Prediction.ticker == ticker.upper(),
        Prediction.actual_direction.isnot(None),
    )
    result = await session.execute(stmt)
    predictions = result.scalars().all()

    if not predictions:
        raise HTTPException(
            status_code=404, detail=f"No evaluated predictions for {ticker.upper()}"
        )

    total, correct = _compute_accuracy(predictions)
    return TickerAccuracy(
        ticker=ticker.upper(),
        total_predictions=total,
        correct_predictions=correct,
        accuracy=correct / total if total > 0 else 0.0,
    )
