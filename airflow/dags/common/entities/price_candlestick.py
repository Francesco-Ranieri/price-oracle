from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, PositiveInt


class PriceCandlestick(BaseModel):
    close_time: PositiveInt
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    coin: str
    period: str

    @property
    def close_time_date(self) -> str:
        return datetime.strftime(
            datetime.fromtimestamp(self.close_time), "%Y-%m-%d %H:%M:%S"
        )

    @property
    def period_name(self) -> str:
        return {
            "60": "1 minute",
            "180": "3 minutes",
            "300": "5 minutes",
            "900": "15 minutes",
            "1800": "30 minutes",
            "3600": "1 hour",
            "7200": "2 hours",
            "14400": "4 hours",
            "21600": "6 hours",
            "43200": "12 hours",
            "86400": "1 day",
            "259200": "3 days",
            "604800": "1 week",
            "604800_Monday": "1 week (Monday)",
        }.get(self.period, "Unknown")

    def __repr__(self):
        return f"PriceCandlestick({self.close_time}, {self.open_price}, {self.high_price}, {self.low_price}, {self.close_price}, {self.volume}, {self.quote_volume}, {self.coin})"


class PriceCandleStickDTO(BaseModel):
    result: Dict[str, List[List[float]]]
    allowance: Dict[str, Any]
