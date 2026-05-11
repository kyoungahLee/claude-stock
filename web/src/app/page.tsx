import { getForecasts } from "@/lib/api";
import DashboardClient from "./DashboardClient";

export default async function DashboardPage() {
  let forecasts: any[] = [];
  let error: string | null = null;

  try {
    forecasts = await getForecasts();
  } catch (e) {
    error = "Failed to load forecasts. Is the backend running on localhost:8000?";
  }

  return <DashboardClient initialForecasts={forecasts} error={error} />;
}
