from django.urls import path
from .views import (
    home_view,
    volunteer_dashboard_view,
    ngo_dashboard_view,
    ngo_public_profile_view,
    community_feed_view,
    login_view,
    register_volunteer_view,
    register_ngo_view,
    NGOImpactAnalyticsAPIView,
    NGOPublicProfileAPIView,
    NGOLiveTrackingAPIView
)

urlpatterns = [
    # HTML views
    path('', home_view, name='home'),
    path('volunteer/dashboard/', volunteer_dashboard_view, name='volunteer-dashboard-page'),
    path('ngo/dashboard/', ngo_dashboard_view, name='ngo-dashboard-page'),
    path('ngo/profile/<int:ngo_id>/', ngo_public_profile_view, name='ngo-public-profile-page'),
    path('community/', community_feed_view, name='community-feed-page'),
    path('auth/login/', login_view, name='login-page'),
    path('auth/register/volunteer/', register_volunteer_view, name='register-volunteer-page'),
    path('auth/register/ngo/', register_ngo_view, name='register-ngo-page'),

    # API endpoints
    path('api/ngo/impact-analytics/', NGOImpactAnalyticsAPIView.as_view(), name='ngo-analytics-me'),
    path('api/ngo/impact-analytics/<int:ngo_id>/', NGOImpactAnalyticsAPIView.as_view(), name='ngo-analytics'),
    path('api/ngo/profile/<int:ngo_id>/', NGOPublicProfileAPIView.as_view(), name='ngo-profile-api'),
    path('api/ngo/live-tracking/', NGOLiveTrackingAPIView.as_view(), name='ngo-live-tracking'),
]
