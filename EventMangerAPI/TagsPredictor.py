import pickle
from rest_framework.response import Response
import nltk
import numpy
from nltk.stem import WordNetLemmatizer
from nltk.stem.lancaster import LancasterStemmer
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import model_from_yaml

from EventMangerAPI.models import Event
# graph = tf.compat.v1.get_default_graph()
from EventMangerAPI.serializers import EventTagsSerializer

# import tensorflow as tf

stemmer = LancasterStemmer()
wordnet_lemmatizer = WordNetLemmatizer()


def trainTheModel():
    data = Event.objects.all()

    words = []
    labels = []
    docs_x = []
    docs_y = []

    for event in data:
        _words = nltk.word_tokenize(event.description)
        words.extend(_words)
        docs_x.append(event.description)
        eventId = str(event.pk)
        docs_y.append(eventId)

        if eventId not in labels:
            labels.append(eventId)

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

    if not inputText:
        response = []
        return response

    try:
        with open("data.pickle", "rb") as f:
            words, labels, training, output = pickle.load(f)

    except:
        data = Event.objects.all()
        words = []
        labels = []
        docs_x = []
        docs_y = []

        for event in data:
            _words = nltk.word_tokenize(event.description)
            words.extend(_words)
            docs_x.append(event.description)
            eventId = str(event.pk)
            docs_y.append(eventId)

            if eventId not in labels:
                labels.append(eventId)

        words = [stemmer.stem(w.lower()) for w in words]
        words = sorted(list(set(words)))

        labels = sorted(labels)

    try:
        yaml_file = open('model.yaml', 'r')
        loaded_model_yaml = yaml_file.read()
        yaml_file.close()
        model = model_from_yaml(loaded_model_yaml)
        # # load weights into new model
        model.load_weights("model.h5")
        print("Loaded model from disk")

    except:
        trainTheModel()
        yaml_file = open('model.yaml', 'r')
        loaded_model_yaml = yaml_file.read()
        yaml_file.close()
        model = model_from_yaml(loaded_model_yaml)
        # # load weights into new model
        model.load_weights("model.h5")
        print("Loaded model from disk")

    currentText = create_bag(inputText, words)
    currentTextArray = [currentText]
    numpyCurrentText = numpy.array(currentTextArray)

    if numpy.all((numpyCurrentText == 0)):
        response = []
        return response

    predictions = model.predict(numpyCurrentText[0:1])
    result_index = numpy.argmax(predictions)
    print("Accuracy: " + str(predictions[0][result_index]))
    tag = labels[result_index]
    response = getAnswer(tag)
    return response


def getAnswer(eventId):
    event = Event.objects.raw("SELECT * FROM eventmanagernew.eventmangerapi_event WHERE "
                              "eventmanagernew.eventmangerapi_event.id = " + eventId)
    if event:
        serializer = EventTagsSerializer(event[0].eventTags, many=True)
        return serializer.data
    else:
        return []
