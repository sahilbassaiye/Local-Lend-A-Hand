from django.contrib.gis.db import models
from django.utils import timezone
from apps.authentication.models import NGOProfile, VolunteerProfile

class EventStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    ACTIVE = 'ACTIVE', 'Active / Upcoming'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class EventCategory(models.TextChoices):
    ENVIRONMENT = 'ENVIRONMENT', 'Environment & Conservation'
    EDUCATION = 'EDUCATION', 'Education & Literacy'
    HEALTH = 'HEALTH', 'Health & Sanitation'
    ANIMAL_WELFARE = 'ANIMAL_WELFARE', 'Animal Welfare'
    FOOD_HUNGER = 'FOOD_HUNGER', 'Hunger & Food Distribution'
    DISASTER_RELIEF = 'DISASTER_RELIEF', 'Disaster Relief'
    COMMUNITY = 'COMMUNITY', 'Community Development'

class Event(models.Model):
    ngo = models.ForeignKey(NGOProfile, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=EventCategory.choices, default=EventCategory.COMMUNITY)
    description = models.TextField()
    banner_image_url = models.URLField(blank=True, null=True)
    
    # Requirements
    required_skills = models.JSONField(default=list, blank=True, help_text="List of skills e.g. ['Teaching', 'Logistics']")
    headcount_needed = models.PositiveIntegerField(default=5)
    headcount_applied = models.PositiveIntegerField(default=0)
    headcount_confirmed = models.PositiveIntegerField(default=0)

    # Schedule
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    # GeoDjango PostGIS Spatial Fields
    location = models.PointField(srid=4326, help_text="Geographical Point (longitude, latitude) of drive")
    address = models.CharField(max_length=500)
    geofence_radius_meters = models.PositiveIntegerField(
        default=250, 
        help_text="Allowed radius in meters for GPS check-in/out verification"
    )

    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    @property
    def latitude(self):
        return self.location.y if self.location else None

    @property
    def longitude(self):
        return self.location.x if self.location else None

    @property
    def is_in_progress(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status == EventStatus.ACTIVE

    def __str__(self):
        return f"{self.title} ({self.ngo.organization_name})"


class ApplicationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Applied'
    APPROVED = 'APPROVED', 'Approved / Confirmed'
    REJECTED = 'REJECTED', 'Rejected'
    CANCELLED = 'CANCELLED', 'Withdrawn'

class EventApplication(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='applications')
    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name='event_applications')
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.APPROVED)
    applied_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('event', 'volunteer')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.volunteer.user.username} -> {self.event.title} ({self.get_status_display()})"
