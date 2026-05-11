import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    slack_webhook_url: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_recipients: str = ""
    database_url: str = f"sqlite:///{ROOT_DIR}/data/stock_forecast.db"
    analysis_depth: str = "standard"

    class Config:
        env_file = str(ROOT_DIR / ".env")
        env_file_encoding = "utf-8"


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
