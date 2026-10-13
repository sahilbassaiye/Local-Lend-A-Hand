from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.utils import timezone
from .validators import darpan_validator

class UserRole(models.TextChoices):
    VOLUNTEER = 'VOLUNTEER', 'Volunteer'
    NGO = 'NGO', 'Non-Governmental Organization'
    ADMIN = 'ADMIN', 'Platform Administrator'

class User(AbstractUser):
    firebase_uid = models.CharField(max_length=128, unique=True, db_index=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VOLUNTEER)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image_url = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_volunteer(self):
        return self.role == UserRole.VOLUNTEER

    def is_ngo(self):
        return self.role == UserRole.NGO

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class VolunteerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteer_profile')
    bio = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list, blank=True, help_text="List of skills e.g. ['Teaching', 'Tree Plantation']")
    home_location = models.PointField(srid=4326, null=True, blank=True, help_text="Default coordinates for nearby queries")
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Aggregated Strava Metrics (Updated automatically on drive checkout)
    total_logged_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    current_streak_days = models.PositiveIntegerField(default=0)
    longest_streak_days = models.PositiveIntegerField(default=0)
    last_volunteered_date = models.DateField(null=True, blank=True)

    def update_metrics(self, hours_completed, activity_date=None):
        """
        Updates total hours and streak calculation.
        """
        if activity_date is None:
            activity_date = timezone.now().date()
            
        self.total_logged_hours += hours_completed
        if self.last_volunteered_date:
            delta = (activity_date - self.last_volunteered_date).days
            if delta == 1:
                self.current_streak_days += 1
            elif delta == 0:
                # Same day volunteer work keeps current streak
                pass
            else:
                self.current_streak_days = 1
        else:
            self.current_streak_days = 1

        if self.current_streak_days > self.longest_streak_days:
            self.longest_streak_days = self.current_streak_days

        self.last_volunteered_date = activity_date
        self.save(update_fields=[
            'total_logged_hours', 
            'current_streak_days', 
            'longest_streak_days', 
            'last_volunteered_date'
        ])

    def __str__(self):
        return f"Volunteer: {self.user.get_full_name() or self.user.username} ({self.total_logged_hours} hrs)"


class NGOVerificationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Verification'
    VERIFIED = 'VERIFIED', 'Verified'
    REJECTED = 'REJECTED', 'Rejected'


class NGOProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ngo_profile')
    organization_name = models.CharField(max_length=255)
    darpan_id = models.CharField(
        max_length=50, 
        unique=True, 
        validators=[darpan_validator],
        help_text="NITI Aayog NGO Darpan Unique ID"
    )
    verification_status = models.CharField(
        max_length=20, 
        choices=NGOVerificationStatus.choices, 
        default=NGOVerificationStatus.PENDING
    )
    mission_statement = models.TextField()
    history_and_impact = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    headquarters_location = models.PointField(srid=4326, null=True, blank=True)
    address = models.TextField()
    
    # Aggregated NGO impact metrics
    total_man_hours_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_events_completed = models.PositiveIntegerField(default=0)

    def add_impact_hours(self, hours):
        self.total_man_hours_received += hours
        self.save(update_fields=['total_man_hours_received'])

    def __str__(self):
        return f"{self.organization_name} (Darpan: {self.darpan_id})"


class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    icon_url = models.URLField(blank=True, null=True)
    icon_name = models.CharField(max_length=50, default='fa-award', help_text="FontAwesome or emoji icon")
    threshold_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    category = models.CharField(max_length=50, default='HOURS')

    def __str__(self):
        return f"{self.name} ({self.threshold_hours} hrs)"


class VolunteerBadge(models.Model):
    volunteer = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('volunteer', 'badge')

    def __str__(self):
        return f"{self.volunteer.user.username} - {self.badge.name}"
