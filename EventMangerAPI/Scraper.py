import pickle
from datetime import datetime

import bs4
import nltk
import numpy
import requests
import tensorflow
from nltk.stem import WordNetLemmatizer
from nltk.stem.lancaster import LancasterStemmer
from tensorflow_core.python.keras.models import model_from_yaml

from EventMangerAPI.models import Event, ScrapedEventTags, ScrapedEvent, Skill
from EventMangerAPI.serializers import EventTagsSerializer

stemmer = LancasterStemmer()
wordnet_lemmatizer = WordNetLemmatizer()


def scrapeTheSite():
    res = requests.get('https://www.eventbrite.com/d/online/all-events/?page=1')
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    pp = soup.find_all('article',
                       class_='eds-l-pad-all-4 eds-event-card-content eds-event-card-content--list '
                              'eds-event-card-content--mini eds-event-card-content--square eds-l-pad-vert-3')
    for article in pp:
        date = article.find('div', class_='eds-text-color--primary-brand eds-l-pad-bot-1 eds-text-weight--heavy '
                                          'eds-text-bs').text

        print(date)
        if 'PM' in date:
            date = date[:date.rfind('PM') + 2]
        else:
            date = date[:date.rfind('AM') + 2]

        description = article.h3.find('div', class_='eds-is-hidden-accessible').text
        if date:
            date = datetime.strptime(date, '%a, %b %d, %Y %I:%M %p')
            print(date)
            print('')
            save_ScrapedData("title", description, date)


def get_EventList():
    events_list = Event.objects.all()
    return events_list


def get_WordsAndLabels(event_list):
    word_list = []
    label_list = []
    for event in event_list:
        _words = nltk.word_tokenize(event.description)
        word_list.extend(_words)
        eventId = str(event.pk)

        if eventId not in label_list:
            label_list.append(eventId)

    word_list = [stemmer.stem(w.lower()) for w in word_list]
    word_list = sorted(list(set(word_list)))

    label_list = sorted(label_list)

    return word_list, label_list


def get_xAxisAndYAxisList(event_list):
    xAxis_list = []
    yAxis_list = []
    for event in event_list:
        xAxis_list.append(event.description)
        eventId = str(event.pk)
        yAxis_list.append(eventId)

    return xAxis_list, yAxis_list


def get_trainingAndOutPutDataList(word_list, label_list, xAxis_list, yAxis_list):
    training_input_data_list = []
    training_output_data_list = []

    temp_out = [0 for _ in range(len(label_list))]

    for i, desc in enumerate(xAxis_list):
        bag = []

        temp_words = [stemmer.stem(w.lower()) for w in nltk.word_tokenize(desc)]

        for w in word_list:
            if w in temp_words:
                bag.append(1)
            else:
                bag.append(0)

        out = temp_out[:]
        out[label_list.index(yAxis_list[i])] = 1

        training_input_data_list.append(bag)
        training_output_data_list.append(out)

    return training_input_data_list, training_output_data_list

try:
    with open("EventMangerAPI/scraper.pickle", "rb") as f:
        saved_word_list, saved_label_list, saved_training_input_data_list, saved_training_output_data_list = pickle.load(f)

    yaml_file = open('EventMangerAPI/scraper.yaml', 'r')
    loaded_model_yaml = yaml_file.read()
    yaml_file.close()
    saved_model = model_from_yaml(loaded_model_yaml)
    # # load weights into new model
    saved_model.load_weights("EventMangerAPI/scraper.h5")
    print("Loaded model from disk")

except:
    print("Scraper model not trained yet")

def train_TheScraper():
    my_event_list = get_EventList()

    word_list, label_list = get_WordsAndLabels(my_event_list)
    xAxis_list, yAxis_list = get_xAxisAndYAxisList(my_event_list)

    training_input_data_list, training_output_data_list = get_trainingAndOutPutDataList(word_list, label_list,
                                                                                        xAxis_list, yAxis_list)

    with open("EventMangerAPI/scraper.pickle", "wb") as f:
        pickle.dump((word_list, label_list, training_input_data_list, training_output_data_list), f)

    network_model = tensorflow.keras.models.Sequential()
    network_model.add(tensorflow.keras.layers.Dense(8, input_shape=[len(word_list)], activation='relu'))
    network_model.add(tensorflow.keras.layers.Dense(len(label_list), activation='softmax'))

    network_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    network_model.fit(training_input_data_list, training_output_data_list, epochs=1000, batch_size=8)

    model_to_yaml = network_model.to_yaml()
    with open("EventMangerAPI/scraper.yaml", "w") as yaml_file:
        yaml_file.write(model_to_yaml)
    # serialize weights to HDF5
    network_model.save_weights("EventMangerAPI/scraper.h5")
    print("Saved model to disk")


def convert_descriptionToBag(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return numpy.array(bag)

def save_ScrapedData(title, description, event_date):
    if description:

        description_bag_of_words = convert_descriptionToBag(description, saved_word_list)
        currentTextArray = [description_bag_of_words]
        numpyCurrentText = numpy.array(currentTextArray)

        if numpy.all((numpyCurrentText == 0)):
            response = []
            return response

        predictions = saved_model.predict(numpyCurrentText[0:1])
        result_index = numpy.argmax(predictions)
        print("Accuracy: " + str(predictions[0][result_index]))
        matched_event = saved_label_list[result_index]
        matching_tags = get_TagsForMatchingEvents(matched_event)

        if matching_tags:
            save_ScrapedEvents(title, description, event_date, matching_tags)


def get_TagsForMatchingEvents(eventId):
    event = Event.objects.raw("SELECT * FROM eventmanagernew.eventmangerapi_event WHERE "
                              "eventmanagernew.eventmangerapi_event.id = " + eventId)
    if event:
        serializer = EventTagsSerializer(event[0].eventTags, many=True)
        return serializer.data
    else:
        return []


def save_ScrapedEvents(title, description, event_date, event_tags):
    saved_event = ScrapedEvent.objects.create(title=title, description=description, eventDate=event_date)

    for tag in event_tags:
        skill_tag = Skill()
        skill_tag.pk = tag['tagId']
        skill_tag.tagName = tag['tagName']
        ScrapedEventTags.objects.create(tagId=skill_tag, eventId=saved_event)
