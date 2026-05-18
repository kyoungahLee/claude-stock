"""
Stock Forecast Platform - Airflow DAG (MWAA 직접 실행)

Docker/ECS 없이 MWAA 워커에서 직접 Python 실행.
소스코드는 S3에서 다운로드하여 실행.

스케줄:
- 한국 시장: 08:00 KST 전망 / 16:00 KST 마감
- 미국 시장: 22:00 KST 전망 / 06:30 KST 마감 (다음날)
"""

import os
import sys
import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

import boto3


# ============================================================
# 설정
# ============================================================
AWS_REGION = "eu-west-1"
S3_SOURCE_BUCKET = "mwaa-bucket-only"
S3_SOURCE_PREFIX = "stock-forecast-src/"
S3_REPORT_BUCKET = "stock-forecast-reports-197840067661"

BEDROCK_REGION = "us-east-1"
BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


# ============================================================
# 헬퍼 함수
# ============================================================
def _download_source():
    """S3에서 소스코드를 다운로드하여 임시 디렉토리에 저장"""
    work_dir = Path(tempfile.mkdtemp(prefix="stock_forecast_"))
    s3 = boto3.client("s3", region_name=AWS_REGION)

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_SOURCE_BUCKET, Prefix=S3_SOURCE_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel_path = key[len(S3_SOURCE_PREFIX):]
            if not rel_path:
                continue
            local_path = work_dir / rel_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(S3_SOURCE_BUCKET, key, str(local_path))

    return str(work_dir)


def _upload_reports(work_dir: str):
    """생성된 리포트를 S3에 업로드"""
    s3 = boto3.client("s3", region_name=AWS_REGION)
    reports_dir = Path(work_dir) / "reports"

    if not reports_dir.exists():
        return

    for report_file in reports_dir.rglob("*.md"):
        rel_path = report_file.relative_to(reports_dir)
        s3_key = f"reports/{rel_path}"
        s3.upload_file(str(report_file), S3_REPORT_BUCKET, s3_key)
        print(f"Uploaded: s3://{S3_REPORT_BUCKET}/{s3_key}")


def _run_script(script_name: str, market: str = "all"):
    """소스코드를 다운로드하고 스크립트 실행 후 리포트 업로드"""
    work_dir = _download_source()

    env = os.environ.copy()
    env.update({
        "PYTHONPATH": work_dir,
        "MARKET_FILTER": market,
        "LLM_PROVIDER": "bedrock",
        "AWS_REGION": BEDROCK_REGION,
        "BEDROCK_MODEL_ID": BEDROCK_MODEL_ID,
        "S3_REPORT_BUCKET": S3_REPORT_BUCKET,
    })

    script_path = Path(work_dir) / "scripts" / script_name
    print(f"Running: {script_path} (market={market})")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=work_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )

    print(result.stdout)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")

    _upload_reports(work_dir)
    return result.returncode


# ============================================================
# Task 함수
# ============================================================
def run_forecast_kr(**kwargs):
    _run_script("run_forecast.py", market="korea")


def run_forecast_us(**kwargs):
    _run_script("run_forecast.py", market="us")


def run_closing_kr(**kwargs):
    _run_script("run_closing_report.py", market="korea")


def run_closing_us(**kwargs):
    _run_script("run_closing_report.py", market="us")


def run_backtest_kr(**kwargs):
    _run_script("run_backtest.py", market="korea")


def run_backtest_us(**kwargs):
    _run_script("run_backtest.py", market="us")


# ============================================================
# 기본 DAG 설정
# ============================================================
default_args = {
    "owner": "stock-forecast",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


# ============================================================
# DAG 1: 한국 시장 전망 (매일 08:00 KST = UTC 23:00, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_kr_morning",
    default_args=default_args,
    description="한국 시장 장 시작 전 전망 리포트 생성",
    schedule_interval="0 23 * * 0-4",
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "korea", "morning"],
) as dag_kr_morning:

    PythonOperator(
        task_id="run_forecast_kr",
        python_callable=run_forecast_kr,
    )


# ============================================================
# DAG 2: 한국 시장 마감 (매일 16:00 KST = UTC 07:00, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_kr_closing",
    default_args=default_args,
    description="한국 시장 마감 리포트 + 백테스팅",
    schedule_interval="0 7 * * 1-5",
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "korea", "closing"],
) as dag_kr_closing:

    closing = PythonOperator(
        task_id="run_closing_kr",
        python_callable=run_closing_kr,
    )

    backtest = PythonOperator(
        task_id="run_backtest_kr",
        python_callable=run_backtest_kr,
    )

    closing >> backtest


# ============================================================
# DAG 3: 미국 시장 전망 (매일 22:00 KST = UTC 13:00, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_us_morning",
    default_args=default_args,
    description="미국 시장 장 시작 전 전망 리포트 생성",
    schedule_interval="0 13 * * 1-5",
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "us", "morning"],
) as dag_us_morning:

    PythonOperator(
        task_id="run_forecast_us",
        python_callable=run_forecast_us,
    )


# ============================================================
# DAG 4: 미국 시장 마감 (매일 06:30 KST = UTC 21:30, 화~토)
# ============================================================
with DAG(
    dag_id="stock_forecast_us_closing",
    default_args=default_args,
    description="미국 시장 마감 리포트 + 백테스팅",
    schedule_interval="30 21 * * 1-5",
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "us", "closing"],
) as dag_us_closing:

    closing = PythonOperator(
        task_id="run_closing_us",
        python_callable=run_closing_us,
    )

    backtest = PythonOperator(
        task_id="run_backtest_us",
        python_callable=run_backtest_us,
    )

    closing >> backtest
