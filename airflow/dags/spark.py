import logging
from datetime import datetime, timedelta

from airflow.decorators import task
from pyspark.sql import SparkSession
from common.hooks.cassandra_hook import CassandraHook

from airflow import DAG

logging.basicConfig(level=logging.INFO)


@task
def fetch_data(coin: str = None):

    if not coin:
        raise ValueError("Coin must be provided")
    
    logging.info(f"Fetching data from Cassandra for {coin}")

    conn = CassandraHook.get_connection(conn_id="cassandra_default")
    spark = SparkSession.builder \
        .appName("CassandraSpark") \
        .master("spark://price-oracle-spark-master-svc:7077") \
        .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1") \
        .config("spark.cassandra.connection.host", conn.host) \
        .config("spark.cassandra.auth.username", conn.login) \
        .config("spark.cassandra.auth.password", conn.password) \
        .getOrCreate()

    df = spark.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(
            keyspace="mykeyspace",
            table="price_candlestick",
            url=conn.get_uri(),
            pushdown="true",  # Enable pushdown
        )\
        .load() \
        .filter(f"coin = '{coin}'")
    df.explain(extended=True)
    # keep only close pirce
    df = df[['close_price']]

    import numpy as np
    import pandas as pd
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import SimpleRNN, Dense
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    # Normalize the data
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df)

    # Create sequences of data
    def create_sequences(data, sequence_length):
        X, y = [], []
        for i in range(len(data) - sequence_length):
            X.append(data[i:i + sequence_length])
            y.append(data[i + sequence_length])
        return np.array(X), np.array(y)

    sequence_length = 10  # Define the sequence length
    X, y = create_sequences(scaled_data, sequence_length)

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Build the RNN model
    model = Sequential()
    model.add(SimpleRNN(50, activation='relu', input_shape=(sequence_length, 1)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')

    # Train the model
    model.fit(X_train, y_train, epochs=10, batch_size=32)

    # Evaluate the model on the testing set
    mse = model.evaluate(X_test, y_test)
    print(f"Mean Squared Error on Test Set: {mse}")

    # Make predictions for future prices
    next_sequence = X[-1].reshape(1, sequence_length, 1)
    next_price = model.predict(next_sequence)
    denormalized_price = scaler.inverse_transform(np.array([[next_price]]))
    print(f"Predicted Next Price: {denormalized_price[0][0]}")

# @task
# def train_model(data_path: str):
#     import numpy as np
#     import pandas as pd
#     import tensorflow as tf
#     from tensorflow.keras.models import Sequential
#     from tensorflow.keras.layers import SimpleRNN, Dense
#     from sklearn.model_selection import train_test_split
#     from sklearn.preprocessing import MinMaxScaler

#     # Load your dataset using pandas
#     data = pd.read_csv(data_path)
#     data = data[['close_price']]

#     # Normalize the data
#     scaler = MinMaxScaler()
#     scaled_data = scaler.fit_transform(data)

#     # Create sequences of data
#     def create_sequences(data, sequence_length):
#         X, y = [], []
#         for i in range(len(data) - sequence_length):
#             X.append(data[i:i + sequence_length])
#             y.append(data[i + sequence_length])
#         return np.array(X), np.array(y)

#     sequence_length = 10  # Define the sequence length
#     X, y = create_sequences(scaled_data, sequence_length)

#     # Split the data into training and testing sets
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#     # Build the RNN model
#     model = Sequential()
#     model.add(SimpleRNN(50, activation='relu', input_shape=(sequence_length, 1)))
#     model.add(Dense(1))
#     model.compile(optimizer='adam', loss='mean_squared_error')

#     # Train the model
#     model.fit(X_train, y_train, epochs=10, batch_size=32)

#     # Evaluate the model on the testing set
#     mse = model.evaluate(X_test, y_test)
#     print(f"Mean Squared Error on Test Set: {mse}")

#     # Make predictions for future prices
#     next_sequence = X[-1].reshape(1, sequence_length, 1)
#     next_price = model.predict(next_sequence)
#     denormalized_price = scaler.inverse_transform(np.array([[next_price]]))
#     print(f"Predicted Next Price: {denormalized_price[0][0]}")


# @task
# def train_model(data_path: str):
#     import pandas as pd

#     # Load your dataset using pandas
#     df = pd.read_csv(data_path)
#     df = df[['close_price']]


#     # Create a SparkSession
#     conn = CassandraHook.get_connection(conn_id="cassandra_default")
#     spark = SparkSession.builder \
#         .appName("Trainer") \
#         .master("spark://price-oracle-spark-master-svc:7077") \
#         .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1") \
#         .config("spark.cassandra.connection.host", conn.host) \
#         .config("spark.cassandra.auth.username", conn.login) \
#         .config("spark.cassandra.auth.password", conn.password) \
#         .getOrCreate()

#     # Load your time series data into a DataFrame
#     # Ensure the DataFrame has two columns: "timestamp" and "value"


with DAG(
    "spark_load_data_from_cassandra",
    schedule="@once",
    start_date=datetime.now() - timedelta(days=1),
    default_args={
        "owner": "ranierifr"
    },
    is_paused_upon_creation=False,
    tags=["spark"]
) as dag:
    data_filename = fetch_data("BTCUSD")
    #@train_model(data_filename)


if __name__ == "__main__":
    dag.test()
