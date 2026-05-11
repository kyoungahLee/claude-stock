import json

import anthropic

from src.config import get_settings


def _get_client():
    settings = get_settings()

    if settings.llm_provider == "bedrock":
        return anthropic.AnthropicBedrock(
            aws_region=settings.aws_region,
            aws_profile=settings.aws_profile if settings.aws_profile else None,
            aws_access_key=settings.aws_access_key_id if settings.aws_access_key_id else None,
            aws_secret_key=settings.aws_secret_access_key if settings.aws_secret_access_key else None,
            aws_session_token=settings.aws_session_token if settings.aws_session_token else None,
        )
    else:
        if not settings.anthropic_api_key:
            return None
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _get_model_id(settings) -> str:
    if settings.llm_provider == "bedrock":
        return settings.bedrock_model_id
    return "claude-sonnet-4-20250514"


def analyze_with_llm(
    ticker: str,
    ticker_name: str,
    technical_signals: dict,
    news_text: str,
    recent_prices: list[dict],
    current_price: float,
) -> dict:
    settings = get_settings()
    client = _get_client()
    if client is None:
        return {"error": "LLM not configured. Set ANTHROPIC_API_KEY or LLM_PROVIDER=bedrock"}

    system_prompt = """You are a professional stock market analyst. You analyze technical indicators and news to provide stock forecasts across multiple timeframes.

Your output must be valid JSON with this structure:
{
    "news_summary": "Brief summary of relevant news (2-3 sentences)",
    "daily": {
        "direction": "UP" | "DOWN" | "FLAT",
        "confidence": <float from 0.0 to 1.0>,
        "price_range": {"low": <float absolute price>, "high": <float absolute price>},
        "reasoning": "Brief explanation for next-day forecast"
    },
    "weekly": {
        "direction": "UP" | "DOWN" | "FLAT",
        "confidence": <float from 0.0 to 1.0>,
        "price_range": {"low": <float absolute price>, "high": <float absolute price>},
        "reasoning": "Brief explanation for 1-week forecast"
    },
    "monthly": {
        "direction": "UP" | "DOWN" | "FLAT",
        "confidence": <float from 0.0 to 1.0>,
        "price_range": {"low": <float absolute price>, "high": <float absolute price>},
        "reasoning": "Brief explanation for 1-month forecast"
    },
    "key_catalysts": ["catalyst1", "catalyst2"],
    "key_risks": ["risk1", "risk2"]
}

Guidelines:
- price_range values must be absolute dollar prices (not percentages).
- Use the provided current price as the baseline for your price range estimates.
- Wider timeframes should generally have wider price ranges to reflect greater uncertainty.
- Be objective and data-driven. If information is insufficient, lower your confidence score.
- Confidence for longer timeframes should generally be lower than shorter ones."""

    price_text = ""
    if recent_prices:
        price_text = "Recent price history (last 5 days):\n"
        for p in recent_prices[-5:]:
            price_text += f"  {p['date']}: Close={p['close']:.2f}, Change={p['change_pct']:+.2f}%\n"

    signals_text = json.dumps(technical_signals, indent=2) if technical_signals else "No technical data available"

    user_prompt = f"""Analyze the following stock and provide forecasts for three timeframes: next trading day (daily), 1 week (weekly), and 1 month (monthly).

**Stock**: {ticker} ({ticker_name})
**Current Price**: ${current_price:.2f}

**Technical Indicators**:
{signals_text}

**{price_text}**

**Today's Relevant News**:
{news_text if news_text else "No news available for this ticker."}

Provide your analysis as JSON."""

    try:
        response = client.messages.create(
            model=_get_model_id(settings),
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = response.content[0].text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())

    except json.JSONDecodeError:
        return {
            "error": "Failed to parse LLM response as JSON",
            "raw_response": content if 'content' in dir() else "",
        }
    except Exception as e:
        return {"error": str(e)}
