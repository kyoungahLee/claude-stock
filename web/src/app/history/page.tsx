import { getBacktestScores } from "@/lib/api";
import HistoryClient from "./HistoryClient";

export default async function HistoryPage() {
  let scores: any = null;
  let error: string | null = null;

  try {
    scores = await getBacktestScores();
  } catch (e) {
    error = "Failed to load backtest scores. Is the backend running?";
  }

  return <HistoryClient scores={scores} error={error} />;
}
