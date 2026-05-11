import logging
import subprocess
import sys
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import ROOT_DIR

logger = logging.getLogger(__name__)


def _run_forecast_script():
    script_path = ROOT_DIR / "scripts" / "run_forecast.py"
    logger.info("Starting forecast pipeline...")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
    )
    if result.returncode != 0:
        logger.error(f"Forecast pipeline failed:\n{result.stderr}")
    else:
        logger.info("Forecast pipeline completed successfully")
    return result.returncode == 0


async def pre_market_forecast_kr():
    logger.info(f"[KR] Pre-market forecast triggered for {date.today()}")
    _run_forecast_script()


async def pre_market_forecast_us():
    logger.info(f"[US] Pre-market forecast triggered for {date.today()}")
    _run_forecast_script()


async def post_market_evaluate_kr():
    logger.info(f"[KR] Post-market evaluation triggered for {date.today()}")
    # Evaluation logic to be integrated with backtest module
    pass


async def post_market_evaluate_us():
    logger.info(f"[US] Post-market evaluation triggered for {date.today()}")
    # Evaluation logic to be integrated with backtest module
    pass


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # KR market: forecast at 08:00 KST on weekdays
    scheduler.add_job(
        pre_market_forecast_kr,
        trigger=CronTrigger(hour=8, minute=0, day_of_week="mon-fri", timezone="Asia/Seoul"),
        id="pre_market_forecast_kr",
        name="KR Pre-Market Forecast",
        replace_existing=True,
    )

    # US market: forecast at 22:00 KST on weekdays (before US market opens)
    scheduler.add_job(
        pre_market_forecast_us,
        trigger=CronTrigger(hour=22, minute=0, day_of_week="mon-fri", timezone="Asia/Seoul"),
        id="pre_market_forecast_us",
        name="US Pre-Market Forecast",
        replace_existing=True,
    )

    # KR market: evaluate at 16:00 KST on weekdays (after KR market closes)
    scheduler.add_job(
        post_market_evaluate_kr,
        trigger=CronTrigger(hour=16, minute=0, day_of_week="mon-fri", timezone="Asia/Seoul"),
        id="post_market_evaluate_kr",
        name="KR Post-Market Evaluation",
        replace_existing=True,
    )

    # US market: evaluate at 06:00 KST on weekdays (after US market closes)
    scheduler.add_job(
        post_market_evaluate_us,
        trigger=CronTrigger(hour=6, minute=0, day_of_week="mon-fri", timezone="Asia/Seoul"),
        id="post_market_evaluate_us",
        name="US Post-Market Evaluation",
        replace_existing=True,
    )

    return scheduler
