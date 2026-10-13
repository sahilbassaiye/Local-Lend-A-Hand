from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.utils import timezone
from .models import Event, EventApplication, EventStatus, ApplicationStatus
from .serializers import EventSerializer, CreateEventSerializer, EventApplicationSerializer

class NearbyEventsAPIView(APIView):
    """
    Spatial GeoDjango Proximity Query:
    Queries and returns active upcoming events ordered by distance from the user's coordinates.
    """
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius_km = float(request.query_params.get('radius', 50))
        category = request.query_params.get('category')

        events = Event.objects.filter(status=EventStatus.ACTIVE)
        if category:
            events = events.filter(category=category)

        if lat is not None and lng is not None:
            try:
                user_location = Point(float(lng), float(lat), srid=4326)
                # GeoDjango spatial distance calculation and filter using PostGIS index
                events = (
                    events.filter(location__distance_lte=(user_location, D(km=radius_km)))
                    .annotate(distance=Distance('location', user_location))
                    .order_by('distance')
                )
            except Exception as e:
                events = events.order_by('start_time')
        else:
            events = events.order_by('start_time')

        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response({
            'count': events.count(),
            'radius_km': radius_km,
            'events': serializer.data
        })

class ApplyEventAPIView(APIView):
    """
    One-click Apply button for volunteers.
    """
    def post(self, request, event_id):
        if not request.user.is_authenticated:
            return Response({'error': 'You must log in to apply for an event.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        volunteer = getattr(request.user, 'volunteer_profile', None)
        if not volunteer:
            return Response({'error': 'Only volunteer accounts can apply for drives.'}, status=status.HTTP_403_FORBIDDEN)

        event = Event.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        if event.status != EventStatus.ACTIVE:
            return Response({'error': 'This event is no longer active.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check existing application
        application = EventApplication.objects.filter(event=event, volunteer=volunteer).first()
        if application:
            return Response({
                'already_applied': True,
                'message': 'You have already applied to this drive!',
                'application': EventApplicationSerializer(application).data
            })

        # Create application
        notes = request.data.get('notes', '')
        application = EventApplication.objects.create(
            event=event,
            volunteer=volunteer,
            status=ApplicationStatus.APPROVED,
            notes=notes
        )

        event.headcount_applied += 1
        event.save(update_fields=['headcount_applied'])

        return Response({
            'success': True,
            'message': f"Successfully applied for '{event.title}'! Get ready to lend a hand.",
            'application': EventApplicationSerializer(application).data
        }, status=status.HTTP_201_CREATED)

class CreateEventAPIView(APIView):
    """
    NGO Event Posting Engine:
    Accepts drive creation form with coordinates from Google Maps picker.
    """
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        ngo = getattr(request.user, 'ngo_profile', None)
        if not ngo:
            return Response({'error': 'Only verified NGOs can post events.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateEventSerializer(data=request.data, context={'ngo': ngo})
        if serializer.is_valid():
            event = serializer.save()
            return Response({
                'success': True,
                'message': 'Volunteer drive created and live on the map!',
                'event': EventSerializer(event).data
            }, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class EventDetailAPIView(APIView):
    """
    Detailed information for an event.
    """
    def get(self, request, event_id):
        event = Event.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = EventSerializer(event, context={'request': request})
        return Response(serializer.data)

class MyAppliedEventsAPIView(APIView):
    """
    Events applied to by the logged-in volunteer.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        volunteer = getattr(request.user, 'volunteer_profile', None)
        if not volunteer:
            return Response({'error': 'Not a volunteer profile.'}, status=status.HTTP_403_FORBIDDEN)

        applications = EventApplication.objects.filter(volunteer=volunteer).select_related('event', 'event__ngo')
        serializer = EventApplicationSerializer(applications, many=True)
        return Response(serializer.data)
