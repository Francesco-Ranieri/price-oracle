from datetime import datetime

from pydantic import BaseModel


class Prediction(BaseModel):
    close_time_date: datetime
    close_price: float
    coin: str
    model_name: str

    def __repr__(self):
        return f"<Prediction {self.coin} {self.close_time_date} {self.close_price} {self.model_name}>"