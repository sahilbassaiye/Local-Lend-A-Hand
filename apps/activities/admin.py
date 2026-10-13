from django.contrib import admin
from .models import VolunteerActivity

@admin.register(VolunteerActivity)
class VolunteerActivityAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'event', 'status', 'duration_hours', 'check_in_time', 'check_out_time', 'card_generated')
    list_filter = ('status', 'card_generated')
    search_fields = ('volunteer__user__username', 'event__title')
