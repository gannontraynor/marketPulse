from pydantic import BaseModel, Field
from typing import Optional

class VolatilitySignal(BaseModel):
    symbol: str = Field(..., description="The ticker symbol")
    realized_volatility: float = Field(..., description="The realized volatility value")
    lookback: Optional[int] = Field(None, description="The lookback period used for calculation")