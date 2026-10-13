from django.urls import path
from .views import (
    FeedListCreateAPIView,
    ToggleLikeAPIView,
    AddCommentAPIView
)

urlpatterns = [
    path('', FeedListCreateAPIView.as_view(), name='feed-list-create'),
    path('posts/<int:post_id>/like/', ToggleLikeAPIView.as_view(), name='post-like'),
    path('posts/<int:post_id>/comment/', AddCommentAPIView.as_view(), name='post-comment'),
]
