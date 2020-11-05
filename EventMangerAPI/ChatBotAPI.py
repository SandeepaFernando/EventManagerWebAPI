import json
import pickle
import random

import nltk
import numpy
from nltk.stem import LancasterStemmer
from tensorflow_core.python.keras.layers import Dense
from tensorflow_core.python.keras.models import Sequential
from tensorflow_core.python.keras.models import model_from_yaml

nltk.download('punkt')

stemmer = LancasterStemmer()

with open("EventMangerAPI/intents.json") as file:
    data = json.load(file)

try:
    with open("EventMangerAPI/chatbodmodel.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)
except:
    words = []
    labels = []
    docs_x = []
    docs_y = []

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"]
    words = sorted(list(set(words)))

    labels = sorted(labels)

    training = []
    output = []

    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []

        wrds = [stemmer.stem(w.lower()) for w in doc]

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

    with open("EventMangerAPI/chatbodmodel.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

try:
    # load YAML and create model
    yaml_file = open('EventMangerAPI/chatbodmodel.yaml', 'r')
    loaded_model_yaml = yaml_file.read()
    yaml_file.close()
    myChatModel = model_from_yaml(loaded_model_yaml)
    # # load weights into new model
    myChatModel.load_weights("EventMangerAPI/chatbodmodel.h5")
    print("Loaded model from disk")


except:
    # Make the neural network
    myChatModel = Sequential()
    myChatModel.add(Dense(8, input_shape=[len(words)], activation='relu'))
    myChatModel.add(Dense(len(labels), activation='softmax'))

    # optimize the model
    myChatModel.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    # train the model
    myChatModel.fit(training, output, epochs=1000, batch_size=8)

    # serialize model to YAML
    model_yaml = myChatModel.to_yaml()
    with open("EventMangerAPI/chatbodmodel.yaml", "w") as yaml_file:
        yaml_file.write(model_yaml)
    # serialize weights to HDF5
    myChatModel.save_weights("EventMangerAPI/chatbodmodel.h5")
    print("Saved model to disk")


def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return numpy.array(bag)


def chat(inp):
    responses = "I didn't get that, try again!"

    currentText = bag_of_words(inp, words)
    currentTextArray = [currentText]
    numpyCurrentText = numpy.array(currentTextArray)
    results = myChatModel.predict(numpyCurrentText[0:1])
    results_index = numpy.argmax(results)
    tag = labels[results_index]

    if numpy.all((numpyCurrentText == 0)):
        return "I didn't get that, try again!"

    if results[0][results_index] > 0.7:
        for tg in data["intents"]:
            if tg['tag'] == tag:
                responses = tg['responses']

        return random.choice(responses)
    else:
        return "I didn't get that, try again!"

# def chat():
#     print("Start talking with the bot (type quit to stop)!")
#     while True:
#         inp = input("You: ")
#         if inp.lower() == "quit":
#             break
#
#         currentText = bag_of_words(inp, words)
#         currentTextArray = [currentText]
#         numpyCurrentText = numpy.array(currentTextArray)
#         results = myChatModel.predict(numpyCurrentText[0:1])
#         results_index = numpy.argmax(results)
#         tag = labels[results_index]
#
#         for tg in data["intents"]:
#             if tg['tag'] == tag:
#                 responses = tg['responses']
#
#         print(random.choice(responses))
#     else:
#         print("I didn't get that, try again!")
