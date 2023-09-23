from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, PositiveInt
class PriceCandleStick(BaseModel, extra="allow"):
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
        if not hasattr(self, "_close_time_date"):
            self._close_time_date = datetime.strftime(
                datetime.fromtimestamp(self.close_time), "%Y-%m-%d %H:%M:%S"
            )
        return self._close_time_date

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
        return f"PriceCandleStick({self.close_time}, {self.open_price}, {self.high_price}, {self.low_price}, {self.close_price}, {self.volume}, {self.quote_volume}, {self.coin})"
