"use client";

import { useState } from "react";

interface NewsSummaryProps {
  summary: string;
  title?: string;
}

export default function NewsSummary({
  summary,
  title = "News Summary",
}: NewsSummaryProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!summary) {
    return null;
  }

  const previewLength = 150;
  const isLong = summary.length > previewLength;
  const displayText =
    isLong && !isExpanded ? summary.slice(0, previewLength) + "..." : summary;

  return (
    <div className="card">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-left"
      >
        <h3 className="text-sm font-semibold text-gray-300">{title}</h3>
        <svg
          className={`h-4 w-4 text-gray-500 transition-transform duration-200 ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      <div
        className={`mt-3 overflow-hidden transition-all duration-300 ${
          isExpanded ? "max-h-96" : "max-h-20"
        }`}
      >
        <p className="text-sm leading-relaxed text-gray-400">{displayText}</p>
      </div>
      {isLong && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-2 text-xs text-terminal-accent hover:text-terminal-accent/80 transition-colors"
        >
          {isExpanded ? "Show less" : "Read more"}
        </button>
      )}
    </div>
  );
}
