from pydantic import BaseModel, Field
from typing import Optional

class VolatilitySignal(BaseModel):
    symbol: str = Field(..., description="The ticker symbol")
    realized_volatility: float = Field(..., description="The realized volatility value")
    volatility_percentile: Optional[float] = Field(None, description="The yearly percentile rank of the volatility")
    lookback: Optional[int] = Field(None, description="The lookback period used for calculation")
    flags: Optional[list[str]] = Field(None, description="Any flags associated with the signal")