from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from src.config import ROOT_DIR

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORTS_DIR = ROOT_DIR / "reports"
STOCK_REPORTS_DIR = REPORTS_DIR / "stocks"


@router.get("")
async def list_reports():
    """날짜별 전체 리포트 목록 반환"""
    reports = []

    for f in sorted(REPORTS_DIR.glob("*_forecast.md"), reverse=True):
        reports.append({
            "type": "forecast",
            "date": f.stem.split("_forecast")[0],
            "filename": f.name,
        })

    for f in sorted(REPORTS_DIR.glob("*_closing_*.md"), reverse=True):
        parts = f.stem.split("_closing_")
        reports.append({
            "type": "closing",
            "date": parts[0],
            "market": parts[1] if len(parts) > 1 else "all",
            "filename": f.name,
        })

    return {"reports": reports, "count": len(reports)}


@router.get("/daily/{report_date}", response_class=PlainTextResponse)
async def get_daily_report(report_date: str):
    """특정 날짜의 전체 전망 리포트"""
    path = REPORTS_DIR / f"{report_date}_forecast.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"No forecast report for {report_date}")
    return path.read_text(encoding="utf-8")


@router.get("/closing/{report_date}/{market}", response_class=PlainTextResponse)
async def get_closing_report(report_date: str, market: str = "us"):
    """특정 날짜의 마감 리포트"""
    path = REPORTS_DIR / f"{report_date}_closing_{market}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"No closing report for {report_date} ({market})")
    return path.read_text(encoding="utf-8")


@router.get("/stock/{ticker}")
async def list_stock_reports(ticker: str):
    """특정 종목의 날짜별 리포트 목록"""
    safe_symbol = ticker.replace(".", "_")
    reports = []
    for f in sorted(STOCK_REPORTS_DIR.glob(f"*_{safe_symbol}.md"), reverse=True):
        report_date = f.stem.replace(f"_{safe_symbol}", "")
        reports.append({
            "date": report_date,
            "ticker": ticker,
            "filename": f.name,
        })
    return {"reports": reports, "count": len(reports)}


@router.get("/stock/{ticker}/{report_date}", response_class=PlainTextResponse)
async def get_stock_report(ticker: str, report_date: str):
    """특정 종목의 특정 날짜 리포트"""
    safe_symbol = ticker.replace(".", "_")
    path = STOCK_REPORTS_DIR / f"{report_date}_{safe_symbol}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"No report for {ticker} on {report_date}")
    return path.read_text(encoding="utf-8")
