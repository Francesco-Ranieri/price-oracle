import logging
from typing import List

import requests
from common.entities.price_candlestick import PriceCandleStick

# Define a custom exception for HTTP errors
class HTTPError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"HTTP request failed with status code {status_code}")


class CryptoWatchClient:
    def __init__(self, exchange="binance"):
        self.PRICES_BASE_URL = "https://api.cryptowat.ch"
        self.PRICES_OHLC_PATH = "/markets/:exchange/:pair/ohlc"
        self.exchange = exchange

    def fetch_ohlc_data(
        self, coin_pair="BTCUSDT", after=None, before=None
    ) -> List[PriceCandleStick]:
        data = self.__fetch_ohlc_data__(coin_pair, after, before)
        return self.map_to_model(data, coin_pair)

    def __fetch_ohlc_data__(
        self, coin_pair="BTCUSDT", after=None, before=None
    ) -> PriceCandleStick:
        url = self.PRICES_BASE_URL + self.PRICES_OHLC_PATH.replace(
            ":exchange", self.exchange
        ).replace(":pair", coin_pair)

        params = {
            # "periods": self.PRICES_PERIODS,
            "after": after,
            "before": before,
        }

        logging.info(f"Sending request to {url}, with params {params}")
        response = requests.get(url, params=params)

        if response.status_code != 200:
            logging.error(
                f"HTTP request failed with status code {response.status_code}"
            )
            logging.error(response.json())
            raise HTTPError(response.status_code)

        ohlc_data = PriceCandleStick.model_validate(response.json())
        return ohlc_data


