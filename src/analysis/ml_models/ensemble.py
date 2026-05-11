from typing import Any

import pandas as pd

from src.analysis.ml_models.lstm_model import LSTMPredictor
from src.analysis.ml_models.xgboost_model import XGBoostDirectionModel


class MLEnsemble:
    def __init__(self, xgb_weight: float = 0.6, lstm_weight: float = 0.4) -> None:
        self.xgb_model = XGBoostDirectionModel()
        self.lstm_model = LSTMPredictor()
        self.xgb_weight = xgb_weight
        self.lstm_weight = lstm_weight
        self._load_models()

    def _load_models(self) -> None:
        self.xgb_available = self.xgb_model.load_model()
        self.lstm_available = self.lstm_model.load_model()

    def predict(self, df: pd.DataFrame) -> dict[str, Any]:
        xgb_result: dict[str, Any] | None = None
        lstm_result: dict[str, Any] | None = None

        if self.xgb_available:
            xgb_result = self.xgb_model.predict_from_df(df)
            if xgb_result.get("status") in ("not_trained", "insufficient_features"):
                xgb_result = None

        if self.lstm_available:
            lstm_result = self.lstm_model.predict(df)
            if lstm_result.get("status") in ("not_trained", "insufficient_data"):
                lstm_result = None

        if xgb_result is None and lstm_result is None:
            return {
                "direction": "FLAT",
                "confidence": 0.0,
                "ml_score": 0.0,
                "status": "no_models_available",
            }

        if xgb_result is not None and lstm_result is None:
            return self._single_model_result(xgb_result, "xgboost")

        if lstm_result is not None and xgb_result is None:
            return self._single_model_result(lstm_result, "lstm")

        return self._combine(xgb_result, lstm_result)

    def _single_model_result(self, result: dict[str, Any], source: str) -> dict[str, Any]:
        direction = result["direction"]
        if source == "xgboost":
            confidence = result.get("probability", 0.5)
            ml_score = (result.get("up_prob", 0.5) - 0.5) * 2
        else:
            predicted_return = result.get("predicted_return", 0.0)
            confidence = min(abs(predicted_return) * 50, 1.0)
            ml_score = max(min(predicted_return * 10, 1.0), -1.0)

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "ml_score": round(ml_score, 4),
            "source": source,
        }

    def _combine(
        self, xgb_result: dict[str, Any], lstm_result: dict[str, Any]
    ) -> dict[str, Any]:
        xgb_score = (xgb_result.get("up_prob", 0.5) - 0.5) * 2
        lstm_return = lstm_result.get("predicted_return", 0.0)
        lstm_score = max(min(lstm_return * 10, 1.0), -1.0)

        total_weight = self.xgb_weight + self.lstm_weight
        combined_score = (
            self.xgb_weight * xgb_score + self.lstm_weight * lstm_score
        ) / total_weight

        if combined_score > 0.1:
            direction = "UP"
        elif combined_score < -0.1:
            direction = "DOWN"
        else:
            direction = "FLAT"

        xgb_conf = xgb_result.get("probability", 0.5)
        lstm_conf = min(abs(lstm_return) * 50, 1.0)
        confidence = (self.xgb_weight * xgb_conf + self.lstm_weight * lstm_conf) / total_weight

        return {
            "direction": direction,
            "confidence": round(confidence, 4),
            "ml_score": round(combined_score, 4),
            "xgb_prediction": xgb_result,
            "lstm_prediction": lstm_result,
            "weights": {"xgb": self.xgb_weight, "lstm": self.lstm_weight},
        }

    def train_all(self, df: pd.DataFrame, lstm_epochs: int = 50) -> dict[str, Any]:
        xgb_result = self.xgb_model.train(df)
        if xgb_result["status"] == "success":
            self.xgb_model.save_model()
            self.xgb_available = True

        lstm_result = self.lstm_model.train(df, epochs=lstm_epochs)
        if lstm_result["status"] == "success":
            self.lstm_model.save_model()
            self.lstm_available = True

        return {
            "xgboost": xgb_result,
            "lstm": lstm_result,
        }
