from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VolunteerProfile, NGOProfile, Badge, VolunteerBadge

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Platform Info', {'fields': ('role', 'firebase_uid', 'phone_number', 'profile_image_url', 'is_verified')}),
    )

@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'total_logged_hours', 'current_streak_days', 'last_volunteered_date')
    search_fields = ('user__username', 'user__email', 'city')

@admin.register(NGOProfile)
class NGOProfileAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'darpan_id', 'verification_status', 'total_man_hours_received', 'total_events_completed')
    list_filter = ('verification_status',)
    search_fields = ('organization_name', 'darpan_id', 'contact_email')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'threshold_hours', 'icon_name')

@admin.register(VolunteerBadge)
class VolunteerBadgeAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'badge', 'awarded_at')
