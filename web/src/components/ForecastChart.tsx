"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from "recharts";

interface ChartDataPoint {
  date: string;
  price: number;
  predicted_direction?: "UP" | "DOWN" | "FLAT";
  correct?: boolean;
}

interface ForecastChartProps {
  data: ChartDataPoint[];
  title?: string;
  showAccuracy?: boolean;
}

function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="rounded-lg border border-terminal-border bg-terminal-card p-3 shadow-xl">
        <p className="text-xs text-gray-400">{label}</p>
        <p className="mt-1 text-sm font-semibold text-white font-mono">
          {payload[0].value.toLocaleString()}
        </p>
        {data.predicted_direction && (
          <div className="mt-1 flex items-center gap-2">
            <span className="text-xs text-gray-400">Predicted:</span>
            <span
              className={`text-xs font-medium ${
                data.predicted_direction === "UP"
                  ? "text-emerald-400"
                  : data.predicted_direction === "DOWN"
                    ? "text-red-400"
                    : "text-gray-400"
              }`}
            >
              {data.predicted_direction}
            </span>
            {data.correct !== undefined && (
              <span
                className={`text-xs ${data.correct ? "text-emerald-400" : "text-red-400"}`}
              >
                {data.correct ? "Correct" : "Wrong"}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }
  return null;
}

export default function ForecastChart({
  data,
  title,
  showAccuracy = false,
}: ForecastChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="card flex h-64 items-center justify-center">
        <p className="text-sm text-gray-500">No chart data available</p>
      </div>
    );
  }

  return (
    <div className="card">
      {title && (
        <h3 className="mb-4 text-sm font-semibold text-gray-300">{title}</h3>
      )}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#2d3748"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              stroke="#6b7280"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#6b7280"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              domain={["auto", "auto"]}
              tickFormatter={(value) => value.toLocaleString()}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="price"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPrice)"
              dot={(props: any) => {
                const { cx, cy, payload } = props;
                if (showAccuracy && payload.correct !== undefined) {
                  return (
                    <circle
                      key={`dot-${props.index}`}
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill={payload.correct ? "#10b981" : "#ef4444"}
                      stroke="none"
                    />
                  );
                }
                return <circle key={`dot-${props.index}`} r={0} />;
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      {showAccuracy && (
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-500"></div>
            <span>Correct Prediction</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-2.5 w-2.5 rounded-full bg-red-500"></div>
            <span>Wrong Prediction</span>
          </div>
        </div>
      )}
    </div>
  );
}
