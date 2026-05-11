import TickerDetailClient from "./TickerDetailClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

interface PageProps {
  params: { ticker: string };
}

async function fetchTickerData(ticker: string) {
  try {
    const [forecastRes, historyRes, reportRes] = await Promise.all([
      fetch(`http://127.0.0.1:8000/api/forecasts/${ticker}`, { cache: "no-store" }),
      fetch(`http://127.0.0.1:8000/api/forecasts/history/${ticker}`, { cache: "no-store" }),
      fetch(`http://127.0.0.1:8000/api/forecasts/report/${ticker}`, { cache: "no-store" }),
    ]);

    const forecast = forecastRes.ok ? await forecastRes.json() : null;
    const historyData = historyRes.ok ? await historyRes.json() : null;
    const report = reportRes.ok ? await reportRes.text() : null;

    return { forecast, history: historyData, report };
  } catch {
    return { forecast: null, history: null, report: null };
  }
}

export default async function TickerDetailPage({ params }: PageProps) {
  const { ticker } = params;
  const { forecast, history, report } = await fetchTickerData(ticker);

  return (
    <TickerDetailClient
      ticker={ticker}
      forecast={forecast}
      history={history}
      report={report}
      error={null}
    />
  );
}
