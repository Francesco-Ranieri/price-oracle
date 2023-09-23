from typing import List
from common.entities.price_candlestick import PriceCandleStick
from common.dtos.crypto_data_dto import CryptoDataDTO

class CryptoDataMapper:
    @staticmethod
    def to_price_candlesticks(ohlc_data: List[CryptoDataDTO]) -> List[PriceCandleStick]:
        return list(map(CryptoDataMapper.to_price_candlestick, ohlc_data))

    @staticmethod
    def to_price_candlestick(candle: CryptoDataDTO) -> List[PriceCandleStick]:
        return PriceCandleStick.parse_obj(
            {
                "close_time": candle.unix/1000, # convert timestamp to seconds
                "open_price": candle.open,
                "high_price": candle.high,
                "low_price": candle.low,
                "close_price": candle.close,
                "volume": candle.volume_crypto,
                "quote_volume": candle.volume_usd,
                "coin": candle.symbol.replace("/", ""),
                "period": candle.period,
                "_close_time_date": candle.date
            }
        )
