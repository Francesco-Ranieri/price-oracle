from typing import List
from common.entities.price_candlestick import PriceCandleStick
from common.dtos.crypto_watch_dto import CryptoWatchDTO

class CryptoWatchMapper:
    @staticmethod
    def to_price_candlestick(cls, ohlc_data: CryptoWatchDTO, coin: str) -> List[PriceCandleStick]:
        candlesticks = []
        for period, candles in ohlc_data.result.items():
            for row in candles:
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