import { getBacktestScores } from "@/lib/api";
import HistoryClient from "./HistoryClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function HistoryPage() {
  const scores = await getBacktestScores();
  return <HistoryClient scores={scores} error={null} />;
}
