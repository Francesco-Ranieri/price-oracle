import datetime
import logging
from math import sqrt
from typing import List, Optional

import pandas as pd
from common.entities.metrics import Metrics
from common.entities.prediction import Prediction
from common.hooks.spark_hook import SparkHook
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error


def compute_metrics(
    source_data_path: str,
    predictions: List[Prediction],
    coin: str,
    model_name: str = "BASELINE",
) -> Metrics:
    spark_session = SparkHook(app_name=f"{__name__}:compute_metrics").get_spark_session()

    # Load the data from a pickle file
    logging.info(f"Loading data from {source_data_path}")
    df = pd.read_pickle(source_data_path)

    # Convert the data to a Spark DataFrame
    source_data_df = spark_session.createDataFrame(df)
    predictions_df = spark_session.createDataFrame(predictions)
    predictions_df = predictions_df.withColumnRenamed("close_price", "predicted_close_price")
    
    # Merge the source data with the predictions
    df = source_data_df.join(predictions_df, on=["close_time_date", "coin"], how="inner")
    df = df.dropna(subset=['predicted_close_price'])
    df = df.orderBy("close_time_date")

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metrics_list = []
    metrics = {
        "mse": {},
        "rmse": {},
        "mape": {},
    }

    for days in [df.count(), 90, 30, 7]:

        limited_data = df.limit(days).collect()
        source_values = [row.close_price for row in limited_data]
        predicted_values = [row.predicted_close_price for row in limited_data]

        metrics["mse"][days] = mean_squared_error(source_values, predicted_values)
        metrics["rmse"][days] = sqrt(mean_squared_error(source_values, predicted_values))
        metrics["mape"][days] = mean_absolute_percentage_error(source_values, predicted_values)

    for metric_name in ["mse", "rmse", "mape"]:
        metrics_list.append(
            Metrics(
                metric_name=metric_name,
                date=date,
                target=coin,
                metric_all=metrics[metric_name][df.count()],
                metric_90_d=metrics[metric_name][90],
                metric_30_d=metrics[metric_name][30],
                metric_7_d=metrics[metric_name][7],
                model_name=model_name
            )
        )

    return metrics_list