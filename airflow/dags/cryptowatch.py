import logging
from typing import List

import requests

from dtos.PriceCandlestick import PriceCandlestick


# Define a custom exception for HTTP errors
class HTTPError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"HTTP request failed with status code {status_code}")

class CryptoWatchClient:
    def __init__(self, exchange="binance"):
        self.PRICES_BASE_URL = "https://api.cryptowat.ch"
        self.PRICES_OHLC_PATH = "/markets/:exchange/:pair/ohlc"
        self.PRICES_PERIODS = 3600
        self.exchange = exchange

    def fetch_ohlc_data(self, coin_pair="BTCUSDT", after=None, before=None) -> PriceCandlestick:
        url = self.PRICES_BASE_URL + self.PRICES_OHLC_PATH.replace(
            ":exchange", self.exchange
        ).replace(":pair", coin_pair)

        params = {"periods": self.PRICES_PERIODS, "after": after, "before": before}

        logging.info(f"Sending request to {url}")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            ohlc_data = response.json()["result"][str(self.PRICES_PERIODS)]
            return self.map_to_dto(ohlc_data, coin_pair)
        else:
            logging.error(
                f"HTTP request failed with status code {response.status_code}"
            )
            logging.error(response.json())
            raise HTTPError(response.status_code)

    def map_to_dto(self, ohlc_data, coin) -> PriceCandlestick:
        candlestick_dtos = []
        for row in ohlc_data:
            candlestick = PriceCandlestick(
                close_time=row[0],
                open_price=row[1],
                high_price=row[2],
                low_price=row[3],
                close_price=row[4],
                volume=row[5],
                quote_volume=row[6],
                coin=coin,
            )
            candlestick_dtos.append(candlestick)
        return candlestick_dtos
