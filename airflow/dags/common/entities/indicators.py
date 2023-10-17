from datetime import datetime

from pydantic import BaseModel


class Indicators(BaseModel):
    close_time_date: datetime
    coin: str
    ema_12: float
    ema_26: float
    ema_50: float
    ema_100: float
    ema_200: float
    sma_5: float
    sma_10: float
    sma_20: float
    sma_50: float
    sma_100: float
    sma_200: float


    def __repr__(self):
        return f"Indicators({self.close_time_date}, {self.coin}, {self.ema_12}, {self.ema_26}, {self.ema_50}, {self.ema_100}, {self.ema_200}, {self.sma_5}, {self.sma_10}, {self.sma_20}, {self.sma_50}, {self.sma_100}, {self.sma_200})"