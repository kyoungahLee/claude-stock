import { getForecast, getForecastHistory } from "@/lib/api";
import TickerDetailClient from "./TickerDetailClient";

interface PageProps {
  params: { ticker: string };
}

export default async function TickerDetailPage({ params }: PageProps) {
  const { ticker } = params;
  let forecast: any = null;
  let history: any = null;
  let error: string | null = null;

  try {
    [forecast, history] = await Promise.all([
      getForecast(ticker),
      getForecastHistory(ticker),
    ]);
  } catch (e) {
    error = `Failed to load data for ${ticker}. Is the backend running?`;
  }

  return (
    <TickerDetailClient
      ticker={ticker}
      forecast={forecast}
      history={history}
      error={error}
    />
  );
}
