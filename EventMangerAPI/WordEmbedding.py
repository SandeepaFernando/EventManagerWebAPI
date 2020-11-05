import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tensorflow_datasets as tfds
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

embedding_layer = layers.Embedding(100, 5)
result = embedding_layer(tf.constant([1, 2]))

print(result.numpy())
print(result.numpy().shape)
