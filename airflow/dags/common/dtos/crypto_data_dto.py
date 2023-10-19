from datetime import datetime
from pydantic import BaseModel, PositiveInt
from pydantic.functional_validators import field_validator
from dateutil.parser import parse
from pandas._libs.tslibs.timestamps import Timestamp
import math

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

    @field_validator('date', mode='before')
    @classmethod
    def str_to_datetime(cls, v: Timestamp) -> datetime:
        return parse(str(v))