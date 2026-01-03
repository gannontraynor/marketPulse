import datetime as dt
import math
from typing import Callable, Any, Dict, List, Optional

from sqlalchemy import select
from packages.core.db import SessionLocal
from packages.core.models import DailyBar
from packages.core.regimes import regime_from_vol

TRADING_DAYS_1Y = 252


def _stdev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)

def _returns_from_closes(closes: List[float]) -> List[float]:
    returns = []
    for i in range(1, len(closes)):
        ret = (closes[i] - closes[i - 1]) / closes[i - 1]
        returns.append(ret)
    return returns

def _annualize(daily_vol: float, factor: int = TRADING_DAYS_1Y) -> float:
    return daily_vol * math.sqrt(factor)

def get_recent_closes(symbol: str, lookback: int = 20) -> List[float]:
    """Fetch recent closing prices for a symbol."""
    session = SessionLocal()
    try:
        q = (
            select(DailyBar.close)
            .where(DailyBar.symbol == symbol.upper())
            .order_by(DailyBar.date.desc())
            .limit(lookback)
        )
        closes_desc = [rows[0] for rows in session.execute(q).all()]
        closes = list(reversed(closes_desc))
        return closes
    finally:
        session.close()

def get_recent_dates(symbol: str, days: int) -> List[dt.date]:
    """Most recent N dates (chronological)."""
    session = SessionLocal()
    try:
        q = (
            select(DailyBar.date)
            .where(DailyBar.symbol == symbol.upper())
            .order_by(DailyBar.date.desc())
            .limit(days)
        )
        dates_desc = [row[0] for row in session.execute(q).all()]
        return list(reversed(dates_desc))
    finally:
        session.close()


def realized_volatility_asof(symbol: str, asof: dt.date, lookback: int = 20) -> float:
    """
    Realized vol computed up to and including `asof`.
    Pulls lookback+1 closes ending at `asof`.
    Returns annualized vol (because your signal output is annualized).
    """
    session = SessionLocal()
    try:
        q = (
            select(DailyBar.close)
            .where(DailyBar.symbol == symbol.upper(), DailyBar.date <= asof)
            .order_by(DailyBar.date.desc())
            .limit(lookback + 1)
        )
        closes_desc = [row[0] for row in session.execute(q).all()]
        closes = list(reversed(closes_desc))
        if len(closes) < lookback + 1:
            return 0.0

        rets = _returns_from_closes(closes)
        if not rets:
            return 0.0

        mean_ret = sum(rets) / len(rets)
        stdev_ret = _stdev(rets, mean_ret)
        return _annualize(stdev_ret)
    finally:
        session.close()


def volatility_percentile_1y_asof(symbol: str, asof: dt.date, lookback: int = 20) -> Optional[float]:
    """
    Percentile of current vol among trailing 1Y vols, computed as-of date.
    Returns None if insufficient history.
    """
    session = SessionLocal()
    try:
        q = (
            select(DailyBar.close)
            .where(DailyBar.symbol == symbol.upper(), DailyBar.date <= asof)
            .order_by(DailyBar.date.desc())
            .limit(TRADING_DAYS_1Y + lookback + 1)
        )
        closes_desc = [row[0] for row in session.execute(q).all()]
        closes = list(reversed(closes_desc))

        if len(closes) < (TRADING_DAYS_1Y + lookback + 1):
            return None

        vols = []
        # build rolling vols across the trailing year
        for i in range(len(closes) - (lookback + 1) + 1):
            window = closes[i : i + lookback + 1]
            rets = _returns_from_closes(window)
            mean_ret = sum(rets) / len(rets)
            stdev_ret = _stdev(rets, mean_ret)
            vols.append(_annualize(stdev_ret))

        current_vol = vols[-1]
        rank = percentile_rank(current_vol, vols)
        return float(rank)
    finally:
        session.close()

def realized_volatility(
    symbol: str,
    lookback: int = 20,
) -> float:
    """Calculate the realized volatility for a symbol over a lookback period."""
    closes = get_recent_closes(symbol, lookback + 1)
    if len(closes) < lookback + 1:
        return 0.0

    returns = _returns_from_closes(closes)
    mean_ret = sum(returns) / len(returns)
    stdev_ret = _stdev(returns, mean_ret)

    return stdev_ret

def percentile_rank(value: float, data: List[float]) -> float:
    """Calculate the percentile rank [0,1] of a value within a dataset."""
    if not data:
        return 0.0
    count = sum(1 for x in data if x < value)
    return (count / len(data))

def volatility_percentile_1y(symbol: str, lookback: int = 20) -> float:
    """Calculate the 1-year volatility percentile for a symbol."""
    session = SessionLocal()
    try:
        q = (
            select(DailyBar.close)
            .where(DailyBar.symbol == symbol.upper())
            .order_by(DailyBar.date.desc())
            .limit(TRADING_DAYS_1Y + lookback)
        )
        closes_desc = [rows[0] for rows in session.execute(q).all()]
        closes = list(reversed(closes_desc))
        if len(closes) < TRADING_DAYS_1Y + lookback:
            # Not enough data to calculate volatility
            return 0.0

        volatilities_daily = []
        for i in range(len(closes) - lookback):
            window_closes = closes[i : i + lookback + 1]
            returns = _returns_from_closes(window_closes)
            mean_ret = sum(returns) / len(returns)
            stdev_ret = _stdev(returns, mean_ret)
            annualized_vol = _annualize(stdev_ret)
            volatilities_daily.append(annualized_vol)

        current_vol = volatilities_daily[-1]
        rank = percentile_rank(current_vol, volatilities_daily)
        return rank
    finally:
        session.close()

def volatility_flags(vol: float, vol_p: float) -> List[str]:
    """Generate interpretable volatility regime flags."""
    flags: List[str] = []

    # Relative regime (primary signal)
    if vol_p >= 0.90:
        flags.append("VOL_SPIKE")
    elif vol_p >= 0.80:
        flags.append("VOL_ELEVATED")
    elif vol_p <= 0.10:
        flags.append("VOL_CRUSH")

    # Absolute sanity checks (secondary / cross-asset safety)
    if vol >= 0.50:
        flags.append("ABS_HIGH_VOL")
    elif vol <= 0.10:
        flags.append("ABS_LOW_VOL")

    return flags


def signal_volatility(symbol: str, lookback: int = 20) -> float:
    """Signal function to get realized volatility."""
    vol_daily = realized_volatility(symbol, lookback)
    vol_ann = _annualize(vol_daily)

    vol_percentile_1y = volatility_percentile_1y(symbol, lookback)
    flags = volatility_flags(vol_daily, vol_percentile_1y)
    return {
        "symbol": symbol,
        "lookback": lookback,
        "realized_volatility": float(f"{vol_ann:.6f}"),
        "volatility_percentile": float(f"{vol_percentile_1y:.6f}"),
        "flags": flags,
    }

def regimes_over_time(symbol: str, lookback: int = 20, days: int = 30) -> List[Dict[str, Any]]:
    """
    For each of the last `days` trading days, compute:
      - realized vol (annualized)
      - 1Y vol percentile (if available)
      - regime label
    """
    dates = get_recent_dates(symbol, days=days)

    series: List[Dict[str, Any]] = []
    for d in dates:
        vol = realized_volatility_asof(symbol, d, lookback=lookback)
        p = volatility_percentile_1y_asof(symbol, d, lookback=lookback)

        series.append(
            {
                "date": d.isoformat(),
                "symbol": symbol.upper(),
                "vol_ann": float(f"{vol:.6f}"),
                "vol_percentile_1y": None if p is None else float(f"{p:.6f}"),
                "regime": regime_from_vol(vol, p),
            }
        )
    return series


def transitions_from_series(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Emit transition events when regime changes day-to-day.
    """
    events: List[Dict[str, Any]] = []
    if not series:
        return events

    prev = series[0]["regime"]
    for row in series[1:]:
        cur = row["regime"]
        if cur != prev:
            events.append(
                {
                    "symbol": row["symbol"],
                    "date": row["date"],
                    "from": prev,
                    "to": cur,
                }
            )
        prev = cur
    return events