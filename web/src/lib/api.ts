const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface Forecast {
  ticker: string;
  name: string;
  market: "KR" | "US";
  direction: "UP" | "DOWN" | "FLAT";
  confidence: number;
  last_price: number;
  currency: string;
  change_percent: number;
  analysis_summary: string;
  news_summary?: string;
  technical_indicators?: {
    rsi: number;
    macd: string;
    moving_avg_20: number;
    moving_avg_50: number;
    volume_trend: string;
  };
  created_at: string;
}

export interface ForecastHistory {
  ticker: string;
  name: string;
  history: {
    date: string;
    direction: "UP" | "DOWN" | "FLAT";
    confidence: number;
    actual_direction?: "UP" | "DOWN" | "FLAT";
    correct?: boolean;
    price: number;
  }[];
}

export interface BacktestScores {
  overall_accuracy: number;
  total_predictions: number;
  correct_predictions: number;
  by_market: {
    KR: { accuracy: number; total: number; correct: number };
    US: { accuracy: number; total: number; correct: number };
  };
  by_direction: {
    UP: { accuracy: number; total: number };
    DOWN: { accuracy: number; total: number };
    FLAT: { accuracy: number; total: number };
  };
  recent_7d_accuracy: number;
  recent_30d_accuracy: number;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
}

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    next: { revalidate: 60 },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function getHealth(): Promise<HealthStatus> {
  return fetchAPI<HealthStatus>("/api/health");
}

export async function getForecasts(): Promise<Forecast[]> {
  return fetchAPI<Forecast[]>("/api/forecasts");
}

export async function getForecast(ticker: string): Promise<Forecast> {
  return fetchAPI<Forecast>(`/api/forecasts/${ticker}`);
}

export async function getForecastHistory(
  ticker: string
): Promise<ForecastHistory> {
  return fetchAPI<ForecastHistory>(`/api/forecasts/history/${ticker}`);
}

export async function getBacktestScores(): Promise<BacktestScores> {
  return fetchAPI<BacktestScores>("/api/backtests/scores");
}
