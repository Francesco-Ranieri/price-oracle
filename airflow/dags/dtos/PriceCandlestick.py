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

    def __repr__(self):
        return f"PriceCandlestickDTO({self.close_time}, {self.open_price}, {self.high_price}, {self.low_price}, {self.close_price}, {self.volume}, {self.quote_volume}, {self.coin})"