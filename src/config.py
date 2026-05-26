import os
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"


class Settings:
    def __init__(self):
        # Load .env file if exists
        env_file = ROOT_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

        # LLM Provider
        self.llm_provider = os.environ.get("LLM_PROVIDER", "anthropic")

        # Anthropic Direct API
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

        # AWS Bedrock
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        self.aws_profile = os.environ.get("AWS_PROFILE", "")
        self.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        self.aws_session_token = os.environ.get("AWS_SESSION_TOKEN", "")
        self.bedrock_model_id = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")

        # Notifications
        self.slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.email_recipients = os.environ.get("EMAIL_RECIPIENTS", "")

        # Database
        self.database_url = os.environ.get("DATABASE_URL", f"sqlite:///{ROOT_DIR}/data/stock_forecast.db")

        # Analysis
        self.analysis_depth = os.environ.get("ANALYSIS_DEPTH", "standard")

        # S3
        self.s3_report_bucket = os.environ.get("S3_REPORT_BUCKET", "")


def load_yaml(filename: str) -> dict[str, Any]:
    path = CONFIG_DIR / filename
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_settings() -> Settings:
    return Settings()


def get_app_config() -> dict[str, Any]:
    return load_yaml("settings.yaml")


def get_news_sources() -> dict[str, Any]:
    return load_yaml("news_sources.yaml")


def get_stock_watchlist() -> dict[str, Any]:
    return load_yaml("stocks.yaml")
