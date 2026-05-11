from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.config import ROOT_DIR

MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

SEQUENCE_LENGTH = 20
FEATURE_COLS = [
    "Open", "High", "Low", "Close", "Volume",
    "RSI", "MACD", "MACD_Histogram", "SMA_20", "SMA_50",
    "EMA_12", "EMA_26", "ATR",
]


class LSTMNet(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2,
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        return self.fc(last_hidden)


class LSTMPredictor:
    def __init__(self) -> None:
        self.model: LSTMNet | None = None
        self.is_trained: bool = False
        self.feature_means: np.ndarray | None = None
        self.feature_stds: np.ndarray | None = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        if self.feature_means is None or self.feature_stds is None:
            raise ValueError("Normalization parameters not set. Train first.")
        stds = np.where(self.feature_stds == 0, 1.0, self.feature_stds)
        return (data - self.feature_means) / stds

    def _prepare_sequences(
        self, df: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray]:
        from src.analysis.technical import compute_indicators

        df = compute_indicators(df.copy())
        available_cols = [c for c in FEATURE_COLS if c in df.columns]
        data = df[available_cols].dropna().values

        returns = np.diff(df["Close"].dropna().values) / df["Close"].dropna().values[:-1]

        if len(data) < SEQUENCE_LENGTH + 1:
            return np.array([]), np.array([])

        offset = len(data) - len(returns)
        sequences = []
        targets = []

        for i in range(len(data) - SEQUENCE_LENGTH - 1):
            seq = data[i : i + SEQUENCE_LENGTH]
            target_idx = i + SEQUENCE_LENGTH - offset
            if 0 <= target_idx < len(returns):
                sequences.append(seq)
                targets.append(returns[target_idx])

        return np.array(sequences), np.array(targets)

    def train(self, df: pd.DataFrame, epochs: int = 50) -> dict[str, Any]:
        sequences, targets = self._prepare_sequences(df)

        if len(sequences) < 30:
            return {"status": "error", "message": "Insufficient data for training"}

        self.feature_means = sequences.reshape(-1, sequences.shape[-1]).mean(axis=0)
        self.feature_stds = sequences.reshape(-1, sequences.shape[-1]).std(axis=0)

        sequences_norm = np.array([self._normalize(seq) for seq in sequences])

        X = torch.FloatTensor(sequences_norm).to(self.device)
        y = torch.FloatTensor(targets).unsqueeze(1).to(self.device)

        dataset = TensorDataset(X, y)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

        input_size = sequences.shape[-1]
        self.model = LSTMNet(input_size=input_size).to(self.device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        self.model.train()
        losses = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                output = self.model(batch_X)
                loss = criterion(output, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            losses.append(epoch_loss / len(dataloader))

        self.is_trained = True
        return {
            "status": "success",
            "samples": len(sequences),
            "final_loss": round(losses[-1], 6),
            "epochs": epochs,
        }

    def predict(self, sequence: pd.DataFrame | np.ndarray) -> dict[str, Any]:
        if not self.is_trained or self.model is None:
            return {"predicted_return": 0.0, "direction": "FLAT", "status": "not_trained"}

        if isinstance(sequence, pd.DataFrame):
            from src.analysis.technical import compute_indicators

            sequence = compute_indicators(sequence.copy())
            available_cols = [c for c in FEATURE_COLS if c in sequence.columns]
            data = sequence[available_cols].dropna().values[-SEQUENCE_LENGTH:]
        else:
            data = sequence[-SEQUENCE_LENGTH:]

        if len(data) < SEQUENCE_LENGTH:
            return {"predicted_return": 0.0, "direction": "FLAT", "status": "insufficient_data"}

        data_norm = self._normalize(data)
        X = torch.FloatTensor(data_norm).unsqueeze(0).to(self.device)

        self.model.eval()
        with torch.no_grad():
            predicted_return = self.model(X).item()

        if predicted_return > 0.002:
            direction = "UP"
        elif predicted_return < -0.002:
            direction = "DOWN"
        else:
            direction = "FLAT"

        return {
            "predicted_return": round(predicted_return, 6),
            "direction": direction,
        }

    def save_model(self, path: Path | None = None) -> Path:
        path = path or MODELS_DIR / "lstm_predictor.pt"
        path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "model_state": self.model.state_dict() if self.model else None,
            "is_trained": self.is_trained,
            "feature_means": self.feature_means,
            "feature_stds": self.feature_stds,
            "input_size": self.model.lstm.input_size if self.model else None,
        }
        torch.save(state, path)
        return path

    def load_model(self, path: Path | None = None) -> bool:
        path = path or MODELS_DIR / "lstm_predictor.pt"
        if not path.exists():
            return False
        state = torch.load(path, map_location=self.device, weights_only=False)
        if state.get("model_state") is None:
            return False
        self.model = LSTMNet(input_size=state["input_size"]).to(self.device)
        self.model.load_state_dict(state["model_state"])
        self.is_trained = state["is_trained"]
        self.feature_means = state["feature_means"]
        self.feature_stds = state["feature_stds"]
        return True
