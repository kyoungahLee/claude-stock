import DashboardClient from "./DashboardClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

async function fetchForecasts() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/forecasts", {
      cache: "no-store",
    });
    const data = await res.json();
    const forecasts = data.forecasts || [];
    return forecasts.map((f: any) => ({
      ticker: f.ticker || "",
      name: f.name || f.ticker || "",
      market: (f.ticker || "").includes(".KS") ? "KR" : "US",
      direction: f.direction || "FLAT",
      confidence: f.confidence || 0,
      last_price: 0,
      currency: (f.ticker || "").includes(".KS") ? "KRW" : "USD",
      change_percent: f.actual_change || 0,
      analysis_summary: "",
      created_at: f.created_at || "",
    }));
  } catch (e) {
    console.error("Fetch error:", e);
    return [];
  }
}

export default async function DashboardPage() {
  const forecasts = await fetchForecasts();
  return <DashboardClient initialForecasts={forecasts} error={null} />;
}
