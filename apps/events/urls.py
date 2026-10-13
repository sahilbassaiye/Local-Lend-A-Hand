from django.urls import path
from .views import (
    NearbyEventsAPIView,
    ApplyEventAPIView,
    CreateEventAPIView,
    EventDetailAPIView,
    MyAppliedEventsAPIView
)

urlpatterns = [
    path('nearby/', NearbyEventsAPIView.as_view(), name='events-nearby'),
    path('create/', CreateEventAPIView.as_view(), name='events-create'),
    path('my-applied/', MyAppliedEventsAPIView.as_view(), name='events-my-applied'),
    path('<int:event_id>/', EventDetailAPIView.as_view(), name='event-detail'),
    path('<int:event_id>/apply/', ApplyEventAPIView.as_view(), name='event-apply'),
]
