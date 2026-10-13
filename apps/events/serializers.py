from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import Event, EventApplication, EventStatus, ApplicationStatus
from apps.authentication.models import NGOProfile

class EventSerializer(serializers.ModelSerializer):
    ngo_name = serializers.CharField(source='ngo.organization_name', read_only=True)
    ngo_darpan_id = serializers.CharField(source='ngo.darpan_id', read_only=True)
    ngo_id = serializers.IntegerField(source='ngo.id', read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'ngo_id', 'ngo_name', 'ngo_darpan_id',
            'title', 'category', 'description', 'banner_image_url',
            'required_skills', 'headcount_needed', 'headcount_applied', 'headcount_confirmed',
            'start_time', 'end_time', 'lat', 'lng', 'address', 'geofence_radius_meters',
            'status', 'distance_km', 'is_applied', 'created_at'
        ]

    def get_lat(self, obj):
        return obj.location.y if obj.location else None

    def get_lng(self, obj):
        return obj.location.x if obj.location else None

    def get_distance_km(self, obj):
        if hasattr(obj, 'distance') and obj.distance is not None:
            return round(obj.distance.km, 2)
        return None

    def get_is_applied(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            volunteer = getattr(request.user, 'volunteer_profile', None)
            if volunteer:
                return EventApplication.objects.filter(event=obj, volunteer=volunteer).exists()
        return False

class CreateEventSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Event
        fields = [
            'title', 'category', 'description', 'banner_image_url',
            'required_skills', 'headcount_needed',
            'start_time', 'end_time', 'latitude', 'longitude',
            'address', 'geofence_radius_meters'
        ]

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lng = validated_data.pop('longitude')
        point = Point(lng, lat, srid=4326)
        
        ngo = self.context['ngo']
        event = Event.objects.create(
            ngo=ngo,
            location=point,
            status=EventStatus.ACTIVE,
            **validated_data
        )
        return event

class EventApplicationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    ngo_name = serializers.CharField(source='event.ngo.organization_name', read_only=True)
    volunteer_name = serializers.CharField(source='volunteer.user.get_full_name', read_only=True)

    class Meta:
        model = EventApplication
        fields = ['id', 'event', 'event_title', 'ngo_name', 'volunteer', 'volunteer_name', 'status', 'applied_at', 'notes']
