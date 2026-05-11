import json
from anthropic import Anthropic

from src.config import get_settings


def analyze_with_llm(
    ticker: str,
    ticker_name: str,
    technical_signals: dict,
    news_text: str,
    recent_prices: list[dict],
) -> dict:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return {"error": "ANTHROPIC_API_KEY not configured"}

    client = Anthropic(api_key=settings.anthropic_api_key)

    system_prompt = """You are a professional stock market analyst. You analyze technical indicators and news to provide stock forecasts.

Your output must be valid JSON with this structure:
{
    "news_summary": "Brief summary of relevant news (2-3 sentences)",
    "sentiment_score": <float from -1.0 (very bearish) to 1.0 (very bullish)>,
    "direction": "UP" | "DOWN" | "FLAT",
    "confidence": <float from 0.0 to 1.0>,
    "magnitude_range": {"low": <float %>, "high": <float %>},
    "key_catalysts": ["catalyst1", "catalyst2"],
    "key_risks": ["risk1", "risk2"],
    "reasoning": "Brief explanation of your analysis"
}

Be objective and data-driven. If information is insufficient, lower your confidence score."""

    price_text = ""
    if recent_prices:
        price_text = "Recent price history (last 5 days):\n"
        for p in recent_prices[-5:]:
            price_text += f"  {p['date']}: Close={p['close']:.2f}, Change={p['change_pct']:+.2f}%\n"

    signals_text = json.dumps(technical_signals, indent=2) if technical_signals else "No technical data available"

    user_prompt = f"""Analyze the following stock and provide your forecast for the next trading day.

**Stock**: {ticker} ({ticker_name})

**Technical Indicators**:
{signals_text}

**{price_text}**

**Today's Relevant News**:
{news_text if news_text else "No news available for this ticker."}

Provide your analysis as JSON."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = response.content[0].text
        # Extract JSON from response
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
