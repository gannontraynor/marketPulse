from fastapi import FastAPI
from typing import Dict, List

from packages.core.signals import signal_volatility, regimes_over_time, transitions_from_series
from packages.core.schemas import VolatilitySignal
app = FastAPI(title = "Market Pulse API")

DEFAULT_SYMBOLS = ["AAPL.US", "MSFT.US", "GOOGL.US", "AMZN.US", "NVDA.US"]

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

@app.get("/signals/volatility/{symbol}", response_model=VolatilitySignal)
def get_volatility(symbol: str, lookback: int = 20) -> VolatilitySignal:
    return VolatilitySignal(**signal_volatility(symbol, lookback))

@app.get("/signals/today", response_model=List[VolatilitySignal])
def get_volatility_for_default_symbols(lookback: int = 20) -> List[VolatilitySignal]:
    return [VolatilitySignal(**signal_volatility(symbol, lookback)) for symbol in DEFAULT_SYMBOLS]

@app.get("/signals/transitions")
def get_transitions(days: int = 30, lookback: int = 20):
    out = []
    for s in DEFAULT_SYMBOLS:
        series = regimes_over_time(s, lookback=lookback, days=days)
        out.extend(transitions_from_series(series))

    return {"count": len(out), "transitions": out}

@app.get("/signals/transitions/{symbol}")
def get_symbol_transitions(symbol: str, days: int = 30, lookback: int = 20):
    series = regimes_over_time(symbol, lookback=lookback, days=days)
    return {
        "symbol": symbol.upper(),
        "days": days,
        "lookback": lookback,
        "transitions": transitions_from_series(series),
        "series": series,
    }