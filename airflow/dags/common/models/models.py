import keras.backend as K
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow import keras


def mean_absolute_percentage_error_keras(y_true, y_pred):
    diff = K.abs((y_true - y_pred) / K.clip(K.abs(y_true), K.epsilon(), None))
    return 100.0 * K.mean(diff, axis=-1)


# Create sequences of data to be used for training
def create_sequences(data, sequence_length):
    sequences = []
    target = []
    for i in range(len(data) - sequence_length):
        sequences.append(data[i:i+sequence_length])
        target.append(data[i+sequence_length])
    return np.array(sequences), np.array(target)


def get_splits(data, sequence_length: int, output_shape: int):

    X, y = create_sequences(data, sequence_length)
    _X_train, X_test, _y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    X_train, X_val, y_train, y_val = train_test_split(_X_train, _y_train, test_size=0.2, shuffle=False)

    if output_shape:
        if output_shape < 1:
            raise ValueError("Error: output_shape must be greater than 0")
        y_train = y_train[:, :output_shape]
        y_test = y_test[:, :output_shape]
        y_val = y_val[:, :output_shape]

    return X_train, X_test, X_val, y_train, y_test, y_val


def build_model(
    data,
    units_per_layer,
    sequence_length,
    learning_rate,
    dropout_rate,
    layer_class,
    optimizer = 'Adam',
    activation = 'relu',
    weight_decay = 0.01,
    output_shape = None
):
    if output_shape is None:
        output_shape = data.shape[1]

    # Build and compile the NN model
    model = keras.Sequential()
    for units in units_per_layer[:-1]:
        model.add(layer_class(units, activation=activation, return_sequences=True, input_shape=(sequence_length, data.shape[1])))
        model.add(keras.layers.Dropout(dropout_rate))
    model.add(layer_class(units_per_layer[-1], activation=activation, input_shape=(sequence_length, data.shape[1])))
    model.add(keras.layers.Dropout(dropout_rate))
    model.add(keras.layers.Dense(output_shape))

    if optimizer == 'Adam':
        optimizer = keras.optimizers.Adam(learning_rate=learning_rate, clipvalue=1.0, weight_decay=weight_decay)
    elif optimizer == 'SGD':
        optimizer = keras.optimizers.SGD(learning_rate=learning_rate, clipvalue=1.0, weight_decay=weight_decay)
    model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=[mean_absolute_percentage_error_keras])

    return model