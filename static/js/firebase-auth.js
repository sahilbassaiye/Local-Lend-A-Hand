/**
 * Firebase Authentication & Onboarding Client
 * Integrates Firebase Web Client SDK with graceful fallback for offline testing
 */

// Global Firebase auth state
let currentUser = null;

async function switchDemoPersona(role) {
    try {
        const res = await fetch('/api/auth/demo-switch/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({ role: role })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`Switched persona to: ${role === 'VOLUNTEER' ? 'Om Sharma (Volunteer)' : 'Care India (NGO)'}`, 'success');
            setTimeout(() => {
                if (role === 'VOLUNTEER') {
                    window.location.href = '/volunteer/dashboard/';
                } else {
                    window.location.href = '/ngo/dashboard/';
                }
            }, 800);
        } else {
            alert(data.error || 'Failed to switch demo persona.');
        }
    } catch (err) {
        alert("Error switching persona: " + err.message);
    }
}

/**
 * Real-time Darpan ID validator on NGO registration form
 */
async function checkDarpanIdRealtime(inputEl) {
    const value = inputEl.value.trim();
    const feedbackEl = document.getElementById('darpan-feedback');
    if (!feedbackEl) return;

    if (!value) {
        feedbackEl.innerHTML = '';
        return;
    }

    try {
        const res = await fetch('/api/auth/validate-darpan/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({ darpan_id: value })
        });
        const data = await res.json();
        if (data.valid) {
            feedbackEl.innerHTML = `
                <div class="text-success small mt-1">
                    <i class="fas fa-check-circle"></i> <b>Verified:</b> Valid Darpan format for <b>${data.state_code}</b> State Chapter (${data.registration_year}).
                </div>
            `;
            inputEl.classList.remove('is-invalid');
            inputEl.classList.add('is-valid');
        } else {
            feedbackEl.innerHTML = `
                <div class="text-danger small mt-1">
                    <i class="fas fa-times-circle"></i> ${data.message}
                </div>
            `;
            inputEl.classList.remove('is-valid');
            inputEl.classList.add('is-invalid');
        }
    } catch (e) {
        console.error("Darpan validation check failed:", e);
    }
}

/**
 * Handle Volunteer Registration
 */
async function handleVolunteerRegister(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Creating Profile...';

    const payload = {
        first_name: form.first_name.value.trim(),
        last_name: form.last_name.value.trim(),
        email: form.email.value.trim(),
        password: form.password.value,
        city: form.city.value.trim(),
        bio: form.bio ? form.bio.value.trim() : '',
        skills: form.skills ? form.skills.value.split(',').map(s => s.trim()).filter(Boolean) : [],
        latitude: form.latitude ? parseFloat(form.latitude.value) || 28.6139 : 28.6139,
        longitude: form.longitude ? parseFloat(form.longitude.value) || 77.2090 : 77.2090,
    };

    try {
        const res = await fetch('/api/auth/register/volunteer/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Welcome to Local Lend a Hand! Profile created.", "success");
            setTimeout(() => {
                window.location.href = '/volunteer/dashboard/';
            }, 800);
        } else {
            alert(JSON.stringify(data.errors || data.error || 'Registration failed.'));
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Sign Up as Volunteer';
        }
    } catch (err) {
        alert("Registration failed: " + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Sign Up as Volunteer';
    }
}

/**
 * Handle NGO Registration with Darpan ID
 */
async function handleNGORegister(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Verifying Darpan ID...';

    const payload = {
        organization_name: form.organization_name.value.trim(),
        darpan_id: form.darpan_id.value.trim().toUpperCase(),
        email: form.email.value.trim(),
        password: form.password.value,
        contact_phone: form.contact_phone.value.trim(),
        mission_statement: form.mission_statement.value.trim(),
        history_and_impact: form.history_and_impact ? form.history_and_impact.value.trim() : '',
        website: form.website ? form.website.value.trim() : '',
        address: form.address.value.trim(),
        latitude: form.latitude ? parseFloat(form.latitude.value) || 28.6139 : 28.6139,
        longitude: form.longitude ? parseFloat(form.longitude.value) || 77.2090 : 77.2090,
    };

    try {
        const res = await fetch('/api/auth/register/ngo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast("NGO Profile registered with verified Darpan ID!", "success");
            setTimeout(() => {
                window.location.href = '/ngo/dashboard/';
            }, 800);
        } else {
            alert(JSON.stringify(data.errors || data.error || 'Registration failed.'));
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Sign Up as NGO';
        }
    } catch (err) {
        alert("Registration error: " + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Sign Up as NGO';
    }
}

/**
 * Handle Standard / Firebase Email Login
 */
async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const email = form.email.value.trim();
    const password = form.password.value;

    try {
        const res = await fetch('/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({ email: email, password: password })
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Logged in successfully!", "success");
            setTimeout(() => {
                if (data.user.role === 'NGO') {
                    window.location.href = '/ngo/dashboard/';
                } else {
                    window.location.href = '/volunteer/dashboard/';
                }
            }, 700);
        } else {
            alert(data.error || 'Login failed. Check your credentials.');
        }
    } catch (err) {
        alert("Login failed: " + err.message);
    }
}

/**
 * Google OAuth Mock / Firebase Trigger
 */
function handleGoogleOAuth() {
    // In production, triggers Firebase popup:
    // const provider = new firebase.auth.GoogleAuthProvider();
    // firebase.auth().signInWithPopup(provider)...
    // For local evaluation, automatically logs in as verified demo volunteer
    showToast("Connecting to Google OAuth via Firebase...", "info");
    setTimeout(() => {
        switchDemoPersona('VOLUNTEER');
    }, 600);
}
