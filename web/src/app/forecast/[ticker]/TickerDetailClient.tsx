"use client";

import Link from "next/link";
import ForecastChart from "@/components/ForecastChart";
import AccuracyBadge from "@/components/AccuracyBadge";
import NewsSummary from "@/components/NewsSummary";
import { Forecast, ForecastHistory } from "@/lib/api";

interface TickerDetailClientProps {
  ticker: string;
  forecast: Forecast | null;
  history: ForecastHistory | null;
  error: string | null;
}

function DirectionBadge({ direction }: { direction: "UP" | "DOWN" | "FLAT" }) {
  const config = {
    UP: {
      bg: "bg-emerald-500/10",
      text: "text-emerald-400",
      ring: "ring-emerald-500/20",
      icon: "M7 11l5-5m0 0l5 5m-5-5v12",
    },
    DOWN: {
      bg: "bg-red-500/10",
      text: "text-red-400",
      ring: "ring-red-500/20",
      icon: "M17 13l-5 5m0 0l-5-5m5 5V6",
    },
    FLAT: {
      bg: "bg-gray-500/10",
      text: "text-gray-400",
      ring: "ring-gray-500/20",
      icon: "M20 12H4",
    },
  };

  const c = config[direction];

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full px-4 py-2 ${c.bg} ring-1 ${c.ring}`}
    >
      <svg
        className={`h-5 w-5 ${c.text}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d={c.icon}
        />
      </svg>
      <span className={`text-sm font-bold ${c.text}`}>{direction}</span>
    </div>
  );
}

function TechnicalIndicators({
  indicators,
}: {
  indicators: Forecast["technical_indicators"];
}) {
  if (!indicators) return null;

  const items = [
    { label: "RSI (14)", value: indicators.rsi.toFixed(1), warn: indicators.rsi > 70 || indicators.rsi < 30 },
    { label: "MACD", value: indicators.macd },
    { label: "MA 20", value: indicators.moving_avg_20.toLocaleString() },
    { label: "MA 50", value: indicators.moving_avg_50.toLocaleString() },
    { label: "Volume Trend", value: indicators.volume_trend },
  ];

  return (
    <div className="card">
      <h3 className="mb-4 text-sm font-semibold text-gray-300">
        Technical Indicators
      </h3>
      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between border-b border-terminal-border/50 pb-2 last:border-0"
          >
            <span className="text-xs text-gray-500">{item.label}</span>
            <span className={`text-sm font-mono ${item.warn ? "text-amber-400" : "text-white"}`}>
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TickerDetailClient({
  ticker,
  forecast,
  history,
  error,
}: TickerDetailClientProps) {
  if (error || !forecast) {
    return (
      <div className="space-y-4">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Dashboard
        </Link>
        <div className="flex h-[50vh] items-center justify-center">
          <div className="card max-w-md text-center">
            <p className="text-sm text-gray-400">
              {error || `No data available for ${ticker}`}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const chartData = history?.history.map((h) => ({
    date: new Date(h.date).toLocaleDateString("ko-KR", {
      month: "short",
      day: "numeric",
    }),
    price: h.price,
    predicted_direction: h.direction,
    correct: h.correct,
  })) || [];

  const accuracyRate = history
    ? history.history.filter((h) => h.correct).length /
      history.history.filter((h) => h.correct !== undefined).length
    : 0;

  return (
    <div className="space-y-6">
      {/* Back navigation */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back to Dashboard
      </Link>

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white">{forecast.ticker}</h1>
            <span className="rounded bg-terminal-border px-2 py-0.5 text-xs text-gray-400">
              {forecast.market === "KR" ? "KRX" : "NYSE/NASDAQ"}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-400">{forecast.name}</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-2xl font-bold text-white font-mono">
              {forecast.currency === "KRW" ? "₩" : "$"}
              {forecast.last_price.toLocaleString()}
            </p>
            <p
              className={`text-sm font-mono ${
                forecast.change_percent >= 0
                  ? "text-emerald-400"
                  : "text-red-400"
              }`}
            >
              {forecast.change_percent >= 0 ? "+" : ""}
              {forecast.change_percent.toFixed(2)}%
            </p>
          </div>
          <DirectionBadge direction={forecast.direction} />
        </div>
      </div>

      {/* Forecast Summary Card */}
      <div className="card">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-300 mb-2">
              AI Forecast
            </h3>
            <p className="text-sm leading-relaxed text-gray-400">
              {forecast.analysis_summary}
            </p>
          </div>
          <div className="flex items-center gap-6">
            <AccuracyBadge
              accuracy={forecast.confidence}
              size="md"
              label="Confidence"
            />
            {history && !isNaN(accuracyRate) && (
              <AccuracyBadge
                accuracy={accuracyRate}
                size="md"
                label="30d Accuracy"
              />
            )}
          </div>
        </div>
      </div>

      {/* Chart and Indicators Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ForecastChart
            data={chartData}
            title="Price History & Predictions (30 Days)"
            showAccuracy={true}
          />
        </div>
        <div>
          <TechnicalIndicators indicators={forecast.technical_indicators} />
        </div>
      </div>

      {/* News Summary */}
      {forecast.news_summary && (
        <NewsSummary summary={forecast.news_summary} title="Latest News & Analysis" />
      )}

      {/* Forecast History Table */}
      {history && history.history.length > 0 && (
        <div className="card">
          <h3 className="mb-4 text-sm font-semibold text-gray-300">
            Prediction History
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-terminal-border text-left">
                  <th className="pb-2 text-xs font-medium text-gray-500">
                    Date
                  </th>
                  <th className="pb-2 text-xs font-medium text-gray-500">
                    Predicted
                  </th>
                  <th className="pb-2 text-xs font-medium text-gray-500">
                    Actual
                  </th>
                  <th className="pb-2 text-xs font-medium text-gray-500">
                    Confidence
                  </th>
                  <th className="pb-2 text-xs font-medium text-gray-500">
                    Result
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-terminal-border/50">
                {history.history.slice(-10).reverse().map((h, i) => (
                  <tr key={i} className="text-gray-300">
                    <td className="py-2 font-mono text-xs">
                      {new Date(h.date).toLocaleDateString("ko-KR")}
                    </td>
                    <td className="py-2">
                      <span
                        className={`text-xs font-medium ${
                          h.direction === "UP"
                            ? "text-emerald-400"
                            : h.direction === "DOWN"
                              ? "text-red-400"
                              : "text-gray-400"
                        }`}
                      >
                        {h.direction}
                      </span>
                    </td>
                    <td className="py-2">
                      {h.actual_direction ? (
                        <span
                          className={`text-xs font-medium ${
                            h.actual_direction === "UP"
                              ? "text-emerald-400"
                              : h.actual_direction === "DOWN"
                                ? "text-red-400"
                                : "text-gray-400"
                          }`}
                        >
                          {h.actual_direction}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-600">-</span>
                      )}
                    </td>
                    <td className="py-2 font-mono text-xs">
                      {(h.confidence * 100).toFixed(0)}%
                    </td>
                    <td className="py-2">
                      {h.correct !== undefined ? (
                        <span
                          className={`badge ${
                            h.correct ? "badge-green" : "badge-red"
                          }`}
                        >
                          {h.correct ? "Correct" : "Wrong"}
                        </span>
                      ) : (
                        <span className="badge badge-gray">Pending</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
