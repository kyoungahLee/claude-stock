"use client";

import { useState } from "react";

interface Report {
  type: string;
  date: string;
  market?: string;
  filename: string;
}

export default function ReportsClient({ reports }: { reports: Report[] }) {
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [reportContent, setReportContent] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const loadReport = async (report: Report) => {
    setLoading(true);
    try {
      let url = "";
      if (report.type === "forecast") {
        url = `/api/reports/daily/${report.date}`;
      } else if (report.type === "closing") {
        url = `/api/reports/closing/${report.date}/${report.market || "us"}`;
      }

      const res = await fetch(url);
      if (res.ok) {
        const text = await res.text();
        setReportContent(text);
        setSelectedReport(report.filename);
      }
    } catch {
      setReportContent("Failed to load report.");
    }
    setLoading(false);
  };

  const forecastReports = reports.filter((r) => r.type === "forecast");
  const closingReports = reports.filter((r) => r.type === "closing");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Reports / 리포트</h1>
        <p className="mt-1 text-sm text-gray-500">
          날짜별 생성된 전망 리포트와 마감 리포트를 확인합니다
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Report List */}
        <div className="space-y-4">
          {/* Forecast Reports */}
          <div className="card">
            <h3 className="mb-3 text-sm font-semibold text-gray-300">
              📈 Forecast Reports / 전망 리포트
            </h3>
            <div className="space-y-1">
              {forecastReports.length === 0 && (
                <p className="text-xs text-gray-500">No reports yet</p>
              )}
              {forecastReports.map((r) => (
                <button
                  key={r.filename}
                  onClick={() => loadReport(r)}
                  className={`w-full text-left rounded-md px-3 py-2 text-sm transition-all ${
                    selectedReport === r.filename
                      ? "bg-terminal-accent text-white"
                      : "text-gray-400 hover:bg-terminal-border hover:text-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono">{r.date}</span>
                    <span className="text-xs text-gray-500">Daily</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Closing Reports */}
          <div className="card">
            <h3 className="mb-3 text-sm font-semibold text-gray-300">
              📊 Closing Reports / 마감 리포트
            </h3>
            <div className="space-y-1">
              {closingReports.length === 0 && (
                <p className="text-xs text-gray-500">No reports yet</p>
              )}
              {closingReports.map((r) => (
                <button
                  key={r.filename}
                  onClick={() => loadReport(r)}
                  className={`w-full text-left rounded-md px-3 py-2 text-sm transition-all ${
                    selectedReport === r.filename
                      ? "bg-terminal-accent text-white"
                      : "text-gray-400 hover:bg-terminal-border hover:text-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono">{r.date}</span>
                    <span className="text-xs text-gray-500">
                      {r.market?.toUpperCase()}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Report Content */}
        <div className="lg:col-span-2">
          <div className="card min-h-[600px]">
            {loading ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-gray-500">Loading...</p>
              </div>
            ) : reportContent ? (
              <div className="prose prose-invert prose-sm max-w-none overflow-auto">
                <pre className="whitespace-pre-wrap text-sm text-gray-300 leading-relaxed font-sans">
                  {reportContent}
                </pre>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-gray-500">
                  ← 왼쪽에서 리포트를 선택하세요
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
