from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import VolunteerActivity, ActivityStatus
from .serializers import VolunteerActivitySerializer, CheckInInputSerializer, CheckOutInputSerializer
from .services import check_in_volunteer, check_out_volunteer

class CheckInAPIView(APIView):
    """
    Strava Check-In:
    POST /api/strava/check-in/
    Requires: event_id, latitude, longitude
    """
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'You must be logged in to check in.'}, status=status.HTTP_401_UNAUTHORIZED)

        volunteer = getattr(request.user, 'volunteer_profile', None)
        if not volunteer:
            return Response({'error': 'Only volunteer accounts can check in to drives.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CheckInInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            activity = check_in_volunteer(
                volunteer=volunteer,
                event_id=data['event_id'],
                lat=data['latitude'],
                lng=data['longitude'],
                bypass_geofence=data.get('bypass_geofence', False)
            )
            return Response({
                'success': True,
                'message': f"Checked in successfully to '{activity.event.title}'! Your volunteering session has started.",
                'activity': VolunteerActivitySerializer(activity).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CheckOutAPIView(APIView):
    """
    Strava Check-Out:
    POST /api/strava/check-out/
    Finalizes drive session, updates hours/streaks/badges, and generates Strava-style Shareable Activity Card.
    """
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'You must be logged in to check out.'}, status=status.HTTP_401_UNAUTHORIZED)

        volunteer = getattr(request.user, 'volunteer_profile', None)
        if not volunteer:
            return Response({'error': 'Only volunteer accounts can check out.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CheckOutInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            result = check_out_volunteer(
                volunteer=volunteer,
                activity_id=data.get('activity_id'),
                lat=data.get('latitude'),
                lng=data.get('longitude'),
                reflection_notes=data.get('reflection_notes', ''),
                photo_url=data.get('photo_url', ''),
                simulated_hours=data.get('simulated_hours'),
                bypass_geofence=data.get('bypass_geofence', False)
            )

            return Response({
                'success': True,
                'message': f"Great job! You logged {result['duration_hours']} volunteer hours.",
                'activity': VolunteerActivitySerializer(result['activity']).data,
                'duration_hours': result['duration_hours'],
                'new_total_hours': result['new_total_hours'],
                'current_streak_days': result['current_streak_days'],
                'newly_awarded_badges': result['newly_awarded_badges'],
                'activity_card': result['activity_metadata']
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ActiveSessionAPIView(APIView):
    """
    Returns current active in-progress check-in session for the volunteer.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'has_active': False})

        volunteer = getattr(request.user, 'volunteer_profile', None)
        if not volunteer:
            return Response({'has_active': False})

        active = VolunteerActivity.objects.filter(
            volunteer=volunteer,
            status=ActivityStatus.CHECKED_IN
        ).select_related('event', 'event__ngo').first()

        if active:
            return Response({
                'has_active': True,
                'activity': VolunteerActivitySerializer(active).data
            })
        return Response({'has_active': False})

class VolunteerHistoryAPIView(APIView):
    """
    Returns past completed activities.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        volunteer = getattr(request.user, 'volunteer_profile', None)
        if not volunteer:
            return Response({'error': 'Not a volunteer profile.'}, status=status.HTTP_403_FORBIDDEN)

        activities = VolunteerActivity.objects.filter(volunteer=volunteer).order_by('-created_at')
        serializer = VolunteerActivitySerializer(activities, many=True)
        return Response(serializer.data)
