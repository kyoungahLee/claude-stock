from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from src.config import ROOT_DIR

MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLUMNS = [
    "RSI",
    "MACD",
    "MACD_Histogram",
    "BB_Position",
    "SMA_Ratio",
    "EMA_Ratio",
    "Volume_Ratio",
    "ATR",
    "Return_1d",
    "Return_3d",
    "Return_5d",
]


def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    features = pd.DataFrame(index=df.index)

    features["RSI"] = df["RSI"]
    features["MACD"] = df["MACD"]
    features["MACD_Histogram"] = df["MACD_Histogram"]

    bb_range = df["BB_Upper"] - df["BB_Lower"]
    features["BB_Position"] = np.where(
        bb_range != 0,
        (df["Close"] - df["BB_Lower"]) / bb_range,
        0.5,
    )

    features["SMA_Ratio"] = np.where(
        df["SMA_50"] != 0, df["SMA_20"] / df["SMA_50"], 1.0
    )
    features["EMA_Ratio"] = np.where(
        df["EMA_26"] != 0, df["EMA_12"] / df["EMA_26"], 1.0
    )
    features["Volume_Ratio"] = np.where(
        df["Volume_SMA_20"] != 0, df["Volume"] / df["Volume_SMA_20"], 1.0
    )
    features["ATR"] = df["ATR"]

    features["Return_1d"] = df["Close"].pct_change(1)
    features["Return_3d"] = df["Close"].pct_change(3)
    features["Return_5d"] = df["Close"].pct_change(5)

    return features


class XGBoostDirectionModel:
    def __init__(self) -> None:
        self.model: XGBClassifier | None = None
        self.is_trained: bool = False

    def train(self, df: pd.DataFrame) -> dict[str, Any]:
        from src.analysis.technical import compute_indicators

        df = compute_indicators(df.copy())
        features = _prepare_features(df)

        target = (df["Close"].shift(-1) > df["Close"]).astype(int)

        mask = features.notna().all(axis=1) & target.notna()
        X = features.loc[mask]
        y = target.loc[mask]

        if len(X) < 30:
            return {"status": "error", "message": "Insufficient data for training"}

        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        self.model.fit(X.values, y.values)
        self.is_trained = True

        train_accuracy = float(self.model.score(X.values, y.values))
        return {
            "status": "success",
            "samples": len(X),
            "train_accuracy": round(train_accuracy, 4),
        }

    def predict(self, features: pd.DataFrame | dict[str, float]) -> dict[str, Any]:
        if not self.is_trained or self.model is None:
            return {"direction": "FLAT", "probability": 0.5, "status": "not_trained"}

        if isinstance(features, dict):
            X = pd.DataFrame([features])[FEATURE_COLUMNS].values
        else:
            X = features[FEATURE_COLUMNS].values if len(features.shape) > 1 else features.values.reshape(1, -1)

        proba = self.model.predict_proba(X)[0]
        direction = "UP" if proba[1] >= 0.5 else "DOWN"
        probability = float(max(proba))

        return {
            "direction": direction,
            "probability": round(probability, 4),
            "up_prob": round(float(proba[1]), 4),
            "down_prob": round(float(proba[0]), 4),
        }

    def predict_from_df(self, df: pd.DataFrame) -> dict[str, Any]:
        from src.analysis.technical import compute_indicators

        df = compute_indicators(df.copy())
        features = _prepare_features(df)
        last_row = features.iloc[[-1]].dropna(axis=1, how="any")

        if last_row.empty or len(last_row.columns) < len(FEATURE_COLUMNS):
            return {"direction": "FLAT", "probability": 0.5, "status": "insufficient_features"}

        return self.predict(features.iloc[[-1]])

    def save_model(self, path: Path | None = None) -> Path:
        path = path or MODELS_DIR / "xgboost_direction.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "is_trained": self.is_trained}, path)
        return path

    def load_model(self, path: Path | None = None) -> bool:
        path = path or MODELS_DIR / "xgboost_direction.joblib"
        if not path.exists():
            return False
        data = joblib.load(path)
        self.model = data["model"]
        self.is_trained = data["is_trained"]
        return True
