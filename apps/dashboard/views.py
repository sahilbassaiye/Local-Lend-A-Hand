from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.authentication.models import User, UserRole, VolunteerProfile, NGOProfile, Badge
from apps.authentication.serializers import NGOProfileSerializer
from apps.events.models import Event, EventApplication, EventStatus
from apps.events.serializers import EventSerializer
from apps.activities.models import VolunteerActivity, ActivityStatus

class NGOImpactAnalyticsAPIView(APIView):
    """
    NGO Analytics & Reach (Impact Dashboard):
    Computes total man-hours donated to their cause, volunteer headcount reach, and drive breakdown.
    """
    def get(self, request, ngo_id=None):
        if ngo_id:
            ngo = NGOProfile.objects.filter(id=ngo_id).first()
        elif request.user.is_authenticated:
            ngo = getattr(request.user, 'ngo_profile', None)
        else:
            ngo = None

        if not ngo:
            return Response({'error': 'NGO Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        events = Event.objects.filter(ngo=ngo)
        total_events = events.count()
        active_events = events.filter(status=EventStatus.ACTIVE).count()
        completed_events = events.filter(status=EventStatus.COMPLETED).count()

        total_man_hours = float(ngo.total_man_hours_received)

        unique_volunteers_count = (
            VolunteerActivity.objects.filter(event__ngo=ngo, status=ActivityStatus.COMPLETED)
            .values('volunteer')
            .distinct()
            .count()
        )

        total_applications = EventApplication.objects.filter(event__ngo=ngo).count()

        events_breakdown = []
        for ev in events.order_by('-start_time')[:10]:
            ev_hours = (
                VolunteerActivity.objects.filter(event=ev, status=ActivityStatus.COMPLETED)
                .aggregate(total=Sum('duration_hours'))['total'] or 0.00
            )
            events_breakdown.append({
                'id': ev.id,
                'title': ev.title,
                'category': ev.category,
                'start_time': ev.start_time.strftime('%Y-%m-%d %H:%M'),
                'address': ev.address,
                'status': ev.status,
                'headcount_needed': ev.headcount_needed,
                'headcount_applied': ev.headcount_applied,
                'total_hours_logged': float(ev_hours),
            })

        return Response({
            'ngo': {
                'id': ngo.id,
                'organization_name': ngo.organization_name,
                'darpan_id': ngo.darpan_id,
                'verification_status': ngo.verification_status,
                'total_man_hours_received': total_man_hours,
            },
            'summary': {
                'total_man_hours_donated': total_man_hours,
                'unique_volunteers_engaged': unique_volunteers_count,
                'total_events_hosted': total_events,
                'active_events': active_events,
                'completed_events': completed_events,
                'total_applications_received': total_applications,
            },
            'events_breakdown': events_breakdown
        })

class NGOLiveTrackingAPIView(APIView):
    """
    Live Event Tracking for NGOs:
    Provides real-time monitor data for currently active drives and on-site checked-in volunteers.
    """
    def get(self, request):
        ngo = None
        if request.user.is_authenticated:
            ngo = getattr(request.user, 'ngo_profile', None)
        if not ngo:
            ngo = NGOProfile.objects.first()

        if not ngo:
            return Response({'has_active': False})

        active_event = Event.objects.filter(ngo=ngo, status=EventStatus.ACTIVE).first()
        if not active_event:
            return Response({'has_active': False})

        # Attendees currently checked in
        live_activities = VolunteerActivity.objects.filter(
            event=active_event,
            status=ActivityStatus.CHECKED_IN
        ).select_related('volunteer', 'volunteer__user')

        attendees = []
        now = timezone.now()
        for act in live_activities:
            elapsed_min = int((now - act.check_in_time).total_seconds() / 60)
            attendees.append({
                'activity_id': act.id,
                'volunteer_name': act.volunteer.user.get_full_name() or act.volunteer.user.username,
                'volunteer_avatar': act.volunteer.user.profile_image_url,
                'check_in_time': act.check_in_time.strftime('%I:%M %p'),
                'elapsed_minutes': elapsed_min,
                'distance_meters': int(act.check_in_distance_meters),
                'verified': act.is_check_in_verified
            })

        # Also get past completed activities for this event
        completed_hours = (
            VolunteerActivity.objects.filter(event=active_event, status=ActivityStatus.COMPLETED)
            .aggregate(total=Sum('duration_hours'))['total'] or 0.00
        )

        return Response({
            'has_active': True,
            'event': {
                'id': active_event.id,
                'title': active_event.title,
                'category': active_event.category,
                'address': active_event.address,
                'latitude': active_event.latitude,
                'longitude': active_event.longitude,
                'geofence_radius_meters': active_event.geofence_radius_meters,
                'headcount_needed': active_event.headcount_needed,
                'headcount_applied': active_event.headcount_applied,
                'start_time': active_event.start_time.strftime('%b %d, %I:%M %p'),
                'end_time': active_event.end_time.strftime('%b %d, %I:%M %p'),
            },
            'live_attendees_count': live_activities.count(),
            'live_attendees': attendees,
            'total_hours_completed': float(completed_hours)
        })

class NGOPublicProfileAPIView(APIView):
    """
    Public-facing info page data about the organization's mission and history.
    """
    def get(self, request, ngo_id):
        ngo = get_object_or_404(NGOProfile, id=ngo_id)
        active_events = Event.objects.filter(ngo=ngo, status=EventStatus.ACTIVE)
        past_events = Event.objects.filter(ngo=ngo, status=EventStatus.COMPLETED)

        return Response({
            'profile': NGOProfileSerializer(ngo).data,
            'active_events': EventSerializer(active_events, many=True).data,
            'past_events': EventSerializer(past_events, many=True).data,
        })


# ==================== HTML TEMPLATE VIEWS ====================

def home_view(request):
    featured_events = Event.objects.filter(status=EventStatus.ACTIVE)[:6]
    total_volunteers = VolunteerProfile.objects.count()
    total_ngos = NGOProfile.objects.count()
    total_hours = VolunteerProfile.objects.aggregate(total=Sum('total_logged_hours'))['total'] or 0.0

    return render(request, 'index.html', {
        'featured_events': featured_events,
        'total_volunteers': total_volunteers,
        'total_ngos': total_ngos,
        'total_hours': total_hours
    })

def volunteer_dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('/auth/login/?role=volunteer')

    volunteer = getattr(request.user, 'volunteer_profile', None)
    if not volunteer:
        # If logged in user is not volunteer, allow switching
        return redirect('/ngo/dashboard/')

    # Active session check
    active_session = VolunteerActivity.objects.filter(
        volunteer=volunteer,
        status=ActivityStatus.CHECKED_IN
    ).select_related('event', 'event__ngo').first()

    # Upcoming applied drives
    applied_events = EventApplication.objects.filter(
        volunteer=volunteer
    ).select_related('event', 'event__ngo')

    # Selected active drive for live tracking map
    tracking_event = None
    if active_session:
        tracking_event = active_session.event
    elif applied_events.exists():
        tracking_event = applied_events.first().event
    else:
        tracking_event = Event.objects.filter(status=EventStatus.ACTIVE).first()

    all_badges = Badge.objects.all()
    earned_badge_ids = set(volunteer.earned_badges.values_list('badge_id', flat=True))

    return render(request, 'volunteer/dashboard.html', {
        'volunteer': volunteer,
        'active_session': active_session,
        'tracking_event': tracking_event,
        'applied_events': applied_events,
        'all_badges': all_badges,
        'earned_badge_ids': earned_badge_ids
    })

def ngo_dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('/auth/login/?role=ngo')

    ngo = getattr(request.user, 'ngo_profile', None)
    if not ngo:
        return redirect('/volunteer/dashboard/')

    active_events = Event.objects.filter(ngo=ngo, status=EventStatus.ACTIVE)
    active_event = active_events.first()

    # Checked-in volunteers for live tracking
    live_activities = []
    if active_event:
        live_activities = VolunteerActivity.objects.filter(
            event=active_event,
            status=ActivityStatus.CHECKED_IN
        ).select_related('volunteer', 'volunteer__user')

    return render(request, 'ngo/dashboard.html', {
        'ngo': ngo,
        'active_events': active_events,
        'active_event': active_event,
        'live_activities': live_activities
    })

def ngo_public_profile_view(request, ngo_id):
    ngo = get_object_or_404(NGOProfile, id=ngo_id)
    active_events = Event.objects.filter(ngo=ngo, status=EventStatus.ACTIVE)
    return render(request, 'ngo/profile.html', {
        'ngo': ngo,
        'active_events': active_events
    })

def community_feed_view(request):
    # After signing in they can access community
    # If not authenticated, template shows the community sign-in gate
    return render(request, 'community/feed.html', {
        'is_authenticated': request.user.is_authenticated
    })

def login_view(request):
    role_hint = request.GET.get('role', 'volunteer')
    return render(request, 'auth/login.html', {'role_hint': role_hint})

def register_volunteer_view(request):
    return render(request, 'auth/register_volunteer.html')

def register_ngo_view(request):
    return render(request, 'auth/register_ngo.html')
