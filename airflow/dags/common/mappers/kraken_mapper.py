from typing import List
from common.entities.price_candlestick import PriceCandleStick
from common.dtos.kraken_dto import KrakenDTO

class KrakenMapper:
    @staticmethod
    def to_price_candlestick(
        ohlc_data: KrakenDTO,
        coin: str,
        period: str
    ) -> List[PriceCandleStick]:
        candlesticks = []
        for row in ohlc_data:
            candlestick = PriceCandleStick.parse_obj(
                {
                    "close_time": row[0],
                    "open_price": row[1],
                    "high_price": row[2],
                    "low_price": row[3],
                    "close_price": row[4],
                    "volume": row[5],
                    "quote_volume": row[6],
                    "coin": coin,
                    "period": period,
                }
            )
            candlesticks.append(candlestick)
        return candlesticks