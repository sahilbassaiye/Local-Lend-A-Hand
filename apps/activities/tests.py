from django.test import TestCase
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.authentication.models import User, UserRole, VolunteerProfile, NGOProfile, Badge, VolunteerBadge
from apps.authentication.validators import validate_ngo_darpan_id
from apps.events.models import Event, EventCategory, EventStatus, EventApplication
from apps.activities.models import VolunteerActivity, ActivityStatus
from apps.activities.services import check_in_volunteer, check_out_volunteer, haversine_distance_meters
from apps.community.models import FeedPost, PostType

class DarpanIdValidationTest(TestCase):
    def test_valid_darpan_ids(self):
        res1 = validate_ngo_darpan_id("DL/2019/0182736")
        self.assertTrue(res1['valid'])
        self.assertEqual(res1['state_code'], 'DL')

        res2 = validate_ngo_darpan_id("MH/2021/1234567")
        self.assertTrue(res2['valid'])
        self.assertEqual(res2['state_code'], 'MH')

    def test_invalid_format_darpan_ids(self):
        # Missing state code or incorrect digits
        self.assertFalse(validate_ngo_darpan_id("12345")['valid'])
        self.assertFalse(validate_ngo_darpan_id("DELHI/2019/1234567")['valid'])
        self.assertFalse(validate_ngo_darpan_id("DL-2019-1234567")['valid'])

    def test_blacklisted_mock_darpan_id(self):
        res = validate_ngo_darpan_id("DL/2020/0000000")
        self.assertFalse(res['valid'])
        self.assertIn("flagged", res['message'])


class StravaForVolunteeringEngineTest(TestCase):
    def setUp(self):
        # Create Badges
        self.b1 = Badge.objects.create(
            name="First Step",
            slug="first-step",
            description="First drive",
            threshold_hours=Decimal('1.00')
        )
        self.b2 = Badge.objects.create(
            name="Impact Maker",
            slug="impact-maker",
            description="10 hours",
            threshold_hours=Decimal('10.00')
        )

        # Create NGO
        self.ngo_user = User.objects.create_user(
            username='ngo_test',
            email='ngo@test.org',
            role=UserRole.NGO,
            password='password123'
        )
        self.ngo_profile = NGOProfile.objects.create(
            user=self.ngo_user,
            organization_name='Test NGO Trust',
            darpan_id='DL/2020/0123456',
            mission_statement='Test mission',
            contact_email='ngo@test.org',
            contact_phone='1234567890',
            address='Test Delhi HQ'
        )

        # Create Volunteer
        self.vol_user = User.objects.create_user(
            username='vol_test',
            email='vol@test.org',
            role=UserRole.VOLUNTEER,
            first_name='Rahul',
            password='password123'
        )
        self.vol_profile = VolunteerProfile.objects.create(
            user=self.vol_user,
            city='Delhi',
            total_logged_hours=Decimal('8.00'),
            current_streak_days=1
        )

        # Create Event in Delhi (28.6500, 77.2410) with 250m geofence
        self.event = Event.objects.create(
            ngo=self.ngo_profile,
            title='Park Cleanup Drive',
            category=EventCategory.ENVIRONMENT,
            description='Test park cleanup',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=4),
            location=Point(77.2410, 28.6500, srid=4326),
            address='Yamuna Park',
            geofence_radius_meters=250,
            status=EventStatus.ACTIVE
        )

    def test_haversine_distance(self):
        # Exact same point should be 0
        d = haversine_distance_meters(28.6500, 77.2410, 28.6500, 77.2410)
        self.assertEqual(d, 0.0)

        # Point ~100m away
        d_close = haversine_distance_meters(28.6500, 77.2410, 28.6508, 77.2410)
        self.assertLess(d_close, 150)

    def test_geofenced_check_in_within_radius(self):
        # Within 50 meters
        activity = check_in_volunteer(
            volunteer=self.vol_profile,
            event_id=self.event.id,
            lat=28.6502,
            lng=77.2411
        )
        self.assertEqual(activity.status, ActivityStatus.CHECKED_IN)
        self.assertTrue(activity.is_check_in_verified)

    def test_geofenced_check_in_outside_radius(self):
        # 10 km away in Gurgaon (28.4595, 77.0266)
        with self.assertRaises(ValueError) as ctx:
            check_in_volunteer(
                volunteer=self.vol_profile,
                event_id=self.event.id,
                lat=28.4595,
                lng=77.0266,
                bypass_geofence=False
            )
        self.assertIn("Geofence check failed", str(ctx.exception))

    def test_checkout_and_activity_card_generation(self):
        # Check in volunteer
        check_in_volunteer(
            volunteer=self.vol_profile,
            event_id=self.event.id,
            lat=28.6500,
            lng=77.2410
        )

        # Check out volunteer with 3 hours simulated
        result = check_out_volunteer(
            volunteer=self.vol_profile,
            lat=28.6500,
            lng=77.2410,
            reflection_notes='Great cleanup work!',
            simulated_hours=3.00
        )

        self.assertEqual(result['duration_hours'], 3.0)
        # 8 + 3 = 11 hours -> Should trigger 'Impact Maker' badge (10 hr threshold)
        self.vol_profile.refresh_from_db()
        self.assertEqual(float(self.vol_profile.total_logged_hours), 11.0)
        self.assertEqual(self.vol_profile.current_streak_days, 1)

        # Verify badge awarded
        self.assertTrue(self.vol_profile.earned_badges.filter(badge=self.b2).exists())

        # Verify NGO received impact hours
        self.ngo_profile.refresh_from_db()
        self.assertEqual(float(self.ngo_profile.total_man_hours_received), 3.0)

        # Verify automated Strava Activity Card created in Community Feed
        card_post = FeedPost.objects.filter(author=self.vol_user, post_type=PostType.ACTIVITY_CARD).first()
        self.assertIsNotNone(card_post)
        self.assertIn("volunteered 3.0 hours", card_post.content)
        self.assertEqual(card_post.activity_metadata['duration_hours'], 3.0)
        self.assertIn("Impact Maker", card_post.activity_metadata['badges_unlocked'])
