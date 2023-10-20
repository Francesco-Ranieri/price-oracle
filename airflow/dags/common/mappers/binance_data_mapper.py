from typing import List
from common.entities.price_candlestick import PriceCandleStick
from common.dtos.binance_data_dto import BinanceDataDTO

class BinanceDataMapper:
    @staticmethod
    def to_price_candlesticks(ohlc_data: List[BinanceDataDTO]) -> List[PriceCandleStick]:
        return list(map(BinanceDataMapper.to_price_candlestick, ohlc_data))

    @staticmethod
    def to_price_candlestick(candle: BinanceDataDTO) -> PriceCandleStick:
        return PriceCandleStick.model_validate(
            {
                "close_time": candle.Unix/1000,
                "close_time_date": candle.Date,
                "open_price": candle.Open,
                "high_price": candle.High,
                "low_price": candle.Low,
                "close_price": candle.Close,
                "volume": candle.volume_crypto,
                "quote_volume": candle.volume_usd,
                "coin": candle.Symbol,
                "period": candle.period
            }
        )
