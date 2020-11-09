from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.datetime_safe import datetime
import EventMangerAPI.FirebasePushManager as massenger
import EventMangerAPI.ReviewAnalizer as ra


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Admin'),
        (2, 'Event Organizer'),
        (3, 'Vendor'),
        (4, 'Customer'),
    )
    userType = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=4)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=100, blank=True, default="")
    minBudget = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    maxBudget = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)


class Device(models.Model):
    userId = models.ForeignKey(User, related_name='devices', on_delete=models.CASCADE)
    push_token = models.TextField(blank=True, default="")
    deviceId = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    isTestDevice = models.BooleanField(default=False)

    def __str__(self):
        return str(self.userId) + " - " + str(self.deviceId) + " - " + str(self.updated)


class Skill(models.Model):
    tagName = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.tagName)


class VendorSkill(models.Model):
    userId = models.ForeignKey(User, related_name='skills', on_delete=models.CASCADE)
    tagId = models.ForeignKey(Skill, related_name='tag', default="", on_delete=models.CASCADE, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Event(models.Model):
    organizer = models.ForeignKey(User, related_name='events', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=False, default="")
    eventDate = models.DateTimeField(blank=False, default=datetime.now)
    venue = models.TextField(blank=False, default="")
    noOfGuests = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    isPushSent = models.BooleanField(default=False)
    acceptedVendor = models.ForeignKey(User, related_name='acceptedEvents', on_delete=models.CASCADE, blank=True,
                                       null=True)
    eventBudget = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title

    @property
    def eventTags(self):
        return self.eventTags_set.all()

    @property
    def eventReviews(self):
        return self.eventReviews_set.all()


class EventTags(models.Model):
    eventId = models.ForeignKey(Event, related_name='eventTags', on_delete=models.CASCADE)
    tagId = models.ForeignKey(Skill, related_name='eventTag', default="", on_delete=models.CASCADE, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class EventComment(models.Model):
    userId = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    eventId = models.ForeignKey(Event, related_name='eventReviews', on_delete=models.CASCADE)
    comment = models.TextField(blank=False, default="")
    sentimentValue = models.IntegerField(default=-1)
    commentedOn = models.DateTimeField(blank=False, default=datetime.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class EventBid(models.Model):
    eventId = models.ForeignKey(Event, related_name='eventBids', on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, related_name='bidders', on_delete=models.CASCADE)
    bidAmount = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    isPushSent = models.BooleanField(default=False)


class ScrapedEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=False, default="")
    eventDate = models.DateTimeField(blank=False, default=datetime.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ScrapedEventTags(models.Model):
    eventId = models.ForeignKey(ScrapedEvent, related_name='scrapedEventTags', on_delete=models.CASCADE)
    tagId = models.ForeignKey(Skill, related_name='scrapedEventTag', default="", on_delete=models.CASCADE, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class UserQuestions(models.Model):
    id = models.CharField('id', max_length=120, primary_key=True)
    text = models.CharField('text', max_length=120)


@receiver(post_save, sender=EventTags)
def postSaveEvent(sender, instance=None, created=False, **kwargs):
    event = Event.objects.get(pk=instance.eventId.id)
    if not event.isPushSent:
        sendMessageToVendorDevices(event.id, "New event found",
                                   "New event found that matches for your skills: " + event.title, {
                                       "eventId": str(event.id)
                                   })
        event.isPushSent = True
        event.save()


def sendMessageToVendorDevices(eventId, title, msg, data=None):
    result = []
    tokens = Device.objects.raw(
        "SELECT * FROM eventmanagernew.eventmangerapi_device WHERE eventmanagernew.eventmangerapi_device.userId_id IN("
        "SELECT distinct userId_id FROM eventmanagernew.eventmangerapi_vendorskill WHERE "
        "eventmanagernew.eventmangerapi_vendorskill.tagId_id IN (SELECT tagId_id FROM "
        "eventmanagernew.eventmangerapi_eventtags WHERE eventId_id = " + str(eventId) + "))")

    if tokens:
        for x in tokens:
            if x.push_token:
                result.append(x.push_token)

    if result:
        massenger.sendPush(title, msg, result, data)


@receiver(post_save, sender=EventComment)
def postSaveComment(sender, instance=None, created=False, **kwargs):
    percent = float(ra.sample_predict(instance.comment, pad=True)) * 100
    prediction = int((percent + 5) / 10)
    if instance.sentimentValue != prediction:
        instance.sentimentValue = prediction
        instance.save()


@receiver(post_save, sender=EventBid)
def postSaveEventBid(sender, instance=None, created=False, **kwargs):
    if not instance.isPushSent:
        event = Event.objects.get(pk=instance.eventId.id)
        if event:
            sendMessageToOrganizerDevices(event.id, "New bid found",
                                          "New bid found for the event: " + event.title, {
                                              "eventId": str(event.id),
                                              "bidId": str(instance.id)
                                          })
            instance.isPushSent = True
            instance.save()


def sendMessageToOrganizerDevices(bidderId, title, msg, data=None):
    result = []
    tokens = Device.objects.raw(
        "SELECT * FROM eventmanagernew.eventmangerapi_device WHERE eventmanagernew.eventmangerapi_device.userId_id = "
        + str(bidderId))

    if tokens:
        for x in tokens:
            if x.push_token:
                result.append(x.push_token)

    if result:
        massenger.sendPush(title, msg, result, data)
