import DashboardClient from "./DashboardClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const TICKER_NAMES: Record<string, string> = {
  "005930.KS": "삼성전자",
  "000660.KS": "SK하이닉스",
  "373220.KS": "LG에너지솔루션",
  "005380.KS": "현대자동차",
  "035420.KS": "NAVER",
  "035720.KS": "카카오",
  "006400.KS": "삼성SDI",
  "051910.KS": "LG화학",
  AAPL: "Apple",
  NVDA: "NVIDIA",
  MSFT: "Microsoft",
  GOOGL: "Alphabet",
  AMZN: "Amazon",
  TSLA: "Tesla",
  META: "Meta Platforms",
  AMD: "AMD",
  WMT: "Walmart",
  PLTR: "Palantir Technologies",
  QCOM: "Qualcomm",
  SNOW: "Snowflake",
  V: "Visa",
  LLY: "Eli Lilly & Co",
  TLN: "Talen Energy Corp",
  ORCL: "Oracle",
  CNI: "Canadian National Railway",
  AVGO: "Broadcom",
  COST: "Costco",
  NFLX: "Netflix",
  UBER: "Uber",
  COIN: "Coinbase",
  ARM: "ARM Holdings",
  NOW: "ServiceNow",
  CRWD: "CrowdStrike",
};

async function fetchForecasts() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/forecasts", {
      cache: "no-store",
    });
    const data = await res.json();
    const forecasts = data.forecasts || [];
    return forecasts.map((f: any) => ({
      ticker: f.ticker || "",
      name: TICKER_NAMES[f.ticker] || f.ticker || "",
      market: (f.ticker || "").includes(".KS") ? "KR" : "US",
      direction: f.direction || "FLAT",
      confidence: f.confidence || 0,
      last_price: f.last_price || 0,
      currency: (f.ticker || "").includes(".KS") ? "KRW" : "USD",
      change_percent: f.change_pct || f.actual_change || 0,
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
