from django.db import connection
from rest_framework import serializers

from EventMangerAPI.models import User, Skill, VendorSkill, Event, EventTags, EventComment,UserQuestions ,EventBid, ScrapedEvent, \
    ScrapedEventTags


class VendorSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorSkill
        fields = ['tagId', 'tagName']

    tagName = serializers.SerializerMethodField('get_tagName')

    def get_tagName(self, obj):
        return obj.tagId.tagName


class UserSerializer(serializers.ModelSerializer):
    skills = VendorSkillSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "userType",
            "password",
            "location",
            "skills",
            "rateCategory",
            "minBudget",
            "maxBudget"
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id': {'read_only': True},
            'skills': {'read_only': True},
            'rateCategory': {'read_only': True}
        }

    rateCategory = serializers.SerializerMethodField('get_rateCategory')

    def get_rateCategory(self, obj):
        sql = "select CASE WHEN table1.rating >= 8 then 'Platinum' WHEN table1.rating >= 5 then 'Gold' ELSE " \
              "'Silver' END as rateCategory from (SELECT *, IFNULL((SELECT SUM(sentimentValue) FROM " \
              "eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = eventmanagernew.eventmangerapi_user.id) / (SELECT " \
              "count(*) FROM eventmanagernew.eventmangerapi_eventcomment WHERE userId_id = " \
              + str(obj.id) + "), 0)as rating FROM eventmanagernew.eventmangerapi_user) table1  WHERE table1.id = " + str(
            obj.id)

        cursor = connection.cursor()
        cursor.execute(sql)

        return cursor.fetchone()[0]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        updateValues = self.Meta.model(**validated_data)
        instance.username = instance.username
        instance.first_name = updateValues.first_name
        instance.last_name = updateValues.last_name
        instance.email = updateValues.email
        instance.userType = updateValues.userType
        instance.minBudget = updateValues.minBudget
        instance.maxBudget = updateValues.maxBudget

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'tagName', ]
        depth = 1


class BotQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuestions
        fields = ['id', 'text', ]
        depth = 1


class VendorSerializer(serializers.ModelSerializer):
    skills = VendorSkillSerializer(many=True)
    rateCategory = serializers.CharField(default="")

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "userType",
            "skills",
            "rateCategory",
            "location",
            "minBudget",
            "maxBudget"
        ]


class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "userType",
            "location"
        ]


class CommenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "userType",
        ]


class BidderSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "userType"
        ]


class EventTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTags
        fields = ['tagId', 'tagName']

    tagName = serializers.SerializerMethodField('get_tagName')

    def get_tagName(self, obj):
        return obj.tagId.tagName


class EventBidSerializer(serializers.ModelSerializer):
    bidder = BidderSerializer()

    class Meta:
        model = EventBid
        fields = ['id', 'eventId', 'bidder', 'bidAmount']


class EventCommentSerializer(serializers.ModelSerializer):
    commentedBy = CommenterSerializer(source='userId', read_only=True)

    class Meta:
        model = EventComment
        fields = ['id', 'comment', 'sentimentValue', 'commentedOn', 'commentedBy', 'eventId']


class EventSerializer(serializers.ModelSerializer):
    organizer = OrganizerSerializer()
    acceptedVendor = OrganizerSerializer()
    eventTags = EventTagsSerializer(many=True)
    eventReviews = EventCommentSerializer(many=True, read_only=True)
    eventBids = EventBidSerializer(many=True)

    class Meta:
        model = Event
        fields = ["id", "title", "description", "eventDate", "venue",
                  "noOfGuests", "eventTags", "eventReviews", "organizer", "acceptedVendor", "eventBids", "eventBudget"]


class SaveEventSerializer(serializers.ModelSerializer):
    eventTags = EventTagsSerializer(many=True)

    class Meta:
        model = Event
        fields = ["id", "title", "description", "eventDate", "venue",
                  "noOfGuests", "eventTags", "organizer", "eventBudget"]
        read_only_fields = ('eventReviews',)

    def create(self, validated_data):
        eventTags = validated_data.pop('eventTags')
        event = Event.objects.create(**validated_data)

        for tag in eventTags:
            EventTags.objects.create(**tag, eventId=event)

        return event

    def update(self, instance, validated_data):
        eventTags = validated_data.pop('eventTags')
        instance.title = validated_data.pop('title')
        instance.description = validated_data.pop('description')
        instance.venue = validated_data.pop('venue')
        instance.eventDate = validated_data.pop('eventDate')
        instance.noOfGuests = validated_data.pop('noOfGuests')
        instance.organizer = validated_data.pop('organizer')
        instance.eventBudget = validated_data.pop('eventBudget')

        EventTags.objects.filter(eventId=instance.id).delete()
        instance.save()

        for tag in eventTags:
            EventTags.objects.create(**tag, eventId=instance)

        return instance


class SaveVendorSerializer(serializers.ModelSerializer):
    skills = VendorSkillSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "userType",
            "skills",
            "password",
            "location",
            "minBudget",
            "maxBudget"
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id': {'read_only': True}
        }

    def create(self, validated_data):
        skills = validated_data.pop('skills')
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)

        if password is not None:
            instance.set_password(password)
        instance.save()

        for skill in skills:
            VendorSkill.objects.create(**skill, userId=instance)

        return instance

    def update(self, instance, validated_data):
        skills = validated_data.pop('skills')
        updateValues = self.Meta.model(**validated_data)
        instance.username = updateValues.username
        instance.first_name = updateValues.first_name
        instance.last_name = updateValues.last_name
        instance.email = updateValues.email
        instance.userType = updateValues.userType
        instance.location = updateValues.location
        instance.minBudget = updateValues.minBudget
        instance.maxBudget = updateValues.maxBudget

        VendorSkill.objects.filter(userId=instance.id).delete()

        for skill in skills:
            VendorSkill.objects.create(**skill, userId=instance)

        instance.save()

        return instance


class ScrapedEventTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTags
        fields = ['tagId', 'tagName']

    tagName = serializers.SerializerMethodField('get_tagName')

    def get_tagName(self, obj):
        return obj.tagId.tagName


class SaveScrapedEventSerializer(serializers.ModelSerializer):
    scrapedEventTags = ScrapedEventTagsSerializer(many=True)

    class Meta:
        model = ScrapedEvent
        fields = ["id", "title", "description", "eventDate", "scrapedEventTags"]

    def create(self, validated_data):
        scrapedEventTags = validated_data.pop('scrapedEventTags')
        event = ScrapedEvent.objects.create(**validated_data)

        for tag in scrapedEventTags:
            ScrapedEventTags.objects.create(**tag, eventId=event)

        return event


class EventBidSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventBid
        fields = ["id", "eventId", "bidder", "bidAmount", "isPushSent", ]

        extra_kwargs = {
            'isPushSent': {'write_only': True},
            'id': {'read_only': True}
        }


class SaveEventCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventComment
        fields = ["id", "eventId", "userId", "comment", "sentimentValue", "commentedOn"]

        extra_kwargs = {
            'id': {'read_only': True},
            'sentimentValue': {'read_only': True},
            'commentedOn': {'read_only': True}
        }