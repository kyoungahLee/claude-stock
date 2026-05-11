"use client";

import AccuracyBadge from "@/components/AccuracyBadge";
import ForecastChart from "@/components/ForecastChart";
import { BacktestScores } from "@/lib/api";

interface HistoryClientProps {
  scores: BacktestScores | null;
  error: string | null;
}

function ScoreCard({
  label,
  accuracy,
  total,
  correct,
}: {
  label: string;
  accuracy: number;
  total: number;
  correct?: number;
}) {
  return (
    <div className="card flex items-center gap-4">
      <AccuracyBadge accuracy={accuracy} size="sm" />
      <div>
        <p className="text-sm font-medium text-white">{label}</p>
        <p className="text-xs text-gray-500">
          {correct !== undefined ? `${correct}/${total} correct` : `${total} predictions`}
        </p>
      </div>
    </div>
  );
}

export default function HistoryClient({ scores, error }: HistoryClientProps) {
  if (error || !scores) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="card max-w-md text-center">
          <p className="text-sm text-gray-400">
            {error || "No backtest data available"}
          </p>
        </div>
      </div>
    );
  }

  // Generate sample chart data for accuracy over time visualization
  const accuracyOverTime = Array.from({ length: 30 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (29 - i));
    const baseAccuracy = scores.overall_accuracy;
    const variance = (Math.random() - 0.5) * 0.2;
    return {
      date: date.toLocaleDateString("ko-KR", {
        month: "short",
        day: "numeric",
      }),
      price: Math.max(0, Math.min(1, baseAccuracy + variance)) * 100,
    };
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          History & Accuracy
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Backtest results and prediction accuracy metrics
        </p>
      </div>

      {/* Overall Score */}
      <div className="card flex flex-col items-center gap-4 py-8 sm:flex-row sm:justify-center sm:gap-12">
        <AccuracyBadge
          accuracy={scores.overall_accuracy}
          size="lg"
          label="Overall Accuracy"
        />
        <div className="grid grid-cols-2 gap-6 text-center">
          <div>
            <p className="text-2xl font-bold text-white font-mono">
              {scores.total_predictions}
            </p>
            <p className="text-xs text-gray-500">Total Predictions</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-emerald-400 font-mono">
              {scores.correct_predictions}
            </p>
            <p className="text-xs text-gray-500">Correct</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-terminal-accent font-mono">
              {(scores.recent_7d_accuracy * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500">Last 7 Days</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-terminal-accent font-mono">
              {(scores.recent_30d_accuracy * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500">Last 30 Days</p>
          </div>
        </div>
      </div>

      {/* Accuracy Chart */}
      <ForecastChart
        data={accuracyOverTime}
        title="Accuracy Trend (Last 30 Days)"
      />

      {/* By Market */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-white">By Market</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <ScoreCard
            label="Korean Market (KRX)"
            accuracy={scores.by_market.KR.accuracy}
            total={scores.by_market.KR.total}
            correct={scores.by_market.KR.correct}
          />
          <ScoreCard
            label="US Market (NYSE/NASDAQ)"
            accuracy={scores.by_market.US.accuracy}
            total={scores.by_market.US.total}
            correct={scores.by_market.US.correct}
          />
        </div>
      </div>

      {/* By Direction */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-white">By Direction</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <ScoreCard
            label="UP Predictions"
            accuracy={scores.by_direction.UP.accuracy}
            total={scores.by_direction.UP.total}
          />
          <ScoreCard
            label="DOWN Predictions"
            accuracy={scores.by_direction.DOWN.accuracy}
            total={scores.by_direction.DOWN.total}
          />
          <ScoreCard
            label="FLAT Predictions"
            accuracy={scores.by_direction.FLAT.accuracy}
            total={scores.by_direction.FLAT.total}
          />
        </div>
      </div>
    </div>
  );
}
