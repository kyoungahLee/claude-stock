from src.config import get_app_config


def combine_signals(technical_signals: dict, llm_result: dict) -> dict:
    config = get_app_config()
    ml_weight = config.get("analysis", {}).get("ml_weight", 0.5)
    llm_weight = config.get("analysis", {}).get("llm_weight", 0.5)

    # Technical score: derive from signals
    tech_score = _compute_technical_score(technical_signals)

    # LLM score: derive from daily forecast (primary timeframe for combined signal)
    daily = llm_result.get("daily", {})
    llm_direction = daily.get("direction", "FLAT")
    llm_confidence = daily.get("confidence", 0.5)
    # Convert direction to a sentiment score for weighted combination
    direction_scores = {"UP": 0.5, "DOWN": -0.5, "FLAT": 0.0}
    llm_score = direction_scores.get(llm_direction, 0.0) * llm_confidence

    # Weighted combination
    final_score = (ml_weight * tech_score) + (llm_weight * llm_score)

    # Determine direction
    if final_score > 0.15:
        direction = "UP"
    elif final_score < -0.15:
        direction = "DOWN"
    else:
        direction = "FLAT"

    # Confidence is weighted average of tech clarity and LLM confidence
    tech_confidence = min(abs(tech_score) * 2, 1.0)
    final_confidence = (ml_weight * tech_confidence) + (llm_weight * llm_confidence)

    return {
        "final_score": round(final_score, 4),
        "direction": direction,
        "confidence": round(final_confidence, 3),
        "technical_score": round(tech_score, 4),
        "llm_score": round(llm_score, 4),
        "weights": {"ml": ml_weight, "llm": llm_weight},
        "llm_analysis": {
            "news_summary": llm_result.get("news_summary", ""),
            "daily": llm_result.get("daily", {}),
            "weekly": llm_result.get("weekly", {}),
            "monthly": llm_result.get("monthly", {}),
            "key_catalysts": llm_result.get("key_catalysts", []),
            "key_risks": llm_result.get("key_risks", []),
        },
    }


def _compute_technical_score(signals: dict) -> float:
    if not signals:
        return 0.0

    scores = []

    rsi = signals.get("RSI", {})
    if rsi:
        if rsi.get("signal") == "oversold":
            scores.append(0.5)
        elif rsi.get("signal") == "overbought":
            scores.append(-0.5)
        else:
            val = rsi.get("value", 50)
            scores.append((50 - val) / 100)

    macd = signals.get("MACD", {})
    if macd:
        scores.append(0.4 if macd.get("signal") == "bullish" else -0.4)

    bb = signals.get("BollingerBands", {})
    if bb:
        val = bb.get("value", 0.5)
        scores.append((0.5 - val) * 0.8)

    sma = signals.get("SMA_Trend", {})
    if sma:
        scores.append(0.3 if sma.get("signal") == "bullish" else -0.3)

    if not scores:
        return 0.0

    return sum(scores) / len(scores)
