from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin

from EventMangerAPI.models import User, Skill, VendorSkill, Event, EventTags, EventComment, EventBid, UserQuestions

admin.site.register(User)
admin.site.register(Skill)
admin.site.register(VendorSkill)
admin.site.register(Event)
admin.site.register(EventTags)
admin.site.register(EventComment)
admin.site.register(EventBid)
admin.site.register(UserQuestions)
