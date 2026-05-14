"""
Stock Forecast Platform - Airflow DAG

스케줄:
- 한국 시장: 08:00 KST 전망 / 16:00 KST 마감
- 미국 시장: 22:00 KST 전망 / 06:30 KST 마감 (다음날)

실행 방식: ECS Fargate Task
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago


# ============================================================
# 설정 - MWAA 환경 정보
# ============================================================
ECS_CLUSTER = "stock-forecast-cluster"  # ECS 클러스터명 (생성 필요)
TASK_DEFINITION = "stock-forecast-task"  # ECS Task Definition명 (생성 필요)
SUBNETS = ["subnet-09fd7a476c383a8cd", "subnet-0c591e884b7fd1411"]
SECURITY_GROUPS = ["sg-09b8deb50bba429d2"]
AWS_REGION = "eu-west-1"
S3_REPORT_BUCKET = "mwaa-bucket-only"  # 또는 별도 리포트 버킷 생성 가능

# 공통 환경변수 (ECS Task에 전달)
COMMON_ENV = [
    {"name": "LLM_PROVIDER", "value": "bedrock"},
    {"name": "AWS_REGION", "value": "us-east-1"},  # Bedrock은 us-east-1 사용
    {"name": "BEDROCK_MODEL_ID", "value": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"},
    {"name": "S3_REPORT_BUCKET", "value": S3_REPORT_BUCKET},
    {"name": "DATABASE_URL", "value": "postgresql://user:pass@host:5432/stock_forecast"},  # RDS
]


# ============================================================
# 기본 DAG 설정
# ============================================================
default_args = {
    "owner": "stock-forecast",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _ecs_task(command: list[str], env_overrides: list[dict] = None):
    """ECS Fargate Task 실행을 위한 overrides 생성"""
    env = COMMON_ENV.copy()
    if env_overrides:
        env.extend(env_overrides)

    return {
        "containerOverrides": [
            {
                "name": "stock-forecast",
                "command": command,
                "environment": env,
            }
        ],
    }


# ============================================================
# DAG 1: 한국 시장 전망 (매일 08:00 KST, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_kr_morning",
    default_args=default_args,
    description="한국 시장 장 시작 전 전망 리포트 생성",
    schedule_interval="0 23 * * 0-4",  # UTC 23:00 = KST 08:00 (월~금)
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "korea", "morning"],
) as dag_kr_morning:

    forecast_kr = EcsRunTaskOperator(
        task_id="run_forecast_kr",
        cluster=ECS_CLUSTER,
        task_definition=TASK_DEFINITION,
        launch_type="FARGATE",
        overrides=_ecs_task(
            command=["python", "scripts/run_forecast.py"],
            env_overrides=[{"name": "MARKET_FILTER", "value": "korea"}],
        ),
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS,
                "securityGroups": SECURITY_GROUPS,
                "assignPublicIp": "ENABLED",
            }
        },
        region=AWS_REGION,
        awslogs_group="/ecs/stock-forecast",
        awslogs_stream_prefix="forecast-kr",
    )


# ============================================================
# DAG 2: 한국 시장 마감 (매일 16:00 KST, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_kr_closing",
    default_args=default_args,
    description="한국 시장 장 마감 후 마감 리포트 + 백테스팅",
    schedule_interval="0 7 * * 1-5",  # UTC 07:00 = KST 16:00 (월~금)
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "korea", "closing"],
) as dag_kr_closing:

    closing_kr = EcsRunTaskOperator(
        task_id="run_closing_kr",
        cluster=ECS_CLUSTER,
        task_definition=TASK_DEFINITION,
        launch_type="FARGATE",
        overrides=_ecs_task(
            command=["python", "scripts/run_closing_report.py"],
            env_overrides=[{"name": "MARKET_FILTER", "value": "korea"}],
        ),
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS,
                "securityGroups": SECURITY_GROUPS,
                "assignPublicIp": "ENABLED",
            }
        },
        region=AWS_REGION,
        awslogs_group="/ecs/stock-forecast",
        awslogs_stream_prefix="closing-kr",
    )

    backtest_kr = EcsRunTaskOperator(
        task_id="run_backtest_kr",
        cluster=ECS_CLUSTER,
        task_definition=TASK_DEFINITION,
        launch_type="FARGATE",
        overrides=_ecs_task(
            command=["python", "scripts/run_backtest.py"],
            env_overrides=[{"name": "MARKET_FILTER", "value": "korea"}],
        ),
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS,
                "securityGroups": SECURITY_GROUPS,
                "assignPublicIp": "ENABLED",
            }
        },
        region=AWS_REGION,
        awslogs_group="/ecs/stock-forecast",
        awslogs_stream_prefix="backtest-kr",
    )

    closing_kr >> backtest_kr


# ============================================================
# DAG 3: 미국 시장 전망 (매일 22:00 KST, 월~금)
# ============================================================
with DAG(
    dag_id="stock_forecast_us_morning",
    default_args=default_args,
    description="미국 시장 장 시작 전 전망 리포트 생성",
    schedule_interval="0 13 * * 1-5",  # UTC 13:00 = KST 22:00 (월~금)
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "us", "morning"],
) as dag_us_morning:

    forecast_us = EcsRunTaskOperator(
        task_id="run_forecast_us",
        cluster=ECS_CLUSTER,
        task_definition=TASK_DEFINITION,
        launch_type="FARGATE",
        overrides=_ecs_task(
            command=["python", "scripts/run_forecast.py"],
            env_overrides=[{"name": "MARKET_FILTER", "value": "us"}],
        ),
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS,
                "securityGroups": SECURITY_GROUPS,
                "assignPublicIp": "ENABLED",
            }
        },
        region=AWS_REGION,
        awslogs_group="/ecs/stock-forecast",
        awslogs_stream_prefix="forecast-us",
    )


# ============================================================
# DAG 4: 미국 시장 마감 (매일 06:30 KST, 화~토)
# ============================================================
with DAG(
    dag_id="stock_forecast_us_closing",
    default_args=default_args,
    description="미국 시장 장 마감 후 마감 리포트 + 백테스팅",
    schedule_interval="30 21 * * 1-5",  # UTC 21:30 = KST 06:30 (화~토)
    start_date=days_ago(1),
    catchup=False,
    tags=["stock-forecast", "us", "closing"],
) as dag_us_closing:

    closing_us = EcsRunTaskOperator(
        task_id="run_closing_us",
        cluster=ECS_CLUSTER,
        task_definition=TASK_DEFINITION,
        launch_type="FARGATE",
        overrides=_ecs_task(
            command=["python", "scripts/run_closing_report.py"],
            env_overrides=[{"name": "MARKET_FILTER", "value": "us"}],
        ),
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS,
                "securityGroups": SECURITY_GROUPS,
                "assignPublicIp": "ENABLED",
            }
        },
        region=AWS_REGION,
        awslogs_group="/ecs/stock-forecast",
        awslogs_stream_prefix="closing-us",
    )

    backtest_us = EcsRunTaskOperator(
        task_id="run_backtest_us",
        cluster=ECS_CLUSTER,
        task_definition=TASK_DEFINITION,
        launch_type="FARGATE",
        overrides=_ecs_task(
            command=["python", "scripts/run_backtest.py"],
            env_overrides=[{"name": "MARKET_FILTER", "value": "us"}],
        ),
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": SUBNETS,
                "securityGroups": SECURITY_GROUPS,
                "assignPublicIp": "ENABLED",
            }
        },
        region=AWS_REGION,
        awslogs_group="/ecs/stock-forecast",
        awslogs_stream_prefix="backtest-us",
    )

    closing_us >> backtest_us
