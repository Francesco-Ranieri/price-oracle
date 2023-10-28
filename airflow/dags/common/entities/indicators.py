from datetime import datetime

from pydantic import BaseModel


class Indicators(BaseModel):
    close_time_date: datetime
    coin: str
    sma_5: float
    sma_10: float
    sma_20: float
    sma_50: float
    sma_100: float
    sma_200: float


    def __repr__(self):
        return f"Indicators({self.close_time_date}, {self.coin}, {self.sma_5}, {self.sma_10}, {self.sma_20}, {self.sma_50}, {self.sma_100}, {self.sma_200})"