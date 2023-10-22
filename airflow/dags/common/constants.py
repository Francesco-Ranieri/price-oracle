import os

DATA_PATH = os.path.join("assets", "binance_1d")
FILE_NAMES = [file_name for file_name in os.listdir(DATA_PATH) if file_name.endswith(".csv")]
