from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from EventMangerAPI import views

urlpatterns = [
    path('login', views.CustomAuthToken.as_view(), name='login'),
    path('register', views.register, name='register'),
    path('registerVendor', views.registerVendor, name='registerVendor'),
    path('updateOrganizer', views.OrganizerAPIView.as_view(), name='updateOrganizer'),
    path('updateVendor', views.VendorAPIView.as_view(), name='updateVendor'),
    path('getSkills', views.getSkills, name='getSkills'),
    path('getTags', views.getSkills, name='getTags'),
    path('checkReview', views.checkReview, name='checkReview'),
    path('getVendors', views.getVendors, name='getVendors'),
    path('events', views.EventAPIView.as_view()),
    path('trainTagsPredictor', views.trainTagsPredictor, name='trainTagsPredictor'),
    path('predictTags', views.predictTags, name='predictTags'),
    path('updatePushToken', views.updatePushToken, name='updatePushToken'),
    path('acceptBidder', views.acceptBidder, name='acceptBidder'),
    path('chat', views.chat, name='chat'),
    path('scraperTrain', views.scraperTrain, name='scraperTrain'),
    path('scrapeTheSite', views.scrapeTheSite, name='scrapeTheSite'),
    path('checkDateAvailability', views.checkDateAvailability, name='checkDateAvailability'),
    path('filterVendors', views.filterVendors, name='filterVendors'),
    path('bidForEvent', views.EventBidAPIView.as_view(), name='bidForEvent'),
    path('bidForEvent/<int:pk>/', views.EventBidAPIView.as_view()),
    path('eventComment', views.EventCommentAPIView.as_view(), name='eventComment'),
    path('eventComment/<int:pk>/', views.EventCommentAPIView.as_view()),
    path('getVendorsByBudgetAndTags', views.get_vendor_count_by_budget, name='getVendorsByBudgetAndTags'),
    path('', views.home, name='home'),
]
