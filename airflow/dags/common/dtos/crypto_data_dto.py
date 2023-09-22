from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, PositiveInt

class CryptoDataDTO(BaseModel):
    unix: PositiveInt 
    date: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume_crypto: float
    volume_usd: float
    period: str = "3600"
