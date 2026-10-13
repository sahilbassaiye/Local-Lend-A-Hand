# Local Lend a Hand 🤝

> Next-generation civic engagement marketplace connecting **Volunteers** and certified **NGOs**, powered by GeoDjango, PostGIS spatial indexing, Firebase Authentication, and a **"Strava for Volunteering"** activity tracking engine.

---

## 🛠️ Technology Stack
- **Backend**: Python 3.14, Django 6.1, GeoDjango
- **Spatial Database**: PostgreSQL 18 with PostGIS 3.6 extension
- **APIs**: Django REST Framework, REST Framework GIS
- **Authentication**: Firebase Authentication (Google OAuth & Email/Password) with custom role-based User model
- **Frontend**: HTML5, Modern CSS, Vanilla JavaScript, Leaflet / Google Maps JS API

---

## 🚀 Quick Start & How to Run

### 1. Database & Migrations
The PostGIS database `local_lend_a_hand` has already been created and migrated.
To re-run migrations at any point:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Seed Realistic Test Data
To re-seed demo volunteers, verified NGOs, badges, spatial events, and sample Strava activities:
```bash
python manage.py seed_data
```

### 3. Run Development Server
```bash
python manage.py runserver 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 👥 Demo Personas (Pre-seeded)

Use the **Persona Switcher** in the top navigation bar to switch personas with 1-click:

| Persona | Role | Credentials | Highlights |
| :--- | :--- | :--- | :--- |
| **Om Sharma** | Volunteer | `om@example.com` / `password123` | 16.5h logged, 4-day streak, 3 unlocked milestone badges |
| **Priya Patel** | Volunteer | `priya@example.com` / `password123` | 8.0h logged, 2-day streak |
| **Care India** | Verified NGO | `contact@careindia.org` / `password123` | Darpan ID: `DL/2019/0182736`, 148.5 man-hours received |
| **Green Earth Trust**| Verified NGO | `hello@greenearth.org` / `password123` | Darpan ID: `DL/2021/0091827`, 320.0 man-hours received |

---

## 🌟 Key Features Implemented

### 1. Authentication & Onboarding
- **Volunteer Auth**: Email/Password and Google OAuth sign-up/login.
- **NGO Auth**: Requires mandatory **NGO Darpan ID** field formatted as `STATE/YEAR/7-DIGITS` (e.g. `DL/2019/0182736`). Real-time validation endpoint (`/api/auth/validate-darpan/`) checks formatting against official NITI Aayog portal rules.
- **Dual-role Data Model**: Custom `User` model with `role` (`VOLUNTEER` vs `NGO`), linked to `VolunteerProfile` and `NGOProfile`.

### 2. Volunteer Dashboard (`/volunteer/dashboard/`)
- **Profile Tab**: Displays total logged hours, current & longest streak, and an interactive **Achievement Badges Shelf** (unlocked and locked badges).
- **Event Sign-Up Tab**: GeoDjango spatial query (`/api/events/nearby/?lat=...&lng=...&radius=...`) displaying nearby NGO events on an embedded map with radius filter and **1-Click Apply** button.
- **Community Feed Tab**: Direct access to social timeline with likes and comments.

### 3. NGO Dashboard (`/ngo/dashboard/`)
- **Impact & Analytics Dashboard**: Real-time aggregated metrics displaying total man-hours donated to their cause, unique volunteers engaged, active drives, and drive-by-drive reach breakdown.
- **Event Posting Engine**: Form with required skills, headcount needed, start/end dates, and an interactive **Location Map Picker** with draggable pin and visual geofence circle overlay (100m – 1000m).
- **NGO Public Profile** (`/ngo/profile/<id>/`): Public-facing info page about organization's mission, history, contact details, and active drives.

### 4. The "Strava for Volunteering" Core Engagement Engine
- **Geolocation Check-In** (`/api/strava/check-in/`): Uses browser GPS to verify the volunteer is physically within the drive venue's geofence radius.
- **Live Session Timer**: Real-time ticker while volunteering.
- **Geolocation Check-Out** (`/api/strava/check-out/`): Computes duration, increments volunteer's total hours, advances activity streak, awards new milestone badges, and increments the hosting NGO's total man-hours.
- **Automated Shareable Activity Card**: Automatically publishes a card into the Community Feed (e.g., *"Om Sharma volunteered 4.0 hours for Yamuna River Clean-up Drive with Green Earth Trust"*), including hours badge, event title, NGO Darpan badge, and reflection story.

---

## 🧪 Automated Test Suite
Run the test suite:
```bash
python manage.py test apps.activities
```
Tests verify:
- Darpan ID regex validation & blacklisting
- PostGIS Haversine distance accuracy
- Geofence check-in verification (within radius vs outside radius)
- Check-out duration calculation, milestone badge awarding, NGO impact increment, and automatic Community Feed card publication.
