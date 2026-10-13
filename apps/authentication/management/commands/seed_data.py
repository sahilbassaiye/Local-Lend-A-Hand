from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.authentication.models import (
    User, UserRole, VolunteerProfile, NGOProfile, NGOVerificationStatus,
    Badge, VolunteerBadge
)
from apps.events.models import Event, EventCategory, EventStatus, EventApplication, ApplicationStatus
from apps.activities.models import VolunteerActivity, ActivityStatus
from apps.community.models import FeedPost, PostType, PostLike, PostComment

class Command(BaseCommand):
    help = 'Seeds realistic sample data for Local Lend a Hand (NGOs, Volunteers, Badges, Spatial Events, Strava Activities)'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding for Local Lend a Hand...")

        # 1. Seed Badges
        badges_data = [
            {
                'name': 'First Step',
                'slug': 'first-step',
                'description': 'Awarded for completing your first verified volunteering drive.',
                'threshold_hours': Decimal('1.00'),
                'icon_name': 'fa-shoe-prints',
                'category': 'HOURS'
            },
            {
                'name': 'Helping Hand',
                'slug': 'helping-hand',
                'description': 'Logged 5 cumulative hours of community service.',
                'threshold_hours': Decimal('5.00'),
                'icon_name': 'fa-hands-helping',
                'category': 'HOURS'
            },
            {
                'name': 'Impact Maker',
                'slug': 'impact-maker',
                'description': 'Dedicated 10+ hours towards making a tangible local difference.',
                'threshold_hours': Decimal('10.00'),
                'icon_name': 'fa-fire',
                'category': 'HOURS'
            },
            {
                'name': 'Eco Champion',
                'slug': 'eco-champion',
                'description': 'Achieved 25 hours contributing to environment and sustainability causes.',
                'threshold_hours': Decimal('25.00'),
                'icon_name': 'fa-leaf',
                'category': 'CAUSE'
            },
            {
                'name': 'Centurion (100h)',
                'slug': 'centurion-100h',
                'description': 'Logged 100 selfless hours transforming lives and communities.',
                'threshold_hours': Decimal('100.00'),
                'icon_name': 'fa-trophy',
                'category': 'HOURS'
            },
        ]

        badges_dict = {}
        for b_data in badges_data:
            badge, _ = Badge.objects.get_or_create(slug=b_data['slug'], defaults=b_data)
            badges_dict[badge.slug] = badge

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(badges_dict)} achievement badges."))

        # 2. Seed NGOs
        # NGO 1: Care India Foundation (Delhi)
        care_user, _ = User.objects.get_or_create(
            username='care_india',
            defaults={
                'email': 'contact@careindia.org',
                'first_name': 'Care India Foundation',
                'role': UserRole.NGO,
                'is_verified': True,
                'profile_image_url': 'https://images.unsplash.com/photo-1593113598332-cd288d649433?w=150&auto=format&fit=crop&q=80'
            }
        )
        care_user.set_password('password123')
        care_user.save()

        care_ngo, _ = NGOProfile.objects.get_or_create(
            user=care_user,
            defaults={
                'organization_name': 'Care India Foundation',
                'darpan_id': 'DL/2019/0182736',
                'verification_status': NGOVerificationStatus.VERIFIED,
                'mission_statement': 'Dedicated to uplifting marginalized communities through quality education, environmental stewardship, and basic healthcare.',
                'history_and_impact': 'Founded in 2012, Care India has impacted over 45,000 underprivileged children and spearheaded 120+ community cleanups across Northern India.',
                'website': 'https://careindia.example.org',
                'contact_email': 'contact@careindia.org',
                'contact_phone': '+91 98112 34567',
                'address': 'Connaught Place, Central Delhi, Delhi - 110001',
                'headquarters_location': Point(77.2195, 28.6315, srid=4326),
                'total_man_hours_received': Decimal('148.50'),
                'total_events_completed': 18
            }
        )

        # NGO 2: Green Earth Trust (Delhi/NCR)
        green_user, _ = User.objects.get_or_create(
            username='green_earth',
            defaults={
                'email': 'hello@greenearth.org',
                'first_name': 'Green Earth Trust',
                'role': UserRole.NGO,
                'is_verified': True,
                'profile_image_url': 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=150&auto=format&fit=crop&q=80'
            }
        )
        green_user.set_password('password123')
        green_user.save()

        green_ngo, _ = NGOProfile.objects.get_or_create(
            user=green_user,
            defaults={
                'organization_name': 'Green Earth Trust',
                'darpan_id': 'DL/2021/0091827',
                'verification_status': NGOVerificationStatus.VERIFIED,
                'mission_statement': 'Restoring urban biodiversity, cleaning water bodies, and organizing massive native tree plantation drives.',
                'history_and_impact': 'Over 85,000 saplings planted with a 92% survival rate. Regular wetland clean-ups engaged over 2,500 active youth volunteers.',
                'website': 'https://greenearthtrust.example.org',
                'contact_email': 'hello@greenearth.org',
                'contact_phone': '+91 98765 43210',
                'address': 'Hauz Khas Enclave, South Delhi, Delhi - 110016',
                'headquarters_location': Point(77.2060, 28.5494, srid=4326),
                'total_man_hours_received': Decimal('320.00'),
                'total_events_completed': 34
            }
        )

        self.stdout.write(self.style.SUCCESS("Seeded 2 Verified NGOs with Darpan IDs."))

        # 3. Seed Volunteers
        # Volunteer 1: Om Sharma (The Hero persona)
        om_user, _ = User.objects.get_or_create(
            username='om_sharma',
            defaults={
                'email': 'om@example.com',
                'first_name': 'Om',
                'last_name': 'Sharma',
                'role': UserRole.VOLUNTEER,
                'is_verified': True,
                'profile_image_url': 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80'
            }
        )
        om_user.set_password('password123')
        om_user.save()

        om_profile, _ = VolunteerProfile.objects.get_or_create(
            user=om_user,
            defaults={
                'bio': 'Passionate about environmental conservation and teaching underprivileged children on weekends. Building a greener tomorrow!',
                'skills': ['River Cleanups', 'Tree Plantation', 'Mathematics Teaching', 'First Aid'],
                'city': 'New Delhi',
                'home_location': Point(77.2090, 28.6139, srid=4326),
                'total_logged_hours': Decimal('16.50'),
                'current_streak_days': 4,
                'longest_streak_days': 6,
                'last_volunteered_date': timezone.now().date()
            }
        )

        # Award badges to Om
        VolunteerBadge.objects.get_or_create(volunteer=om_profile, badge=badges_dict['first-step'])
        VolunteerBadge.objects.get_or_create(volunteer=om_profile, badge=badges_dict['helping-hand'])
        VolunteerBadge.objects.get_or_create(volunteer=om_profile, badge=badges_dict['impact-maker'])

        # Volunteer 2: Priya Patel
        priya_user, _ = User.objects.get_or_create(
            username='priya_patel',
            defaults={
                'email': 'priya@example.com',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'role': UserRole.VOLUNTEER,
                'is_verified': True,
                'profile_image_url': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80'
            }
        )
        priya_user.set_password('password123')
        priya_user.save()

        priya_profile, _ = VolunteerProfile.objects.get_or_create(
            user=priya_user,
            defaults={
                'bio': 'Animal lover and nutrition advocate. Volunteering is my way of giving back.',
                'skills': ['Animal Care', 'Food Distribution', 'Event Photography'],
                'city': 'New Delhi',
                'home_location': Point(77.2200, 28.6200, srid=4326),
                'total_logged_hours': Decimal('8.00'),
                'current_streak_days': 2,
                'longest_streak_days': 3,
                'last_volunteered_date': timezone.now().date() - timedelta(days=1)
            }
        )
        VolunteerBadge.objects.get_or_create(volunteer=priya_profile, badge=badges_dict['first-step'])
        VolunteerBadge.objects.get_or_create(volunteer=priya_profile, badge=badges_dict['helping-hand'])

        self.stdout.write(self.style.SUCCESS("Seeded 2 active Volunteers with streaks & badges."))

        # 4. Seed GeoDjango Events with PostGIS coordinates
        now = timezone.now()
        events_data = [
            {
                'ngo': green_ngo,
                'title': 'Yamuna River Clean-up & Plastic Segregation Drive',
                'category': EventCategory.ENVIRONMENT,
                'description': 'Join Green Earth Trust at Yamuna Ghats to remove discarded plastics, clear shoreline debris, and plant native wetland reeds. Gloves, safety gear, and refreshments will be provided.',
                'banner_image_url': 'https://images.unsplash.com/photo-1618477461853-cf6ed80faba5?w=800&auto=format&fit=crop&q=80',
                'required_skills': ['Debris Clearance', 'Waste Segregation', 'Stamina'],
                'headcount_needed': 25,
                'headcount_applied': 18,
                'headcount_confirmed': 15,
                'start_time': now + timedelta(days=2, hours=9),
                'end_time': now + timedelta(days=2, hours=13),
                'location': Point(77.2410, 28.6500, srid=4326), # Yamuna Ghats, Delhi
                'address': 'Kashmere Gate Yamuna Ghat, Ring Road, Delhi - 110006',
                'geofence_radius_meters': 300,
                'status': EventStatus.ACTIVE
            },
            {
                'ngo': care_ngo,
                'title': 'Weekend Literacy & Fun Mentorship Camp',
                'category': EventCategory.EDUCATION,
                'description': 'Teach foundational math, English reading, and science experiments to primary grade students in community learning centers. No teaching background needed—just enthusiasm!',
                'banner_image_url': 'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800&auto=format&fit=crop&q=80',
                'required_skills': ['Basic English', 'Patience', 'Art & Storytelling'],
                'headcount_needed': 12,
                'headcount_applied': 9,
                'headcount_confirmed': 8,
                'start_time': now + timedelta(days=3, hours=10),
                'end_time': now + timedelta(days=3, hours=14),
                'location': Point(77.2250, 28.5880, srid=4326), # Lodhi Colony, Delhi
                'address': 'Community Centre, Block 12, Lodhi Colony, New Delhi - 110003',
                'geofence_radius_meters': 200,
                'status': EventStatus.ACTIVE
            },
            {
                'ngo': care_ngo,
                'title': 'Community Health & Nutrition Kit Distribution',
                'category': EventCategory.HEALTH,
                'description': 'Help organize medical queues, assist doctors with blood pressure and glucose checks, and distribute fortified nutrition packages to elderly residents.',
                'banner_image_url': 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&auto=format&fit=crop&q=80',
                'required_skills': ['Queue Management', 'Empathy', 'Data Logging'],
                'headcount_needed': 15,
                'headcount_applied': 11,
                'headcount_confirmed': 10,
                'start_time': now + timedelta(days=5, hours=8, minutes=30),
                'end_time': now + timedelta(days=5, hours=13, minutes=30),
                'location': Point(77.1900, 28.6520, srid=4326), # Karol Bagh
                'address': 'Govt School Ground, Ajmal Khan Road, Karol Bagh, Delhi - 110005',
                'geofence_radius_meters': 250,
                'status': EventStatus.ACTIVE
            },
            {
                'ngo': green_ngo,
                'title': 'Urban Reforestation & Seed Ball Workshop',
                'category': EventCategory.ENVIRONMENT,
                'description': 'Make 1,000 clay seed balls containing seeds of Neem, Peepal, and Jamun, and disperse them along the rocky ridge trail to revive local bird populations.',
                'banner_image_url': 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800&auto=format&fit=crop&q=80',
                'required_skills': ['Plantation', 'Outdoor Hiking', 'Teamwork'],
                'headcount_needed': 20,
                'headcount_applied': 16,
                'headcount_confirmed': 14,
                'start_time': now + timedelta(days=6, hours=7),
                'end_time': now + timedelta(days=6, hours=11),
                'location': Point(77.1780, 28.5320, srid=4326), # Sanjay Van, Delhi
                'address': 'Sanjay Van Gate 3, Near Qutub Institutional Area, New Delhi - 110016',
                'geofence_radius_meters': 400,
                'status': EventStatus.ACTIVE
            }
        ]

        created_events = []
        for e_data in events_data:
            ev, _ = Event.objects.get_or_create(title=e_data['title'], ngo=e_data['ngo'], defaults=e_data)
            created_events.append(ev)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_events)} PostGIS spatial events."))

        # 5. Link applications
        EventApplication.objects.get_or_create(event=created_events[0], volunteer=om_profile, defaults={'status': ApplicationStatus.APPROVED})
        EventApplication.objects.get_or_create(event=created_events[1], volunteer=om_profile, defaults={'status': ApplicationStatus.APPROVED})
        EventApplication.objects.get_or_create(event=created_events[0], volunteer=priya_profile, defaults={'status': ApplicationStatus.APPROVED})

        # 6. Seed a completed Strava Activity for Om (Generating the Strava Shareable Activity Card)
        river_event = created_events[0]
        activity_start = now - timedelta(days=1, hours=5)
        activity_end = now - timedelta(days=1, hours=1)

        past_activity, created = VolunteerActivity.objects.get_or_create(
            volunteer=om_profile,
            event=river_event,
            status=ActivityStatus.COMPLETED,
            defaults={
                'check_in_time': activity_start,
                'check_in_location': river_event.location,
                'check_in_distance_meters': 24.5,
                'is_check_in_verified': True,
                'check_out_time': activity_end,
                'check_out_location': river_event.location,
                'check_out_distance_meters': 18.2,
                'is_check_out_verified': True,
                'duration_hours': Decimal('4.00'),
                'reflection_notes': 'Amazing morning cleaning the river bank! Our squad collected 35 sacks of single-use plastic bottles. Feeling so energized and proud!',
                'activity_photo_url': 'https://images.unsplash.com/photo-1618477461853-cf6ed80faba5?w=600&auto=format&fit=crop&q=80',
                'card_generated': True
            }
        )

        # 7. Seed Strava Shareable Card in Community Feed
        if created:
            card_metadata = {
                'volunteer_name': 'Om Sharma',
                'volunteer_username': 'om_sharma',
                'avatar_url': om_user.profile_image_url,
                'duration_hours': 4.0,
                'event_id': river_event.id,
                'event_title': river_event.title,
                'ngo_id': river_event.ngo.id,
                'ngo_name': river_event.ngo.organization_name,
                'ngo_darpan_id': river_event.ngo.darpan_id,
                'event_category': river_event.category,
                'event_address': river_event.address,
                'completed_date': (now - timedelta(days=1)).strftime('%b %d, %Y'),
                'new_streak_days': 4,
                'badges_unlocked': ['Impact Maker'],
                'photo_url': past_activity.activity_photo_url,
            }

            post = FeedPost.objects.create(
                author=om_user,
                post_type=PostType.ACTIVITY_CARD,
                activity=past_activity,
                event=river_event,
                content='Om volunteered 4 hours for River Cleanup with Green Earth Trust! 35 sacks of plastic removed.',
                media_url=past_activity.activity_photo_url,
                likes_count=14,
                comments_count=3,
                activity_metadata=card_metadata
            )

            # Add Likes and Comments
            PostLike.objects.create(post=post, user=priya_user)
            PostLike.objects.create(post=post, user=green_user)
            PostComment.objects.create(post=post, author=green_user, text='Thank you for your tireless dedication, Om! You are a true green hero 🌱')
            PostComment.objects.create(post=post, author=priya_user, text='Super inspiring! Can’t wait to join you on the next one!')

        self.stdout.write(self.style.SUCCESS("Seeded Strava activity with Shareable Activity Card and community feed engagement."))
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
