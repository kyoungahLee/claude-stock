"use client";

import Link from "next/link";
import { Forecast } from "@/lib/api";

function DirectionIcon({ direction }: { direction: "UP" | "DOWN" | "FLAT" }) {
  if (direction === "UP") {
    return (
      <svg
        className="h-5 w-5 text-emerald-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 11l5-5m0 0l5 5m-5-5v12"
        />
      </svg>
    );
  }
  if (direction === "DOWN") {
    return (
      <svg
        className="h-5 w-5 text-red-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 13l-5 5m0 0l-5-5m5 5V6"
        />
      </svg>
    );
  }
  return (
    <svg
      className="h-5 w-5 text-gray-400"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20 12H4"
      />
    </svg>
  );
}

function directionColor(direction: "UP" | "DOWN" | "FLAT") {
  switch (direction) {
    case "UP":
      return "text-emerald-400";
    case "DOWN":
      return "text-red-400";
    default:
      return "text-gray-400";
  }
}

function directionBadgeClass(direction: "UP" | "DOWN" | "FLAT") {
  switch (direction) {
    case "UP":
      return "badge-green";
    case "DOWN":
      return "badge-red";
    default:
      return "badge-gray";
  }
}

export default function StockCard({ forecast }: { forecast: Forecast }) {
  const changeColor =
    forecast.change_percent >= 0 ? "text-emerald-400" : "text-red-400";

  return (
    <Link href={`/forecast/${forecast.ticker}`}>
      <div className="card cursor-pointer group">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white group-hover:text-terminal-accent transition-colors">
                {forecast.ticker}
              </h3>
              <span className="text-xs text-gray-500">
                {forecast.market === "KR" ? "KRX" : "NYSE/NASDAQ"}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-gray-400 truncate max-w-[140px]">
              {forecast.name}
            </p>
          </div>
          <div className="flex items-center gap-1">
            <DirectionIcon direction={forecast.direction} />
            <span
              className={`badge ${directionBadgeClass(forecast.direction)}`}
            >
              {forecast.direction}
            </span>
          </div>
        </div>

        <div className="mt-4 flex items-end justify-between">
          <div>
            <p className="text-lg font-semibold text-white font-mono">
              {forecast.currency === "KRW" ? "₩" : "$"}
              {forecast.last_price.toLocaleString()}
            </p>
            <p className={`text-xs ${changeColor} font-mono`}>
              {forecast.change_percent >= 0 ? "+" : ""}
              {forecast.change_percent.toFixed(2)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Confidence</p>
            <p
              className={`text-sm font-bold ${directionColor(forecast.direction)} font-mono`}
            >
              {(forecast.confidence * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}
