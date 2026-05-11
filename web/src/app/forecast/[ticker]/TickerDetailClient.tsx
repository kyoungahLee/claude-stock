"use client";

import { useState } from "react";
import Link from "next/link";
import AccuracyBadge from "@/components/AccuracyBadge";

interface TickerDetailClientProps {
  ticker: string;
  forecast: any | null;
  history: any | null;
  report: string | null;
  error: string | null;
}

function DirectionBadge({ direction }: { direction: string }) {
  const config: Record<string, { bg: string; text: string; ring: string; icon: string }> = {
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

  const c = config[direction] || config.FLAT;

  return (
    <div className={`inline-flex items-center gap-2 rounded-full px-4 py-2 ${c.bg} ring-1 ${c.ring}`}>
      <svg className={`h-5 w-5 ${c.text}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={c.icon} />
      </svg>
      <span className={`text-sm font-bold ${c.text}`}>{direction}</span>
    </div>
  );
}

export default function TickerDetailClient({
  ticker,
  forecast,
  history,
  report,
  error,
}: TickerDetailClientProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "report">("overview");

  if (error || !forecast) {
    return (
      <div className="space-y-4">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </Link>
        <div className="flex h-[50vh] items-center justify-center">
          <div className="card max-w-md text-center">
            <p className="text-sm text-gray-400">{error || `No data available for ${ticker}`}</p>
          </div>
        </div>
      </div>
    );
  }

  const predictions = history?.forecasts || [];

  return (
    <div className="space-y-6">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </Link>

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white">{ticker}</h1>
            <span className="rounded bg-terminal-border px-2 py-0.5 text-xs text-gray-400">
              {ticker.includes(".KS") ? "KRX" : "NYSE/NASDAQ"}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-400">{forecast.date}</p>
        </div>
        <div className="flex items-center gap-4">
          <AccuracyBadge accuracy={forecast.confidence} size="md" label="Confidence" />
          <DirectionBadge direction={forecast.direction} />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 rounded-lg border border-terminal-border bg-terminal-card p-1">
        <button
          onClick={() => setActiveTab("overview")}
          className={`rounded-md px-4 py-2 text-sm font-medium transition-all ${
            activeTab === "overview" ? "bg-terminal-accent text-white shadow-sm" : "text-gray-400 hover:text-white"
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab("report")}
          className={`rounded-md px-4 py-2 text-sm font-medium transition-all ${
            activeTab === "report" ? "bg-terminal-accent text-white shadow-sm" : "text-gray-400 hover:text-white"
          }`}
        >
          Daily Report (EN/KR)
        </button>
      </div>

      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Forecast Card */}
          <div className="card">
            <h3 className="mb-4 text-sm font-semibold text-gray-300">Forecast Summary</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-lg border border-terminal-border p-4">
                <p className="text-xs text-gray-500 mb-1">Direction</p>
                <DirectionBadge direction={forecast.direction} />
              </div>
              <div className="rounded-lg border border-terminal-border p-4">
                <p className="text-xs text-gray-500 mb-1">Confidence</p>
                <p className="text-2xl font-bold text-white font-mono">{(forecast.confidence * 100).toFixed(0)}%</p>
              </div>
              <div className="rounded-lg border border-terminal-border p-4">
                <p className="text-xs text-gray-500 mb-1">Score</p>
                <p className={`text-2xl font-bold font-mono ${forecast.score > 0 ? "text-emerald-400" : forecast.score < 0 ? "text-red-400" : "text-gray-400"}`}>
                  {forecast.score > 0 ? "+" : ""}{forecast.score.toFixed(4)}
                </p>
              </div>
            </div>
          </div>

          {/* Prediction History Table */}
          {predictions.length > 0 && (
            <div className="card">
              <h3 className="mb-4 text-sm font-semibold text-gray-300">Prediction History</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-terminal-border text-left">
                      <th className="pb-2 text-xs font-medium text-gray-500">Date</th>
                      <th className="pb-2 text-xs font-medium text-gray-500">Predicted</th>
                      <th className="pb-2 text-xs font-medium text-gray-500">Actual</th>
                      <th className="pb-2 text-xs font-medium text-gray-500">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-terminal-border/50">
                    {predictions.slice(0, 10).map((h: any, i: number) => (
                      <tr key={i} className="text-gray-300">
                        <td className="py-2 font-mono text-xs">{h.date}</td>
                        <td className="py-2">
                          <span className={`text-xs font-medium ${
                            h.direction === "UP" ? "text-emerald-400" : h.direction === "DOWN" ? "text-red-400" : "text-gray-400"
                          }`}>
                            {h.direction}
                          </span>
                        </td>
                        <td className="py-2">
                          {h.actual_direction ? (
                            <span className={`text-xs font-medium ${
                              h.actual_direction === "UP" ? "text-emerald-400" : h.actual_direction === "DOWN" ? "text-red-400" : "text-gray-400"
                            }`}>
                              {h.actual_direction}
                            </span>
                          ) : (
                            <span className="text-xs text-gray-600">Pending</span>
                          )}
                        </td>
                        <td className="py-2 font-mono text-xs">{(h.confidence * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "report" && (
        <div className="card">
          <h3 className="mb-4 text-sm font-semibold text-gray-300">
            Daily Forecast Report — {ticker}
          </h3>
          {report ? (
            <div className="prose prose-invert prose-sm max-w-none overflow-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-300 leading-relaxed font-sans">{report}</pre>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No report available for today. Run the forecast first.</p>
          )}
        </div>
      )}
    </div>
  );
}
