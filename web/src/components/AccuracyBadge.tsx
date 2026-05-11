"use client";

interface AccuracyBadgeProps {
  accuracy: number;
  size?: "sm" | "md" | "lg";
  label?: string;
}

function getColor(accuracy: number): string {
  if (accuracy >= 0.7) return "#10b981";
  if (accuracy >= 0.5) return "#f59e0b";
  return "#ef4444";
}

function getTrackColor(accuracy: number): string {
  if (accuracy >= 0.7) return "rgba(16, 185, 129, 0.1)";
  if (accuracy >= 0.5) return "rgba(245, 158, 11, 0.1)";
  return "rgba(239, 68, 68, 0.1)";
}

export default function AccuracyBadge({
  accuracy,
  size = "md",
  label,
}: AccuracyBadgeProps) {
  const percentage = Math.round(accuracy * 100);
  const color = getColor(accuracy);
  const trackColor = getTrackColor(accuracy);

  const dimensions = {
    sm: { size: 48, strokeWidth: 4, fontSize: "text-xs" },
    md: { size: 72, strokeWidth: 5, fontSize: "text-sm" },
    lg: { size: 96, strokeWidth: 6, fontSize: "text-lg" },
  };

  const dim = dimensions[size];
  const radius = (dim.size - dim.strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - accuracy);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: dim.size, height: dim.size }}>
        <svg
          width={dim.size}
          height={dim.size}
          className="-rotate-90"
          viewBox={`0 0 ${dim.size} ${dim.size}`}
        >
          {/* Background track */}
          <circle
            cx={dim.size / 2}
            cy={dim.size / 2}
            r={radius}
            fill="none"
            stroke={trackColor}
            strokeWidth={dim.strokeWidth}
          />
          {/* Progress arc */}
          <circle
            cx={dim.size / 2}
            cy={dim.size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={dim.strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span
            className={`${dim.fontSize} font-bold font-mono`}
            style={{ color }}
          >
            {percentage}%
          </span>
        </div>
      </div>
      {label && <span className="text-xs text-gray-500">{label}</span>}
    </div>
  );
}
