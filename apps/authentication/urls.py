from django.urls import path
from .views import (
    SyncAuthView,
    RegisterVolunteerAPIView,
    RegisterNGOAPIView,
    ValidateDarpanAPIView,
    LoginAPIView,
    LogoutAPIView,
    DemoLoginAPIView,
    VolunteerDashboardAPIView
)

urlpatterns = [
    path('sync/', SyncAuthView.as_view(), name='auth-sync'),
    path('register/volunteer/', RegisterVolunteerAPIView.as_view(), name='register-volunteer'),
    path('register/ngo/', RegisterNGOAPIView.as_view(), name='register-ngo'),
    path('validate-darpan/', ValidateDarpanAPIView.as_view(), name='validate-darpan'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('demo-switch/', DemoLoginAPIView.as_view(), name='demo-switch'),
    path('volunteer/metrics/', VolunteerDashboardAPIView.as_view(), name='volunteer-metrics'),
]
