from django.urls import path
from .views import (
    CheckInAPIView,
    CheckOutAPIView,
    ActiveSessionAPIView,
    VolunteerHistoryAPIView
)

urlpatterns = [
    path('check-in/', CheckInAPIView.as_view(), name='strava-check-in'),
    path('check-out/', CheckOutAPIView.as_view(), name='strava-check-out'),
    path('active/', ActiveSessionAPIView.as_view(), name='strava-active'),
    path('history/', VolunteerHistoryAPIView.as_view(), name='strava-history'),
]
