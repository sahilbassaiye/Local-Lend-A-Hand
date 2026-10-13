from django.contrib import admin
from .models import Event, EventApplication

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'ngo', 'category', 'start_time', 'headcount_needed', 'headcount_applied', 'status')
    list_filter = ('category', 'status')
    search_fields = ('title', 'description', 'ngo__organization_name')

@admin.register(EventApplication)
class EventApplicationAdmin(admin.ModelAdmin):
    list_display = ('event', 'volunteer', 'status', 'applied_at')
    list_filter = ('status',)
