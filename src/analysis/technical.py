import pandas as pd
import ta


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 20:
        return df

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    df["RSI"] = ta.momentum.RSIIndicator(close, window=14).rsi()
    macd = ta.trend.MACD(close)
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Histogram"] = macd.macd_diff()

    bb = ta.volatility.BollingerBands(close, window=20)
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Lower"] = bb.bollinger_lband()
    df["BB_Middle"] = bb.bollinger_mavg()

    df["SMA_20"] = ta.trend.SMAIndicator(close, window=20).sma_indicator()
    df["SMA_50"] = ta.trend.SMAIndicator(close, window=50).sma_indicator()
    df["EMA_12"] = ta.trend.EMAIndicator(close, window=12).ema_indicator()
    df["EMA_26"] = ta.trend.EMAIndicator(close, window=26).ema_indicator()

    df["Volume_SMA_20"] = ta.trend.SMAIndicator(volume.astype(float), window=20).sma_indicator()

    df["ATR"] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()
    df["Stoch_K"] = ta.momentum.StochasticOscillator(high, low, close).stoch()

    return df


def get_latest_signals(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}

    df = compute_indicators(df)
    last = df.iloc[-1]

    signals = {}

    # RSI signal
    rsi = last.get("RSI")
    if pd.notna(rsi):
        if rsi > 70:
            signals["RSI"] = {"value": round(rsi, 2), "signal": "overbought"}
        elif rsi < 30:
            signals["RSI"] = {"value": round(rsi, 2), "signal": "oversold"}
        else:
            signals["RSI"] = {"value": round(rsi, 2), "signal": "neutral"}

    # MACD signal
    macd_hist = last.get("MACD_Histogram")
    if pd.notna(macd_hist):
        signals["MACD"] = {
            "value": round(macd_hist, 4),
            "signal": "bullish" if macd_hist > 0 else "bearish",
        }

    # Bollinger Bands position
    close = last["Close"]
    bb_upper = last.get("BB_Upper")
    bb_lower = last.get("BB_Lower")
    if pd.notna(bb_upper) and pd.notna(bb_lower):
        bb_pct = (close - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        signals["BollingerBands"] = {
            "value": round(bb_pct, 3),
            "signal": "overbought" if bb_pct > 0.8 else "oversold" if bb_pct < 0.2 else "neutral",
        }

    # SMA trend
    sma_20 = last.get("SMA_20")
    sma_50 = last.get("SMA_50")
    if pd.notna(sma_20) and pd.notna(sma_50):
        signals["SMA_Trend"] = {
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "signal": "bullish" if sma_20 > sma_50 else "bearish",
        }

    # Volume
    vol = last.get("Volume")
    vol_sma = last.get("Volume_SMA_20")
    if pd.notna(vol) and pd.notna(vol_sma) and vol_sma > 0:
        vol_ratio = vol / vol_sma
        signals["Volume"] = {
            "ratio": round(vol_ratio, 2),
            "signal": "high" if vol_ratio > 1.5 else "low" if vol_ratio < 0.5 else "normal",
        }

    return signals
