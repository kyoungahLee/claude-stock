const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window === "undefined" ? "http://127.0.0.1:8000" : "");

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
  const res = await fetch(url, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function getHealth(): Promise<HealthStatus> {
  return fetchAPI<HealthStatus>("/api/health");
}

export async function getForecasts(): Promise<Forecast[]> {
  const data = await fetchAPI<any>("/api/forecasts");
  const forecasts = data.forecasts || data || [];
  return forecasts.map((f: any) => ({
    ticker: f.ticker || "",
    name: f.name || f.ticker || "",
    market: (f.ticker || "").includes(".KS") ? "KR" : "US",
    direction: f.direction || "FLAT",
    confidence: f.confidence || 0,
    last_price: f.last_price || f.score || 0,
    currency: (f.ticker || "").includes(".KS") ? "KRW" : "USD",
    change_percent: f.change_percent || f.actual_change || 0,
    analysis_summary: f.analysis_summary || "",
    created_at: f.created_at || "",
  }));
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
  try {
    const data = await fetchAPI<any>("/api/backtests/scores");
    return {
      overall_accuracy: data.overall_accuracy || 0,
      total_predictions: data.total_predictions || 0,
      correct_predictions: data.correct_predictions || 0,
      by_market: data.by_market || {
        KR: { accuracy: 0, total: 0, correct: 0 },
        US: { accuracy: 0, total: 0, correct: 0 },
      },
      by_direction: data.by_direction || {
        UP: { accuracy: 0, total: 0 },
        DOWN: { accuracy: 0, total: 0 },
        FLAT: { accuracy: 0, total: 0 },
      },
      recent_7d_accuracy: data.recent_7d_accuracy || 0,
      recent_30d_accuracy: data.recent_30d_accuracy || 0,
    };
  } catch {
    return {
      overall_accuracy: 0,
      total_predictions: 0,
      correct_predictions: 0,
      by_market: {
        KR: { accuracy: 0, total: 0, correct: 0 },
        US: { accuracy: 0, total: 0, correct: 0 },
      },
      by_direction: {
        UP: { accuracy: 0, total: 0 },
        DOWN: { accuracy: 0, total: 0 },
        FLAT: { accuracy: 0, total: 0 },
      },
      recent_7d_accuracy: 0,
      recent_30d_accuracy: 0,
    };
  }
}
