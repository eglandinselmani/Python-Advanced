"""Technical indicators implemented with pandas / NumPy."""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(close: pd.Series, period: int = 20) -> pd.Series:
    """Simple moving average: mean of the last `period` closes."""
    return close.rolling(period).mean()


def ema(close: pd.Series, period: int = 20) -> pd.Series:
    """Exponential moving average with smoothing factor 2/(period+1)."""
    return close.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index with Wilder's smoothing.

    The first average gain/loss is the simple mean of the first `period` changes;
    afterwards avg = (previous_avg * (period - 1) + current) / period.
    """
    values = close.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    if len(values) <= period:
        return pd.Series(out, index=close.index)
    delta = np.diff(values)
    gain, loss = np.clip(delta, 0, None), np.clip(-delta, 0, None)
    avg_g, avg_l = gain[:period].mean(), loss[:period].mean()
    for i in range(period, len(values)):
        if i > period:
            avg_g = (avg_g * (period - 1) + gain[i - 1]) / period
            avg_l = (avg_l * (period - 1) + loss[i - 1]) / period
        out[i] = 100.0 if avg_l == 0 else 100 - 100 / (1 + avg_g / avg_l)
    return pd.Series(out, index=close.index)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD line, signal line and histogram."""
    line = close.ewm(span=fast, adjust=False, min_periods=fast).mean() - \
        close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    sig = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return pd.DataFrame({"macd": line, "signal": sig, "histogram": line - sig})


def bollinger(close: pd.Series, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands: SMA +/- `std` population standard deviations."""
    mid = close.rolling(period).mean()
    dev = close.rolling(period).std(ddof=0)
    return pd.DataFrame({"upper": mid + std * dev, "middle": mid, "lower": mid - std * dev})


def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
    return volume.rolling(period).mean()


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume: running total, + volume on up-closes, - volume on down-closes."""
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def _clean(s: pd.Series) -> list:
    return [None if pd.isna(v) else round(float(v), 6) for v in s]


def compute(df: pd.DataFrame, requested: list[str]) -> dict[str, list]:
    """Compute requested indicators. Tokens: sma:20, ema:50, rsi:14, macd, bb:20, vol, obv."""
    close, volume = df["close"].astype(float), df["volume"].astype(float)
    out: dict[str, list] = {}
    for token in requested:
        name, _, arg = token.strip().lower().partition(":")
        try:
            n = int(arg) if arg else None
        except ValueError:
            raise ValueError(f"Invalid indicator parameter in '{token}'")
        if n is not None and not 1 <= n <= 500:
            raise ValueError(f"Indicator period must be between 1 and 500 ('{token}')")
        if name == "sma":
            out[f"sma_{n or 20}"] = _clean(sma(close, n or 20))
        elif name == "ema":
            out[f"ema_{n or 20}"] = _clean(ema(close, n or 20))
        elif name == "rsi":
            out[f"rsi_{n or 14}"] = _clean(rsi(close, n or 14))
        elif name == "macd":
            m = macd(close)
            for col in m.columns:
                out[f"macd_{col}" if col != "macd" else "macd"] = _clean(m[col])
        elif name in ("bb", "bollinger"):
            b = bollinger(close, n or 20)
            for col in b.columns:
                out[f"bb_{col}"] = _clean(b[col])
        elif name in ("vol", "volume"):
            out["volume_sma"] = _clean(volume_sma(volume, n or 20))
            out["obv"] = _clean(obv(close, volume))
        elif name == "obv":
            out["obv"] = _clean(obv(close, volume))
        else:
            raise ValueError(f"Unknown indicator '{token}'")
    return out
