from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import login, logout, authenticate
from .models import User, UserRole, VolunteerProfile, NGOProfile, Badge, VolunteerBadge
from .serializers import (
    UserSerializer, 
    VolunteerProfileSerializer, 
    NGOProfileSerializer,
    VolunteerRegistrationSerializer, 
    NGORegistrationSerializer
)
from .validators import validate_ngo_darpan_id
from .firebase_auth import verify_firebase_token

class SyncAuthView(APIView):
    """
    Syncs Firebase ID token with Django user account and establishes a web session.
    """
    def post(self, request):
        auth_header = request.data.get('id_token') or request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            auth_header = auth_header.split('Bearer ')[1].strip()

        if not auth_header:
            if request.user.is_authenticated:
                return Response({
                    'authenticated': True,
                    'user': UserSerializer(request.user).data
                })
            return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token_data = verify_firebase_token(auth_header)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        uid = token_data.get('uid')
        email = token_data.get('email')

        user = User.objects.filter(firebase_uid=uid).first()
        if not user and email:
            user = User.objects.filter(email=email).first()
            if user:
                user.firebase_uid = uid
                user.save(update_fields=['firebase_uid'])

        if user:
            login(request, user)
            return Response({
                'authenticated': True,
                'user': UserSerializer(user).data
            })
        else:
            return Response({
                'authenticated': False,
                'needs_onboarding': True,
                'firebase_data': token_data
            })

class ValidateDarpanAPIView(APIView):
    """
    Real-time validation API for NGO Darpan IDs.
    """
    def post(self, request):
        darpan_id = request.data.get('darpan_id', '')
        result = validate_ngo_darpan_id(darpan_id)
        return Response(result, status=status.HTTP_200_OK if result['valid'] else status.HTTP_400_BAD_REQUEST)

class RegisterVolunteerAPIView(APIView):
    """
    Registers a new volunteer account.
    """
    def post(self, request):
        serializer = VolunteerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return Response({
                'success': True,
                'message': 'Volunteer profile registered successfully!',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class RegisterNGOAPIView(APIView):
    """
    Registers a new NGO account with mandatory Darpan ID verification.
    """
    def post(self, request):
        serializer = NGORegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return Response({
                'success': True,
                'message': 'NGO profile registered and Darpan ID verified successfully!',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    """
    Standard username/email and password login.
    """
    def post(self, request):
        email_or_user = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        user = None
        if '@' in email_or_user:
            candidate = User.objects.filter(email=email_or_user).first()
            if candidate and candidate.check_password(password):
                user = candidate
        else:
            user = authenticate(request, username=email_or_user, password=password)

        if user:
            login(request, user)
            return Response({
                'success': True,
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid email/username or password.'}, status=status.HTTP_400_BAD_REQUEST)

class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({'success': True, 'message': 'Logged out successfully.'})

class DemoLoginAPIView(APIView):
    """
    Enables quick switching for reviewers / testers between demo Volunteer and demo NGO personas.
    """
    def post(self, request):
        role_target = request.data.get('role', 'VOLUNTEER').upper()
        if role_target == 'VOLUNTEER':
            user = User.objects.filter(role=UserRole.VOLUNTEER).first()
        else:
            user = User.objects.filter(role=UserRole.NGO).first()

        if user:
            login(request, user)
            return Response({
                'success': True,
                'switched_to': role_target,
                'user': UserSerializer(user).data
            })
        return Response({'error': f'No demo user found for role {role_target}. Seed sample data first.'}, status=status.HTTP_404_NOT_FOUND)

class VolunteerDashboardAPIView(APIView):
    """
    Profile Tab data: total logged volunteer hours, current streak, badges.
    """
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        profile = getattr(request.user, 'volunteer_profile', None)
        if not profile:
            return Response({'error': 'Volunteer profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        all_badges = Badge.objects.all()
        earned_badge_ids = profile.earned_badges.values_list('badge_id', flat=True)

        badges_data = []
        for badge in all_badges:
            badges_data.append({
                'id': badge.id,
                'name': badge.name,
                'slug': badge.slug,
                'description': badge.description,
                'threshold_hours': float(badge.threshold_hours),
                'icon_name': badge.icon_name,
                'earned': badge.id in earned_badge_ids,
            })

        return Response({
            'volunteer': {
                'id': profile.id,
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'bio': profile.bio,
                'city': profile.city,
                'skills': profile.skills,
                'total_logged_hours': float(profile.total_logged_hours),
                'current_streak_days': profile.current_streak_days,
                'longest_streak_days': profile.longest_streak_days,
                'last_volunteered_date': profile.last_volunteered_date,
            },
            'badges': badges_data
        })
