from fastapi import FastAPI, Query
from typing import Dict, List

from packages.core.signals import signal_volatility
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
