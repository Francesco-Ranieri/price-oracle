from typing import List

from airflow.decorators import task

import os
import sys
root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'dags'))
sys.path.append(root_folder)

from common.dtos.crypto_data_dto import CryptoDataDTO
from common.entities.price_candlestick import PriceCandleStick
from common.mapper.crypto_data_mapper import CryptoDataMapper


@task
def fetch_data(file_path: str) -> PriceCandleStick:
    """
    Load data from CSV and convert into PriceCandleStick
    """
    
    import pandas as pd

    df = pd.read_csv(file_path, skiprows=1)
    df = df.rename(columns={
        df.columns[-2]: "volume_crypto",
        df.columns[-1]: "volume_usd"
    })

    data = df.to_dict("records") 
    data: List[CryptoDataDTO] = [CryptoDataDTO.model_validate(item) for item in data]
    data: List[PriceCandleStick] = [CryptoDataMapper.to_price_candlestick(item) for item in data]

    return data
