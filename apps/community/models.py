from django.db import models
from apps.authentication.models import User
from apps.activities.models import VolunteerActivity
from apps.events.models import Event

class PostType(models.TextChoices):
    USER_POST = 'USER_POST', 'Volunteer Reflection / Story'
    ACTIVITY_CARD = 'ACTIVITY_CARD', 'Automated Strava Activity Card'
    NGO_UPDATE = 'NGO_UPDATE', 'NGO Announcement / Call for Help'

class FeedPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_posts')
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.USER_POST)
    
    # Optional references
    activity = models.OneToOneField(
        VolunteerActivity, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='feed_post'
    )
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')

    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)

    # Denormalized social counts
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    # Activity Card snapshot details for Strava-style rendering
    activity_metadata = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Snapshot of duration_hours, event_title, ngo_name, badges_unlocked, location_address"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username} ({self.get_post_type_display()}) at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class PostLike(models.Model):
    post = models.ForeignKey(FeedPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"


class PostComment(models.Model):
    post = models.ForeignKey(FeedPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"
