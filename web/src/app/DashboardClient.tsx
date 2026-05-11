"use client";

import { useState } from "react";
import StockCard from "@/components/StockCard";
import { Forecast } from "@/lib/api";

type MarketTab = "ALL" | "KR" | "US";

interface DashboardClientProps {
  initialForecasts: Forecast[];
  error: string | null;
}

function MarketSummary({ forecasts }: { forecasts: Forecast[] }) {
  const upCount = forecasts.filter((f) => f.direction === "UP").length;
  const downCount = forecasts.filter((f) => f.direction === "DOWN").length;
  const flatCount = forecasts.filter((f) => f.direction === "FLAT").length;
  const avgConfidence =
    forecasts.length > 0
      ? forecasts.reduce((sum, f) => sum + f.confidence, 0) / forecasts.length
      : 0;

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <div className="card">
        <p className="text-xs text-gray-500 uppercase tracking-wider">
          Total Stocks
        </p>
        <p className="mt-1 text-2xl font-bold text-white font-mono">
          {forecasts.length}
        </p>
      </div>
      <div className="card">
        <p className="text-xs text-gray-500 uppercase tracking-wider">
          Bullish
        </p>
        <p className="mt-1 text-2xl font-bold text-emerald-400 font-mono">
          {upCount}
        </p>
      </div>
      <div className="card">
        <p className="text-xs text-gray-500 uppercase tracking-wider">
          Bearish
        </p>
        <p className="mt-1 text-2xl font-bold text-red-400 font-mono">
          {downCount}
        </p>
      </div>
      <div className="card">
        <p className="text-xs text-gray-500 uppercase tracking-wider">
          Avg Confidence
        </p>
        <p className="mt-1 text-2xl font-bold text-terminal-accent font-mono">
          {(avgConfidence * 100).toFixed(0)}%
        </p>
      </div>
    </div>
  );
}

export default function DashboardClient({
  initialForecasts,
  error,
}: DashboardClientProps) {
  const [activeTab, setActiveTab] = useState<MarketTab>("ALL");

  if (error) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="card max-w-md text-center">
          <div className="mx-auto h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center">
            <svg
              className="h-6 w-6 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <p className="mt-4 text-sm text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  const filteredForecasts =
    activeTab === "ALL"
      ? initialForecasts
      : initialForecasts.filter((f) => f.market === activeTab);

  const tabs: { key: MarketTab; label: string }[] = [
    { key: "ALL", label: "All Markets" },
    { key: "KR", label: "Korean (KRX)" },
    { key: "US", label: "US (NYSE/NASDAQ)" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Market Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            AI-powered stock forecasts for today
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">Last updated</p>
          <p className="text-sm text-gray-300 font-mono">
            {new Date().toLocaleString("ko-KR", {
              timeZone: "Asia/Seoul",
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
      </div>

      {/* Market Summary */}
      <MarketSummary forecasts={filteredForecasts} />

      {/* Market Tabs */}
      <div className="flex items-center gap-1 rounded-lg border border-terminal-border bg-terminal-card p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-all ${
              activeTab === tab.key
                ? "bg-terminal-accent text-white shadow-sm"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Stock Cards Grid */}
      {filteredForecasts.length === 0 ? (
        <div className="card flex h-48 items-center justify-center">
          <p className="text-sm text-gray-500">
            No forecasts available for this market
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredForecasts.map((forecast) => (
            <StockCard key={forecast.ticker} forecast={forecast} />
          ))}
        </div>
      )}
    </div>
  );
}
