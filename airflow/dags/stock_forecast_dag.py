"""
Stock Forecast Platform - Airflow DAG (MWAA)

BashOperator + venv 격리 방식.
- 독립 가상환경에서 패키지 설치 후 실행 (MWAA 패키지 충돌 없음)
- execution_timeout 30분 설정 (33종목 LLM 분석 소요 시간 대응)
- 리포트를 S3에 업로드

스케줄 (KST 기준):
- 한국 시장: 08:00 전망 / 16:00 마감
- 미국 시장: 22:00 전망 / 06:30 마감 (다음날)
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


# ============================================================
# 설정
# ============================================================
S3_SOURCE = "s3://mwaa-bucket-only/stock-forecast-src/"
S3_REPORTS = "s3://stock-forecast-reports-197840067661/reports/"
BEDROCK_MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def _bash_command(script: str, market: str) -> str:
    return f"""
set -e

echo "=== Starting stock forecast task ==="
echo "Script: {script}"
echo "Market: {market}"
echo "Time: $(date)"

# 1. 작업 디렉토리
WORK_DIR=$(mktemp -d /tmp/stock_forecast_XXXXXX)
cd $WORK_DIR
echo "Work dir: $WORK_DIR"

# 2. S3에서 소스코드 다운로드
echo "=== Downloading source from S3 ==="
aws s3 sync {S3_SOURCE} . --quiet --exclude "*.pyc" --exclude "__pycache__/*" --exclude "reports/*"
echo "Source downloaded."

# 3. 가상환경 생성 + 패키지 설치
echo "=== Creating venv and installing packages ==="
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet --no-cache-dir yfinance pandas numpy feedparser beautifulsoup4 httpx ta anthropic sqlalchemy jinja2 pyyaml
echo "Packages installed."

# 4. 디렉토리 생성
mkdir -p data reports/stocks

# 5. 환경변수 설정
export PYTHONPATH=$WORK_DIR
export MARKET_FILTER={market}
export LLM_PROVIDER=bedrock
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID={BEDROCK_MODEL}
export S3_REPORT_BUCKET=stock-forecast-reports-197840067661

# 6. 스크립트 실행
echo "=== Running {script} (market={market}) ==="
python scripts/{script}
echo "=== Script completed ==="

# 7. 리포트 S3 업로드
if [ -d "reports" ] && [ "$(ls -A reports)" ]; then
    echo "=== Uploading reports to S3 ==="
    aws s3 sync reports/ {S3_REPORTS} --quiet
    echo "Reports uploaded."
else
    echo "No reports to upload."
fi

# 8. 정리
deactivate
rm -rf $WORK_DIR
echo "=== Task complete ==="
"""


# ============================================================
# 기본 설정
# ============================================================
default_args = {
    "owner": "stock-forecast",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
    "execution_timeout": timedelta(minutes=30),
}


# ============================================================
# DAG 1: 한국 시장 전망 (08:00 KST = UTC 23:00, 일~목)
# ============================================================
with DAG(
    dag_id="stock_forecast_kr_morning",
    default_args=default_args,
    description="한국 시장 장 시작 전 전망 리포트 생성 (8종목)",
    schedule="0 23 * * 0-4",
    start_date=datetime(2026, 5, 18),
    catchup=False,
    tags=["stock-forecast", "korea", "morning"],
) as dag_kr_morning:

    BashOperator(
        task_id="run_forecast_kr",
        bash_command=_bash_command("run_forecast.py", "korea"),
    )


# ============================================================
# DAG 2: 한국 시장 마감 (16:00 KST = UTC 07:00, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_kr_closing",
    default_args=default_args,
    description="한국 시장 마감 리포트 + 백테스팅 (8종목)",
    schedule="0 7 * * 1-5",
    start_date=datetime(2026, 5, 18),
    catchup=False,
    tags=["stock-forecast", "korea", "closing"],
) as dag_kr_closing:

    closing_kr = BashOperator(
        task_id="run_closing_kr",
        bash_command=_bash_command("run_closing_report.py", "korea"),
    )

    backtest_kr = BashOperator(
        task_id="run_backtest_kr",
        bash_command=_bash_command("run_backtest.py", "korea"),
    )

    closing_kr >> backtest_kr


# ============================================================
# DAG 3: 미국 시장 전망 (22:00 KST = UTC 13:00, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_us_morning",
    default_args=default_args,
    description="미국 시장 장 시작 전 전망 리포트 생성 (25종목)",
    schedule="0 13 * * 1-5",
    start_date=datetime(2026, 5, 18),
    catchup=False,
    tags=["stock-forecast", "us", "morning"],
) as dag_us_morning:

    BashOperator(
        task_id="run_forecast_us",
        bash_command=_bash_command("run_forecast.py", "us"),
    )


# ============================================================
# DAG 4: 미국 시장 마감 (06:30 KST = UTC 21:30, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_us_closing",
    default_args=default_args,
    description="미국 시장 마감 리포트 + 백테스팅 (25종목)",
    schedule="30 21 * * 1-5",
    start_date=datetime(2026, 5, 18),
    catchup=False,
    tags=["stock-forecast", "us", "closing"],
) as dag_us_closing:

    closing_us = BashOperator(
        task_id="run_closing_us",
        bash_command=_bash_command("run_closing_report.py", "us"),
    )

    backtest_us = BashOperator(
        task_id="run_backtest_us",
        bash_command=_bash_command("run_backtest.py", "us"),
    )

    closing_us >> backtest_us
