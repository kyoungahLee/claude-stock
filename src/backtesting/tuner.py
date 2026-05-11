import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import func, select

from src.analysis.ml_models.ensemble import MLEnsemble
from src.config import CONFIG_DIR, ROOT_DIR, get_app_config
from src.data.yahoo_client import fetch_all_tickers
from src.db.database import async_session
from src.db.models import Prediction

from .scorer import AccuracyScorer

logger = logging.getLogger(__name__)


class WeightTuner:
    def __init__(self) -> None:
        self.config = get_app_config()
        backtesting_cfg = self.config.get("backtesting", {})
        self.min_days = backtesting_cfg.get("min_days_for_tuning", 30)
        self.max_change = backtesting_cfg.get("max_weight_change_per_day", 0.05)
        self.accuracy_threshold = backtesting_cfg.get("accuracy_threshold", 0.55)
        self.scorer = AccuracyScorer()

    async def run_tuning(self) -> dict[str, Any]:
        data_days = await self._count_evaluated_days()
        if data_days < self.min_days:
            return {
                "status": "skipped",
                "reason": f"Insufficient data: {data_days}/{self.min_days} days",
            }

        accuracy = await self.scorer.get_accuracy(days=self.min_days)
        current_accuracy = accuracy["weighted_accuracy"]

        result: dict[str, Any] = {
            "status": "tuned",
            "current_accuracy": current_accuracy,
            "data_days": data_days,
        }

        if current_accuracy < self.accuracy_threshold:
            retrain_result = await self._emergency_retrain()
            result["emergency_retrain"] = retrain_result

        adjustment = self._compute_adjustment(accuracy)
        if adjustment != 0.0:
            new_weights = self._apply_adjustment(adjustment)
            result["weight_adjustment"] = adjustment
            result["new_weights"] = new_weights
        else:
            result["weight_adjustment"] = 0.0
            result["message"] = "No adjustment needed"

        return result

    def _compute_adjustment(self, accuracy: dict[str, Any]) -> float:
        weighted_acc = accuracy.get("weighted_accuracy", 0.5)

        if weighted_acc > 0.6:
            return min(0.02, self.max_change)
        elif weighted_acc < 0.45:
            return max(-0.03, -self.max_change)
        elif weighted_acc < 0.5:
            return max(-0.01, -self.max_change)
        return 0.0

    def _apply_adjustment(self, adjustment: float) -> dict[str, float]:
        analysis = self.config.get("analysis", {})
        current_ml = analysis.get("ml_weight", 0.5)
        current_llm = analysis.get("llm_weight", 0.5)

        new_ml = max(0.2, min(0.8, current_ml + adjustment))
        new_llm = 1.0 - new_ml

        self._save_weights(new_ml, new_llm)

        return {"ml_weight": round(new_ml, 4), "llm_weight": round(new_llm, 4)}

    def _save_weights(self, ml_weight: float, llm_weight: float) -> None:
        settings_path = CONFIG_DIR / "settings.yaml"
        with open(settings_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        config.setdefault("analysis", {})
        config["analysis"]["ml_weight"] = round(ml_weight, 4)
        config["analysis"]["llm_weight"] = round(llm_weight, 4)

        with open(settings_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        logger.info(
            "Updated weights: ml=%.4f, llm=%.4f", ml_weight, llm_weight
        )

    async def _emergency_retrain(self) -> dict[str, Any]:
        logger.warning(
            "Accuracy below threshold (%.2f). Triggering emergency retrain.",
            self.accuracy_threshold,
        )
        try:
            ticker_data = fetch_all_tickers()
            if not ticker_data:
                return {"status": "failed", "reason": "No ticker data available"}

            import pandas as pd
            all_data = pd.concat(ticker_data.values(), ignore_index=False)

            ensemble = MLEnsemble()
            result = ensemble.train_all(all_data, lstm_epochs=30)
            return {"status": "retrained", "results": result}
        except Exception as e:
            logger.error("Emergency retrain failed: %s", e)
            return {"status": "failed", "reason": str(e)}

    async def _count_evaluated_days(self) -> int:
        cutoff = date.today() - timedelta(days=90)
        async with async_session() as session:
            stmt = (
                select(func.count(func.distinct(Prediction.date)))
                .where(
                    Prediction.date >= cutoff,
                    Prediction.actual_direction.isnot(None),
                )
            )
            result = await session.execute(stmt)
            return result.scalar() or 0
