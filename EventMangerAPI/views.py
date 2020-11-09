from datetime import datetime
import json
from multiprocessing import Process

from django.db import connection
from django.http import HttpResponse
# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import threading
import EventMangerAPI.ReviewAnalizer as ra
import EventMangerAPI.TagsPredictor as tp
from EventMangerAPI.models import Skill, User, Event, Device, ScrapedEvent, EventBid, EventComment
from EventMangerAPI.serializers import UserSerializer, SkillSerializer, VendorSerializer, EventSerializer, \
    SaveEventSerializer, SaveVendorSerializer, EventBidSerializer, EventCommentSerializer, SaveEventCommentSerializer, \
    BotQuestionSerializer
import EventMangerAPI.FirebasePushManager as massenger
import EventMangerAPI.ChatBotAPI as bot
from EventMangerAPI import Scraper as sp


def home(request):
    return HttpResponse("Everything is ok")


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        userObj = UserSerializer().to_representation(user)

        return Response({
            'response': "Successfully logged in",
            'user': userObj,
            'token': token.key
        })


@api_view(['POST', ])
@permission_classes((AllowAny,))
def register(request):
    serializer = UserSerializer(data=request.data)
    data = {}
    if serializer.is_valid():
        serializer.save()
        data['response'] = "Successfully registered"
        data['user'] = serializer.data
    else:
        data = serializer.errors

    return Response(data)


class OrganizerAPIView(APIView):
    def put(self, request):
        data = request.data
        snippet = User.objects.get(id=data['id'])
        serializer = UserSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


@api_view(['POST', ])
@permission_classes((AllowAny,))
def registerVendor(request):
    serializer = SaveVendorSerializer(data=request.data)
    data = {}
    if serializer.is_valid():
        serializer.save()
        data['response'] = "Successfully registered"
        data['user'] = serializer.data
    else:
        data = serializer.errors

    return Response(data)


class VendorAPIView(APIView):
    def put(self, request, id=None):
        data = request.data
        snippet = User.objects.get(id=data['id'])
        serializer = SaveVendorSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes((AllowAny,))
def getSkills(request):
    skills = Skill.objects.all()
    serializers = SkillSerializer(skills, many=True)
    return Response(serializers.data)


@api_view(['GET'])
def getVendors(request):
    vendors = User.objects.raw("select table1.*, CASE WHEN table1.rating >= 8 then 'Platinum' WHEN table1.rating >= 5 "
                               "then 'Gold' ELSE 'Silver' END as rateCategory from (SELECT *, IFNULL((SELECT SUM("
                               "sentimentValue) FROM eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = "
                               "eventmanagernew.eventmangerapi_user.id) / (SELECT count(*) FROM "
                               "eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = "
                               "eventmanagernew.eventmangerapi_user.id), 0)as rating FROM "
                               "eventmanagernew.eventmangerapi_user) table1 WHERE table1.userType = 3")
    serializers = VendorSerializer(vendors, many=True)
    return Response(serializers.data)


@api_view(['GET'])
def getAllQuestions(request):
    question = User.objects.raw("SELECT * FROM `eventmangerapi_userquestions`")
    serializers = BotQuestionSerializer(question, many=True)
    return Response(serializers.data)


class EventAPIView(APIView):
    def get(self, request):
        organizerId = request.query_params.get("organizerId")
        vendorId = request.query_params.get("vendorId")
        eventId = request.query_params.get("eventId")
        if vendorId:
            events = Event.objects.raw("SELECT * FROM eventmanagernew.eventmangerapi_event WHERE "
                                       "eventmanagernew.eventmangerapi_event.id IN(SELECT distinct eventId_id FROM  "
                                       "eventmanagernew.eventmangerapi_eventtags WHERE "
                                       "eventmanagernew.eventmangerapi_eventtags.tagId_id IN (SELECT tagId_id FROM "
                                       "eventmanagernew.eventmangerapi_vendorskill WHERE userId_id = " + vendorId + "))")
        else:
            if eventId:
                events = Event.objects.raw("SELECT * FROM eventmanagernew.eventmangerapi_event WHERE "
                                           "eventmanagernew.eventmangerapi_event.id = " + eventId)
            else:
                if organizerId:
                    events = Event.objects.raw("SELECT * FROM eventmanagernew.eventmangerapi_event WHERE "
                                               "eventmanagernew.eventmangerapi_event.organizer_id = " + organizerId)
                else:
                    events = Event.objects.all()

        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=200)

    def post(self, request):
        data = request.data
        serializer = SaveEventSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, id=None):
        data = request.data
        snippet = Event.objects.get(id=data['id'])
        serializer = SaveEventSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET'])
def checkReview(request):
    text = request.GET.get("text")
    percent = float(ra.sample_predict(text, pad=True)) * 100
    prediction = int((percent + 5) / 10)
    if prediction >= 9:
        result = "Very Good"
    elif prediction >= 6:
        result = "Good"
    elif prediction >= 3:
        result = "Neutral"
    else:
        result = "Bad"

    return HttpResponse('{'
                        '"predictionString": "' + result + '",'
                                                           '"prediction": ' + str(prediction) +
                        '}',
                        content_type="application/json")


@api_view(['GET'])
def trainTagsPredictor(request):
    try:
        x = threading.Thread(target=tp.trainTheModel(), args=(1,))
        x.start()
        # tp.trainTheModel()
        data = {'response': "Successfully started training"}
        return Response(data)

    except Exception as e:
        print(e)
        data = {'response': "Failed training"}
        return Response(data)


@api_view(['GET'])
def predictTags(request):
    text = request.GET.get("text")
    try:
        result = tp.predictResult(text)
        data = {
            'tags': result
        }
        return Response(data)

    except:
        data = {'tags': []}
        return Response(data)


@api_view(['GET', 'POST'])
def updatePushToken(request):
    push_token = request.POST.get('push_token')
    deviceId = request.POST.get('device_id')
    userId = request.POST.get('user_id')

    if push_token:
        devices = Device.objects.filter(deviceId=deviceId)
        if devices and len(devices) > 1:
            devices.delete()

        profile = Device.objects.filter(deviceId=deviceId).first()

        if not profile:
            user = User.objects.get(pk=userId)
            profile = Device()
            profile.userId = user

        profile.push_token = push_token
        profile.deviceId = deviceId

        try:
            profile.save()
            return HttpResponse(json.dumps({'success': True}), content_type="application/json")
        except (ValueError, Exception):
            return HttpResponse(json.dumps({'success': False}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({'success': False}), content_type="application/json")


@api_view(['GET', 'POST'])
def acceptBidder(request):
    bidId = request.POST.get('bidId')
    if bidId:
        bid = get_object_or_404(EventBid, pk=bidId)
        if bid:
            event = Event.objects.get(pk=bid.eventId.id)
            bidder = User.objects.get(pk=bid.bidder.id)
            if bidder:
                if bidder.userType == 3:
                    event.acceptedVendor = bidder
                    event.save()
                    sendMessageToDevices(bidder.id, "Bid accepted",
                                         "You bid is accepted for the event:" + event.title, {
                                             "eventId": str(event.id)
                                         })
                    return HttpResponse(json.dumps({'success': True}), content_type="application/json")
                else:
                    return HttpResponse(json.dumps({'success': False}), content_type="application/json")
            else:
                return HttpResponse(json.dumps({'success': False}), content_type="application/json")
        else:
            return HttpResponse(json.dumps({'success': False}), content_type="application/json")
    else:
        return HttpResponse(json.dumps({'success': False}), content_type="application/json")


@api_view(['GET'])
def chat(request):
    text = request.GET.get("text")
    try:
        result = bot.chat(text)
        data = {
            'response': result
        }
        return Response(data)

    except:
        data = {'response': "I didn't get that, try again!"}
        return Response(data)


@api_view(['GET'])
def scraperTrain(request):
    try:
        x = threading.Thread(target=sp.train_TheScraper(), args=(1,))
        x.start()
        data = {'response': "Successfully started training"}
        return Response(data)

    except:
        data = {'response': "Failed training"}
        return Response(data)


@api_view(['GET'])
def scrapeTheSite(request):
    # try:
    p = Process(target=sp.scrapeTheSite())
    p.start()
    data = {'response': "Successfully completed the task"}
    return Response(data)

    # except (ValueError, Exception):
    #     data = {'response': "Failed training"}
    #     return Response(data)


@api_view(['GET'])
def checkDateAvailability(request):
    try:
        date = request.GET.get("date")
        tags = request.GET.get("tags")
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

        events = ScrapedEvent.objects.raw(
            "SELECT * FROM eventmanagernew.eventmangerapi_scrapedevent WHERE DATE(eventDate) = " +
            "DATE('" + str(date) + "') AND id IN(SELECT distinct eventId_id FROM " +
            "eventmanagernew.eventmangerapi_scrapedeventtags WHERE tagId_id IN(" + tags + "))")

        if not events:
            data = {
                'response': "Date is available",
                'isDateAvailable': True
            }
        else:
            data = {
                'response': "Date is not available",
                'isDateAvailable': False
            }
        return Response(data)

    except:
        data = {'response': "Something went wrong"}
        return Response(data)


@api_view(['GET'])
def filterVendors(request):
    budget = request.GET.get("budget")
    eventDate = request.GET.get("eventDate")
    tags = request.GET.get("tags")

    sql = "select table1.*, CASE WHEN table1.rating >= 8 then 'Platinum' WHEN table1.rating >= 5 then 'Gold' ELSE " \
          "'Silver' END as rateCategory from (SELECT *, IFNULL((SELECT SUM(sentimentValue) FROM " \
          "eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = eventmanagernew.eventmangerapi_user.id) / (SELECT " \
          "count(*) FROM eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = " \
          "eventmanagernew.eventmangerapi_user.id), 0)as rating FROM eventmanagernew.eventmangerapi_user) table1 WHERE " \
          "table1.userType = 3 "

    if budget:
        sql += " AND minBudget <= " + budget + " AND maxBudget >= " + budget

    if eventDate:
        sql += " AND id NOT IN (SELECT IFNULL(acceptedVendor_id, '') FROM " \
               "eventmanagernew.eventmangerapi_event WHERE DATE(eventDate) = DATE('" + eventDate + "')) "

    if tags:
        sql += " AND id IN(SELECT userId_id FROM eventmanagernew.eventmangerapi_vendorskill WHERE " \
               "tagId_id IN(" + tags + ")) "

    vendors = User.objects.raw(sql)

    serializers = VendorSerializer(vendors, many=True)
    return Response(serializers.data)


class EventBidAPIView(APIView):
    def delete(self, request, pk):
        try:
            snippet = EventBid.objects.get(id=pk)
            if snippet:
                snippet.delete()
                data = {'response': "Delete success"}
                return Response(data, status=201)
        except EventBid.DoesNotExist:
            data = {'response': "Bid not found"}
            return Response(data, status=404)

    def post(self, request):
        data = request.data
        serializer = EventBidSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, id=None):
        data = request.data
        snippet = EventBid.objects.get(id=data['id'])
        serializer = EventBidSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class EventCommentAPIView(APIView):
    def delete(self, request, pk):
        try:
            snippet = EventComment.objects.get(id=pk)
            if snippet:
                snippet.delete()
                data = {'response': "Delete success"}
                return Response(data, status=201)
        except EventComment.DoesNotExist:
            data = {'response': "Comment not found"}
            return Response(data, status=404)

    def post(self, request):
        data = request.data
        serializer = SaveEventCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, id=None):
        data = request.data
        snippet = EventComment.objects.get(id=data['id'])
        serializer = SaveEventCommentSerializer(snippet, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['GET'])
def get_vendor_count_by_budget(request):
    budget = request.GET.get("budget")
    tags = request.GET.get("tags")
    sql_query = "select COUNT(*) AS numberOfVendors, CASE WHEN myTable.rating >= 8 then 'Platinum' WHEN myTable.rating " \
                ">= 5 then 'Gold' ELSE 'Silver' END as rateCategory from (SELECT *, IFNULL((SELECT SUM(" \
                "sentimentValue) FROM eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = " \
                "eventmanagernew.eventmangerapi_user.id) / (SELECT count(*) FROM " \
                "eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = eventmanagernew.eventmangerapi_user.id), " \
                "0)as rating FROM eventmanagernew.eventmangerapi_user) myTable WHERE myTable.userType = 3  AND minBudget <= "  \
                + budget + " AND maxBudget >= " + budget + " AND id IN(SELECT userId_id FROM " \
                                                           "eventmanagernew.eventmangerapi_vendorskill WHERE tagId_id" \
                                                           " IN(" + tags + ")) group by rateCategory"

    data = {}
    try:
        cursor = connection.cursor()
        cursor.execute(sql_query)
        result = []
        dbResult = cursor.fetchall()
        if dbResult:
            for row in dbResult:
                content = {"numberOfVendors": row[0], "rateCategory": row[1]}
                result.append(content)
                data['result'] = result
        else:
            data['result'] = []
    except:
        data['result'] = []

    return Response(data)


def sendMessageToDevices(userId, title, msg, data=None):
    result = []
    tokens = Device.objects.raw(
        "SELECT * FROM eventmanagernew.eventmangerapi_device WHERE eventmanagernew.eventmangerapi_device.userId_id = "
        + str(userId))

    if tokens:
        for x in tokens:
            if x.push_token:
                result.append(x.push_token)

    if result:
        massenger.sendPush(title, msg, result, data)
