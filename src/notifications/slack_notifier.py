import httpx

from src.config import get_settings


def send_slack_notification(forecasts: list[dict], report_path: str = "") -> bool:
    settings = get_settings()
    if not settings.slack_webhook_url:
        return False

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Daily Stock Forecast Report"}
        },
        {"type": "divider"},
    ]

    for f in forecasts[:10]:
        emoji = {"UP": ":chart_with_upwards_trend:", "DOWN": ":chart_with_downwards_trend:", "FLAT": ":left_right_arrow:"}
        direction_emoji = emoji.get(f["direction"], ":question:")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{direction_emoji} *{f['symbol']}* ({f['name']})\n"
                        f"Last: {f['last_close']} ({f['change_pct']:+.2f}%) | "
                        f"Forecast: *{f['direction']}* (conf: {f['confidence']:.0%})",
            },
        })

    payload = {"blocks": blocks}

    try:
        resp = httpx.post(settings.slack_webhook_url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
