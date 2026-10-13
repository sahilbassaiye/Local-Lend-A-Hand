/**
 * Strava for Volunteering Engine Client
 * Handles GPS check-in/out, live timer, and auto-generated shareable activity card modal
 */

let activeTimerInterval = null;
let activeSessionData = null;

document.addEventListener('DOMContentLoaded', () => {
    checkActiveSession();
});

async function checkActiveSession() {
    try {
        const res = await fetch('/api/strava/active/');
        const data = await res.json();
        const activeContainer = document.getElementById('strava-active-container');
        const idleContainer = document.getElementById('strava-idle-container');

        if (!activeContainer || !idleContainer) return;

        if (data.has_active && data.activity) {
            activeSessionData = data.activity;
            activeContainer.classList.remove('d-none');
            idleContainer.classList.add('d-none');

            document.getElementById('active-event-title').textContent = data.activity.event_title;
            document.getElementById('active-ngo-name').textContent = data.activity.ngo_name;
            document.getElementById('active-checkin-time').textContent = new Date(data.activity.check_in_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            startLiveTimer(new Date(data.activity.check_in_time));
        } else {
            activeSessionData = null;
            if (activeTimerInterval) clearInterval(activeTimerInterval);
            activeContainer.classList.add('d-none');
            idleContainer.classList.remove('d-none');
        }
    } catch (err) {
        console.error("Error checking active Strava session:", err);
    }
}

function startLiveTimer(startTime) {
    if (activeTimerInterval) clearInterval(activeTimerInterval);
    const timerDisplay = document.getElementById('live-session-timer');
    if (!timerDisplay) return;

    function update() {
        const now = new Date();
        const diffMs = Math.max(0, now - startTime);
        const hours = Math.floor(diffMs / 3600000);
        const mins = Math.floor((diffMs % 3600000) / 60000);
        const secs = Math.floor((diffMs % 60000) / 1000);
        timerDisplay.textContent = `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    update();
    activeTimerInterval = setInterval(update, 1000);
}

/**
 * Perform GPS Check-In
 */
async function initiateGPSCheckIn(eventId, bypassGeofence = false) {
    const statusMsg = document.getElementById('checkin-status-msg');
    if (statusMsg) statusMsg.innerHTML = '<div class="spinner-border spinner-border-sm text-primary"></div> Acquiring precise GPS coordinates...';

    if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser. Using location simulation.");
        executeCheckInAPI(eventId, 28.6500, 77.2410, true);
        return;
    }

    navigator.geolocation.getCurrentPosition(
        position => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            executeCheckInAPI(eventId, lat, lng, bypassGeofence);
        },
        error => {
            console.warn("GPS error:", error);
            // Graceful fallback: prompt user with option to simulate at event venue
            const simulate = confirm("Could not acquire browser GPS lock. Would you like to check in using venue coordinates for testing?");
            if (simulate) {
                executeCheckInAPI(eventId, 28.6500, 77.2410, true);
            } else if (statusMsg) {
                statusMsg.innerHTML = `<span class="text-danger"><i class="fas fa-exclamation-triangle"></i> Location permission denied.</span>`;
            }
        },
        { enableHighAccuracy: true, timeout: 8000 }
    );
}

async function executeCheckInAPI(eventId, lat, lng, bypassGeofence) {
    const statusMsg = document.getElementById('checkin-status-msg');
    try {
        const res = await fetch('/api/strava/check-in/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({
                event_id: eventId,
                latitude: lat,
                longitude: lng,
                bypass_geofence: bypassGeofence
            })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message, 'success');
            // Close modal if open
            const modalEl = document.getElementById('checkInModal');
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }
            checkActiveSession();
        } else {
            if (statusMsg) {
                statusMsg.innerHTML = `
                    <div class="alert alert-warning mt-2 small">
                        ${data.error || 'Check-in failed.'}
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-dark" onclick="initiateGPSCheckIn(${eventId}, true)">
                                <i class="fas fa-magic"></i> Check In Anyway (Demo Mode)
                            </button>
                        </div>
                    </div>
                `;
            } else {
                alert(data.error || 'Check-in failed');
            }
        }
    } catch (err) {
        alert("Network error during check-in: " + err.message);
    }
}

/**
 * Perform GPS Check-Out and Open Shareable Activity Card
 */
async function initiateGPSCheckOut() {
    const reflectionNotes = document.getElementById('checkout-notes') ? document.getElementById('checkout-notes').value : '';
    const photoUrl = document.getElementById('checkout-photo') ? document.getElementById('checkout-photo').value : '';
    const simulatedHours = document.getElementById('checkout-simulated-hours') ? parseFloat(document.getElementById('checkout-simulated-hours').value) : null;
    const bypassGeofence = document.getElementById('checkout-bypass-geo') ? document.getElementById('checkout-bypass-geo').checked : true;

    let lat = 28.6500;
    let lng = 77.2410;

    if (navigator.geolocation) {
        try {
            const pos = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, { timeout: 3000 }));
            lat = pos.coords.latitude;
            lng = pos.coords.longitude;
        } catch (e) {
            // Keep default venue coordinates
        }
    }

    try {
        const res = await fetch('/api/strava/check-out/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({
                latitude: lat,
                longitude: lng,
                reflection_notes: reflectionNotes,
                photo_url: photoUrl,
                simulated_hours: simulatedHours,
                bypass_geofence: bypassGeofence
            })
        });

        const data = await res.json();
        if (res.ok) {
            showToast(`Awesome work! ${data.duration_hours} hours successfully recorded!`, 'success');
            
            // Close Check-Out modal
            const modalEl = document.getElementById('checkOutModal');
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            // Render Shareable Activity Card Modal
            renderShareableCardModal(data.activity_card, data.new_total_hours, data.current_streak_days, data.newly_awarded_badges);
            
            // Refresh volunteer dashboard metrics & reset timer
            checkActiveSession();
            refreshVolunteerMetrics();
        } else {
            alert(data.error || 'Check-out failed.');
        }
    } catch (err) {
        alert("Error during checkout: " + err.message);
    }
}

function renderShareableCardModal(card, totalHours, streakDays, newBadges) {
    const modalBody = document.getElementById('shareable-card-body');
    if (!modalBody) return;

    modalBody.innerHTML = `
        <div class="strava-activity-card text-start m-0">
            <div class="strava-card-header">
                <div class="d-flex align-items-center gap-2">
                    <img src="${card.avatar_url || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=60&auto=format&fit=crop&q=80'}" class="rounded-circle" width="40" height="40" style="object-fit:cover;">
                    <div>
                        <div class="fw-bold text-dark">${card.volunteer_name}</div>
                        <div class="small text-muted">${card.completed_date} &bull; <i class="fas fa-check-circle text-success"></i> GPS Verified</div>
                    </div>
                </div>
                <span class="badge bg-success-subtle text-success fs-7"><i class="fas fa-bolt"></i> Strava for Volunteering</span>
            </div>
            <div class="strava-card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="strava-hours-hero">
                        <span class="strava-hours-num">${card.duration_hours}</span>
                        <span class="strava-hours-label">Hours Donated</span>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-warning text-dark px-3 py-2 fw-bold"><i class="fas fa-fire text-danger"></i> ${streakDays} Day Streak!</span>
                    </div>
                </div>

                <h5 class="fw-bold text-dark mb-1">${card.event_title}</h5>
                <div class="text-muted small mb-3">
                    <i class="fas fa-building text-primary"></i> <b>${card.ngo_name}</b> 
                    <span class="badge-darpan ms-2"><i class="fas fa-shield-alt"></i> ${card.ngo_darpan_id}</span>
                </div>

                ${card.reflection_notes ? `
                    <div class="p-3 bg-light rounded-3 mb-3 border-start border-3 border-success fst-italic">
                        "${card.reflection_notes}"
                    </div>` : ''
                }

                ${card.badges_unlocked && card.badges_unlocked.length ? `
                    <div class="p-2 bg-warning-subtle text-warning-emphasis rounded mb-2 small fw-bold">
                        🎉 Unlocked Badge: ${card.badges_unlocked.join(', ')}!
                    </div>` : ''
                }

                <div class="text-muted small">
                    <i class="fas fa-map-pin text-danger"></i> ${card.event_address}
                </div>
            </div>
        </div>
    `;

    const shareModalEl = document.getElementById('shareModal');
    if (shareModalEl && typeof bootstrap !== 'undefined') {
        const shareModal = new bootstrap.Modal(shareModalEl);
        shareModal.show();
    }
}

async function refreshVolunteerMetrics() {
    try {
        const res = await fetch('/api/auth/volunteer/metrics/');
        if (!res.ok) return;
        const data = await res.json();
        
        const hoursEl = document.getElementById('profile-total-hours');
        const streakEl = document.getElementById('profile-current-streak');
        if (hoursEl) hoursEl.textContent = data.volunteer.total_logged_hours.toFixed(1);
        if (streakEl) streakEl.textContent = data.volunteer.current_streak_days;
    } catch (e) {
        console.error("Error refreshing metrics:", e);
    }
}
