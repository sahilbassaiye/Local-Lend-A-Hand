from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import User, UserRole, VolunteerProfile, NGOProfile, Badge, VolunteerBadge, NGOVerificationStatus
from .validators import darpan_validator, validate_ngo_darpan_id

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'slug', 'description', 'icon_url', 'icon_name', 'threshold_hours', 'category']

class VolunteerBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    class Meta:
        model = VolunteerBadge
        fields = ['id', 'badge', 'awarded_at']

class VolunteerProfileSerializer(serializers.ModelSerializer):
    earned_badges = VolunteerBadgeSerializer(many=True, read_only=True)
    home_lat = serializers.SerializerMethodField()
    home_lng = serializers.SerializerMethodField()

    class Meta:
        model = VolunteerProfile
        fields = [
            'id', 'bio', 'skills', 'city',
            'home_lat', 'home_lng',
            'total_logged_hours', 'current_streak_days', 'longest_streak_days',
            'last_volunteered_date', 'earned_badges'
        ]

    def get_home_lat(self, obj):
        return obj.home_location.y if obj.home_location else None

    def get_home_lng(self, obj):
        return obj.home_location.x if obj.home_location else None

class NGOProfileSerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    class Meta:
        model = NGOProfile
        fields = [
            'id', 'organization_name', 'darpan_id', 'verification_status',
            'mission_statement', 'history_and_impact', 'website',
            'contact_email', 'contact_phone', 'address',
            'lat', 'lng',
            'total_man_hours_received', 'total_events_completed'
        ]

    def get_lat(self, obj):
        return obj.headquarters_location.y if obj.headquarters_location else None

    def get_lng(self, obj):
        return obj.headquarters_location.x if obj.headquarters_location else None

class UserSerializer(serializers.ModelSerializer):
    volunteer_profile = VolunteerProfileSerializer(read_only=True)
    ngo_profile = NGOProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone_number', 'profile_image_url', 'is_verified',
            'volunteer_profile', 'ngo_profile'
        ]

class VolunteerRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    firebase_uid = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    city = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    def create(self, validated_data):
        email = validated_data['email']
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        firebase_uid = validated_data.get('firebase_uid') or f"local_{username}"
        user = User.objects.create(
            username=username,
            email=email,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=UserRole.VOLUNTEER,
            firebase_uid=firebase_uid,
            is_verified=True
        )
        if validated_data.get('password'):
            user.set_password(validated_data['password'])
            user.save()

        # Spatial home location
        lat = validated_data.get('latitude')
        lng = validated_data.get('longitude')
        home_location = Point(lng, lat, srid=4326) if (lat is not None and lng is not None) else None

        VolunteerProfile.objects.create(
            user=user,
            bio=validated_data.get('bio', ''),
            skills=validated_data.get('skills', []),
            city=validated_data.get('city', ''),
            home_location=home_location
        )
        return user

class NGORegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    organization_name = serializers.CharField(required=True)
    darpan_id = serializers.CharField(required=True, validators=[darpan_validator])
    firebase_uid = serializers.CharField(required=False, allow_blank=True)
    mission_statement = serializers.CharField(required=True)
    history_and_impact = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    def validate_darpan_id(self, value):
        verification = validate_ngo_darpan_id(value)
        if not verification['valid']:
            raise serializers.ValidationError(verification['message'])
        return value.strip().upper()

    def create(self, validated_data):
        email = validated_data['email']
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        firebase_uid = validated_data.get('firebase_uid') or f"local_{username}"
        user = User.objects.create(
            username=username,
            email=email,
            first_name=validated_data.get('organization_name', ''),
            role=UserRole.NGO,
            firebase_uid=firebase_uid,
            is_verified=True
        )
        if validated_data.get('password'):
            user.set_password(validated_data['password'])
            user.save()

        lat = validated_data.get('latitude')
        lng = validated_data.get('longitude')
        hq_location = Point(lng, lat, srid=4326) if (lat is not None and lng is not None) else None

        NGOProfile.objects.create(
            user=user,
            organization_name=validated_data['organization_name'],
            darpan_id=validated_data['darpan_id'],
            verification_status=NGOVerificationStatus.VERIFIED,
            mission_statement=validated_data['mission_statement'],
            history_and_impact=validated_data.get('history_and_impact', ''),
            website=validated_data.get('website', ''),
            contact_email=email,
            contact_phone=validated_data['contact_phone'],
            address=validated_data['address'],
            headquarters_location=hq_location
        )
        return user
