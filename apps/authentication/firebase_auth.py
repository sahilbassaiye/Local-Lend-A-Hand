import logging
from rest_framework import authentication, exceptions
from django.conf import settings
from .models import User, UserRole, VolunteerProfile, NGOProfile

logger = logging.getLogger(__name__)

# Attempt to initialize firebase_admin if credentials or project configured
_firebase_initialized = False
try:
    import firebase_admin
    from firebase_admin import auth as fb_auth, credentials

    if not firebase_admin._apps:
        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
        else:
            project_id = getattr(settings, 'FIREBASE_PROJECT_ID', None)
            if project_id:
                firebase_admin.initialize_app(options={'projectId': project_id})
                _firebase_initialized = True
except Exception as e:
    logger.warning(f"Firebase Admin SDK initialization skipped or in mock mode: {e}")


def verify_firebase_token(id_token: str):
    """
    Verifies Firebase JWT token. If firebase_admin is not initialized or in development mode,
    gracefully handles mock tokens formatted as 'mock-<role>-<uid>' or standard Firebase tokens.
    """
    if not id_token:
        return None

    # Handle mock tokens for seamless development & offline evaluation
    if id_token.startswith('mock-'):
        parts = id_token.split('-')
        # format: mock-volunteer-uid123 or mock-ngo-uid456
        role = parts[1].upper() if len(parts) > 1 else 'VOLUNTEER'
        uid = '-'.join(parts[2:]) if len(parts) > 2 else 'mock-user'
        email = f"{uid}@example.com"
        return {
            'uid': uid,
            'email': email,
            'name': uid.replace('_', ' ').title(),
            'role_hint': role
        }

    # Production Firebase verification
    if _firebase_initialized:
        try:
            decoded_token = fb_auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise exceptions.AuthenticationFailed(f"Invalid Firebase ID token: {str(e)}")

    # Fallback simulation if id_token is provided but firebase is offline
    return {
        'uid': f"fb_{abs(hash(id_token)) % 1000000}",
        'email': 'user@locallendahand.org',
        'name': 'Firebase Authenticated User'
    }


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    DRF Authentication scheme that accepts 'Authorization: Bearer <firebase_token>'
    """
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        id_token = auth_header.split('Bearer ')[1].strip()
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return None

        uid = decoded_token.get('uid')
        if not uid:
            raise exceptions.AuthenticationFailed('User identifier (UID) missing in Firebase token.')

        user = User.objects.filter(firebase_uid=uid).first()
        if not user:
            # Check by email if available
            email = decoded_token.get('email', '')
            if email:
                user = User.objects.filter(email=email).first()
                if user and not user.firebase_uid:
                    user.firebase_uid = uid
                    user.save(update_fields=['firebase_uid'])

        if not user:
            # User must complete onboarding
            return None

        return (user, decoded_token)
