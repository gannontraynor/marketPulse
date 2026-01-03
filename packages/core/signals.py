import math
from typing import Callable, Any, Dict, List, Optional

from sqlalchemy import select
from packages.core.db import SessionLocal
from packages.core.models import DailyBar

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

def realized_volatility(
    symbol: str,
    lookback: int = 20,
    annualize: bool = True,
    annualization_factor: int = 252,
) -> float:
    """Calculate the realized volatility for a symbol over a lookback period."""
    closes = get_recent_closes(symbol, lookback + 1)
    if len(closes) < lookback + 1:
        return 0.0

    returns = _returns_from_closes(closes)
    mean_ret = sum(returns) / len(returns)
    stdev_ret = _stdev(returns, mean_ret)

    realized_vol = stdev_ret * math.sqrt(annualization_factor)
    return realized_vol

def signal_volatility(symbol: str, lookback: int = 20) -> float:
    """Signal function to get realized volatility."""
    vol = realized_volatility(symbol, lookback, annualize=True)
    return {
        "symbol": symbol,
        "lookback": lookback,
        "realized_volatility": vol,
    }