from datetime import datetime
from pydantic import BaseModel, PositiveInt
from pydantic.functional_validators import field_validator
from dateutil.parser import parse
from pandas._libs.tslibs.timestamps import Timestamp

class BinanceDataDTO(BaseModel):
    Unix: PositiveInt 
    Date: datetime
    Symbol: str
    Open: float
    High: float
    Low: float
    Close: float
    volume_crypto: float
    volume_usd: float
    tradecount: PositiveInt # will be ignored for know
    period: str = "86400"

    @field_validator('Date', mode='before')
    @classmethod
    def str_to_datetime(cls, v: Timestamp) -> datetime:
        return parse(str(v))