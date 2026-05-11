import logging
import subprocess
import sys
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import ROOT_DIR

logger = logging.getLogger(__name__)


def _run_script(script_name: str, market: str = "all"):
    script_path = ROOT_DIR / "scripts" / script_name
    env_vars = {"PYTHONPATH": str(ROOT_DIR), "MARKET_FILTER": market}
    import os
    env = {**os.environ, **env_vars}

    logger.info(f"Running {script_name} (market={market})...")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        env=env,
    )
    if result.returncode != 0:
        logger.error(f"{script_name} failed:\n{result.stderr}")
    else:
        logger.info(f"{script_name} completed successfully")
    return result.returncode == 0


async def pre_market_forecast_kr():
    """한국 장 시작 전: 한국 종목 전망 생성"""
    logger.info(f"[KR] Pre-market forecast triggered for {date.today()}")
    _run_script("run_forecast.py", market="korea")


async def pre_market_forecast_us():
    """미국 장 시작 전: 미국 종목 전망 생성"""
    logger.info(f"[US] Pre-market forecast triggered for {date.today()}")
    _run_script("run_forecast.py", market="us")


async def post_market_kr():
    """한국 장 마감 후: 마감 가격 반영 + 백테스팅 + 마감 리포트"""
    logger.info(f"[KR] Post-market closing report for {date.today()}")
    _run_script("run_closing_report.py", market="korea")
    _run_script("run_backtest.py", market="korea")


async def post_market_us():
    """미국 장 마감 후: 마감 가격 반영 + 백테스팅 + 마감 리포트"""
    logger.info(f"[US] Post-market closing report for {date.today()}")
    _run_script("run_closing_report.py", market="us")
    _run_script("run_backtest.py", market="us")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 한국 시장 (KRX)
    # 장 시간: 09:00~15:30 KST
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    scheduler.add_job(
        pre_market_forecast_kr,
        trigger=CronTrigger(hour=8, minute=0, day_of_week="mon-fri", timezone="Asia/Seoul"),
        id="pre_market_forecast_kr",
        name="[KR] Pre-Market Forecast (08:00 KST)",
        replace_existing=True,
    )

    scheduler.add_job(
        post_market_kr,
        trigger=CronTrigger(hour=16, minute=0, day_of_week="mon-fri", timezone="Asia/Seoul"),
        id="post_market_kr",
        name="[KR] Post-Market Closing Report (16:00 KST)",
        replace_existing=True,
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 미국 시장 (NYSE/NASDAQ)
    # 장 시간: 09:30~16:00 EST = 23:30~06:00 KST (서머타임 시 22:30~05:00)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    scheduler.add_job(
        pre_market_forecast_us,
        trigger=CronTrigger(hour=22, minute=0, day_of_week="mon-fri", timezone="Asia/Seoul"),
        id="pre_market_forecast_us",
        name="[US] Pre-Market Forecast (22:00 KST)",
        replace_existing=True,
    )

    scheduler.add_job(
        post_market_us,
        trigger=CronTrigger(hour=6, minute=30, day_of_week="tue-sat", timezone="Asia/Seoul"),
        id="post_market_us",
        name="[US] Post-Market Closing Report (06:30 KST next day)",
        replace_existing=True,
    )

    return scheduler
