from datetime import date, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import ForecastListResponse, ForecastResponse
from src.config import ROOT_DIR
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


@router.get("/report/{ticker}", response_class=PlainTextResponse)
async def get_ticker_report(ticker: str):
    today = date.today().strftime("%Y-%m-%d")
    safe_symbol = ticker.replace(".", "_")
    report_path = ROOT_DIR / "reports" / "stocks" / f"{today}_{safe_symbol}.md"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"No report for {ticker} today")
    return report_path.read_text(encoding="utf-8")
