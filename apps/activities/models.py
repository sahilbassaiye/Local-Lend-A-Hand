from django.contrib.gis.db import models
from django.utils import timezone
from apps.authentication.models import VolunteerProfile
from apps.events.models import Event

class ActivityStatus(models.TextChoices):
    CHECKED_IN = 'CHECKED_IN', 'Checked In (Active)'
    COMPLETED = 'COMPLETED', 'Completed & Logged'
    AUTO_EXPIRED = 'AUTO_EXPIRED', 'Expired / Unfinished'
    CANCELLED = 'CANCELLED', 'Cancelled'

class VolunteerActivity(models.Model):
    """
    Core engine for 'Strava for Volunteering'.
    Tracks real-time GPS check-in and check-out to verify on-site hours.
    """
    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name='activities')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='logged_activities')
    
    # Check-In
    check_in_time = models.DateTimeField(default=timezone.now)
    check_in_location = models.PointField(srid=4326)
    check_in_distance_meters = models.FloatField(default=0.0, help_text="GPS distance from drive coordinates at check-in")
    is_check_in_verified = models.BooleanField(default=True)

    # Check-Out
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_location = models.PointField(srid=4326, null=True, blank=True)
    check_out_distance_meters = models.FloatField(null=True, blank=True)
    is_check_out_verified = models.BooleanField(default=False)

    # Calculated metrics
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=ActivityStatus.choices, default=ActivityStatus.CHECKED_IN)
    reflection_notes = models.TextField(blank=True, null=True)
    activity_photo_url = models.URLField(blank=True, null=True)

    # Automated Activity Card Flag
    card_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def check_in_lat(self):
        return self.check_in_location.y if self.check_in_location else None

    @property
    def check_in_lng(self):
        return self.check_in_location.x if self.check_in_location else None

    @property
    def check_out_lat(self):
        return self.check_out_location.y if self.check_out_location else None

    @property
    def check_out_lng(self):
        return self.check_out_location.x if self.check_out_location else None

    def __str__(self):
        return f"{self.volunteer.user.username} @ {self.event.title} ({self.duration_hours}h - {self.get_status_display()})"
