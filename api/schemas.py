from datetime import date, datetime

from pydantic import BaseModel


class ForecastResponse(BaseModel):
    id: int
    ticker: str
    date: date
    direction: str
    confidence: float
    score: float
    actual_direction: str | None = None
    actual_change: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ForecastListResponse(BaseModel):
    forecasts: list[ForecastResponse]
    count: int


class TickerAccuracy(BaseModel):
    ticker: str
    total_predictions: int
    correct_predictions: int
    accuracy: float


class BacktestScoresResponse(BaseModel):
    overall_accuracy: float
    total_predictions: int
    correct_predictions: int
    by_ticker: list[TickerAccuracy]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
