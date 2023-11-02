import logging
from typing import List

import requests
from common.entities.price_candlestick import PriceCandleStick
from common.mappers.kraken_mapper import KrakenMapper
from common.dtos.kraken_dto import KrakenDTO

# Define a custom exception for HTTP errors
class HTTPError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"HTTP request failed with status code {status_code}")


class KrakenClient:
    def __init__(
        self,
        interval = 1440
    ):
        self.PRICES_BASE_URL = "https://api.kraken.com/0/public/OHLC"
        self.INTERVAL = interval

    def fetch_ohlc_data(
        self, 
        coin_pair="BTCUSDT",
        since=None
    ) -> List[PriceCandleStick]:

        params = {
            "pair": coin_pair,
            "interval": self.INTERVAL,
            "since": since
        }

        response = requests.get(self.PRICES_BASE_URL, params=params)
        logging.info(f"HTTP GET request to {response.url}")

        if response.status_code != 200:
            logging.error(
                f"HTTP request failed with status code {response.status_code}"
            )
            logging.error(response.json())
            raise HTTPError(response.status_code)

        return KrakenDTO.parse_obj(response.json())
        