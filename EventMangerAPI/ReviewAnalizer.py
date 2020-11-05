import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tensorflow_datasets as tfds
import os

from tensorflow_core.python.keras.models import model_from_yaml


# embedding_layer = layers.Embedding(1000, 5)
# result = embedding_layer(tf.constant([1, 2, 3]))
#
# print(result.numpy())
# print(result.numpy().shape)

(trained_dataset, test_dataset), info = tfds.load('imdb_reviews/subwords8k', split=(tfds.Split.TRAIN, tfds.Split.TEST),
                                                  with_info=True, as_supervised=True)

encoder = info.features['text'].encoder
# print(encoder.subwords[:50])

BUFFER_SIZE = 10000
BATCH_SIZE = 64

padded_shapes = ([None], ())


trained_dataset = trained_dataset.shuffle(BUFFER_SIZE).padded_batch(BATCH_SIZE, padded_shapes=padded_shapes)
test_dataset = test_dataset.shuffle(BUFFER_SIZE).padded_batch(BATCH_SIZE, padded_shapes=padded_shapes)


try:
    # load YAML and create model
    yaml_file = open('EventMangerAPI/model2.yaml', 'r')
    loaded_model_yaml = yaml_file.read()
    yaml_file.close()
    model = model_from_yaml(loaded_model_yaml)
    # # load weights into new model
    model.load_weights("EventMangerAPI/model2.h5")
    print("Loaded model from disk")

except:
    model = keras.Sequential([layers.Embedding(encoder.vocab_size, 16),
                              layers.GlobalAveragePooling1D(),
                              layers.Dense(16, activation=tf.nn.relu),
                              layers.Dense(1, activation=tf.nn.sigmoid)])

    model.compile(loss='binary_crossentropy',
                  optimizer=keras.optimizers.Adam(1e-4),
                  metrics=['accuracy'])

    history = model.fit(trained_dataset,
                        epochs=40,
                        validation_data=test_dataset,
                        validation_steps=30)
    # serialize model to YAML
    model_yaml = model.to_yaml()
    with open("model2.yaml", "w") as yaml_file:
        yaml_file.write(model_yaml)
    # serialize weights to HDF5
    model.save_weights("model2.h5")
    print("Saved model to disk")


def pad_to_size(vec, size):
    zeros = [0] * (size - len(vec))
    vec.extend(zeros)
    return vec


def sample_predict(sentence, pad):
    encode_sample_pred_text = encoder.encode(sentence)
    if pad:
        encode_sample_pred_text = pad_to_size(encode_sample_pred_text, 64)

    encode_sample_pred_text = tf.cast(encode_sample_pred_text, tf.float32)
    predictions = model.predict(tf.expand_dims(encode_sample_pred_text, 0))
    print("Accuracy: " + str(predictions))
    return predictions


# sample_text = 'This is a good event'
# prediction = sample_predict(sample_text, pad=True) * 100
#
# print('Probability this is positive review %.2f' % prediction)
#
# sample_text = 'this is not a good event'
# prediction = sample_predict(sample_text, pad=True) * 100
#
# print('Probability this is positive review %.2f' % prediction)
