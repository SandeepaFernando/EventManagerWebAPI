import nltk
from nltk.stem.lancaster import LancasterStemmer
from nltk.stem import WordNetLemmatizer

import numpy

import random
import json
import pickle
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import model_from_yaml

# import tensorflow as tf

# graph = tf.compat.v1.get_default_graph()

stemmer = LancasterStemmer()
wordnet_lemmatizer = WordNetLemmatizer()

with open("tags.json") as file:
    data = json.load(file)

try:
    with open("data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)

except:
    words = []
    labels = []
    docs_x = []
    docs_y = []

    for intent in data["allTags"]:
        for pattern in intent["description"]:
            _words = nltk.word_tokenize(pattern)
            words.extend(_words)
            docs_x.append(pattern)
            docs_y.append(intent["category"])

        if (intent["category"]) not in labels:
            labels.append(intent["category"])

    words = [stemmer.stem(w.lower()) for w in words]
    words = sorted(list(set(words)))

    labels = sorted(labels)

    training = []
    output = []

    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []

        wrds = [stemmer.stem(w.lower()) for w in nltk.word_tokenize(doc)]

        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)

    training = numpy.array(training)
    output = numpy.array(output)

    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

try:
    # load YAML and create model
    yaml_file = open('model.yaml', 'r')
    loaded_model_yaml = yaml_file.read()
    yaml_file.close()
    model = model_from_yaml(loaded_model_yaml)
    # # load weights into new model
    model.load_weights("model.h5")
    print("Loaded model from disk")

except:
    # Make the neural network
    model = Sequential()
    model.add(Dense(8, input_shape=[len(words)], activation='relu'))
    model.add(Dense(len(labels), activation='softmax'))
    model.summary()

    # optimize the model
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    # train the model
    model.fit(training, output, epochs=1000, batch_size=8)

    # serialize model to YAML
    model_yaml = model.to_yaml()
    with open("model.yaml", "w") as yaml_file:
        yaml_file.write(model_yaml)
    # serialize weights to HDF5
    model.save_weights("model.h5")
    print("Saved model to disk")


def chat():
    print("Start talking with the bot (type quit to stop)!")
    while True:
        inp = input("You: ")
        if inp.lower() == "quit":
            break
        print(predictResult(inp))


def create_bag(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return numpy.array(bag)


def predictResult(inputText):
    # global graph
    # with graph.as_default():
    currentText = create_bag(inputText, words)
    currentTextArray = [currentText]
    numpyCurrentText = numpy.array(currentTextArray)
    predictions = model.predict(numpyCurrentText[0:1])
    result_index = numpy.argmax(predictions)
    tag = labels[result_index]
    response = getAnswer(tag)
    return response


def getAnswer(tag):
    for tg in data["allTags"]:
        if tg['category'] == tag:
            responses = tg['tags']
    return random.choice(responses)


chat()
