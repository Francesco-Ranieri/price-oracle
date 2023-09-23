from typing import List

from airflow.decorators import task
from common.entities.price_candlestick import PriceCandleStick
from tqdm import tqdm


@task
def insert_into_cassandra(data: List[PriceCandleStick]):
    
    from common.hooks.cassandra_hook import CassandraHook

    cassandra_hook = CassandraHook()
    insert_query = """
        INSERT INTO 
            price_candlestick (close_time, close_time_date, open_price, high_price, low_price, close_price, volume, quote_volume, coin, period, period_name)
        VALUES 
            (
                %(close_time)s,
                %(close_time_date)s,
                %(open_price)s,
                %(high_price)s,
                %(low_price)s,
                %(close_price)s,
                %(volume)s,
                %(quote_volume)s,
                %(coin)s,
                %(period)s,
                %(period_name)s
            )
    """
    
    for row in tqdm(data):
        cassandra_hook.run_query(
            insert_query, 
            parameters={
                "close_time": row.close_time,
                "close_time_date": row.close_time_date,
                "open_price": row.open_price,
                "high_price": row.high_price,
                "low_price": row.low_price,
                "close_price": row.close_price,
                "volume": row.volume,
                "quote_volume": row.quote_volume,
                "coin": row.coin,
                "period": row.period,
                "period_name": row.period_name
            }
        )