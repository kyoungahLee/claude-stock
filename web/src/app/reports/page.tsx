import ReportsClient from "./ReportsClient";

export const dynamic = "force-dynamic";
export const revalidate = 0;

async function fetchReports() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/reports", {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.reports || [];
  } catch {
    return [];
  }
}

export default async function ReportsPage() {
  const reports = await fetchReports();
  return <ReportsClient reports={reports} />;
}
