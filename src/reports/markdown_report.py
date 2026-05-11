from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config import ROOT_DIR

TEMPLATE_DIR = ROOT_DIR / "src" / "reports" / "templates"
OUTPUT_DIR = ROOT_DIR / "reports"


def generate_daily_report(
    forecasts: list[dict],
    top_news: list,
    accuracy: dict | None = None,
) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("daily_forecast.md.j2")

    today = datetime.now().strftime("%Y-%m-%d")

    if accuracy is None:
        accuracy = {"directional": "N/A", "total": 0, "correct": 0}

    content = template.render(
        date=today,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        forecasts=forecasts,
        top_news=top_news,
        accuracy=accuracy,
        version="0.1.0",
    )

    output_path = OUTPUT_DIR / f"{today}_forecast.md"
    output_path.write_text(content, encoding="utf-8")

    return str(output_path)
