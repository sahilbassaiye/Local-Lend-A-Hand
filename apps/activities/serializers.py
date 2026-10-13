from rest_framework import serializers
from .models import VolunteerActivity

class VolunteerActivitySerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    ngo_name = serializers.CharField(source='event.ngo.organization_name', read_only=True)
    event_category = serializers.CharField(source='event.category', read_only=True)
    volunteer_name = serializers.CharField(source='volunteer.user.get_full_name', read_only=True)

    class Meta:
        model = VolunteerActivity
        fields = [
            'id', 'volunteer', 'volunteer_name',
            'event', 'event_title', 'ngo_name', 'event_category',
            'check_in_time', 'check_in_distance_meters', 'is_check_in_verified',
            'check_out_time', 'check_out_distance_meters', 'is_check_out_verified',
            'duration_hours', 'status', 'reflection_notes', 'activity_photo_url',
            'card_generated', 'created_at'
        ]

class CheckInInputSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(required=True)
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    bypass_geofence = serializers.BooleanField(required=False, default=False)

class CheckOutInputSerializer(serializers.Serializer):
    activity_id = serializers.IntegerField(required=False, allow_null=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    reflection_notes = serializers.CharField(required=False, allow_blank=True, default='')
    photo_url = serializers.URLField(required=False, allow_blank=True, default='')
    simulated_hours = serializers.FloatField(required=False, allow_null=True)
    bypass_geofence = serializers.BooleanField(required=False, default=False)
