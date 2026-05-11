from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ForecastListResponse, ForecastResponse
from src.db.database import get_session
from src.db.models import Prediction

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


@router.get("", response_model=ForecastListResponse)
async def list_today_forecasts(session: AsyncSession = Depends(get_session)):
    today = date.today()
    stmt = select(Prediction).where(Prediction.date == today).order_by(Prediction.ticker)
    result = await session.execute(stmt)
    predictions = result.scalars().all()
    return ForecastListResponse(
        forecasts=[ForecastResponse.model_validate(p) for p in predictions],
        count=len(predictions),
    )


@router.get("/{ticker}", response_model=ForecastResponse)
async def get_ticker_forecast(ticker: str, session: AsyncSession = Depends(get_session)):
    today = date.today()
    stmt = (
        select(Prediction)
        .where(Prediction.ticker == ticker.upper(), Prediction.date == today)
    )
    result = await session.execute(stmt)
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail=f"No forecast found for {ticker.upper()} today")
    return ForecastResponse.model_validate(prediction)


@router.get("/history/{ticker}", response_model=ForecastListResponse)
async def get_ticker_history(ticker: str, session: AsyncSession = Depends(get_session)):
    since = date.today() - timedelta(days=30)
    stmt = (
        select(Prediction)
        .where(Prediction.ticker == ticker.upper(), Prediction.date >= since)
        .order_by(Prediction.date.desc())
    )
    result = await session.execute(stmt)
    predictions = result.scalars().all()
    return ForecastListResponse(
        forecasts=[ForecastResponse.model_validate(p) for p in predictions],
        count=len(predictions),
    )
