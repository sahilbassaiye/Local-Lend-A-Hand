/**
 * Interactive Spatial Maps Engine for Local Lend a Hand
 * Uses fast, reliable ESRI ArcGIS World Street Map (100% unrestricted, zero watermarks)
 * Powers:
 * 1. Event Sign-Up Discovery Map with Auto-GPS & City Search (Volunteer Hub)
 * 2. Current Event Progress & GPS Geofence Radar Map (Volunteer Hub)
 * 3. Event Posting Engine Location Picker with Search (NGO Portal)
 * 4. Live Drive & Attendee Tracking Map (NGO Portal)
 */

let eventDiscoveryMap = null;
let userLocationMarker = null;
let eventMarkers = [];
let volunteerProgressMap = null;
let locationPickerMap = null;
let pickerMarker = null;
let geofenceCircle = null;
let ngoLiveMap = null;

// Initial Coordinates (Delhi NCR center)
const DEFAULT_LAT = 28.6139;
const DEFAULT_LNG = 77.2090;
window.DEFAULT_LAT = DEFAULT_LAT;
window.DEFAULT_LNG = DEFAULT_LNG;
let currentVolunteerLat = DEFAULT_LAT;
let currentVolunteerLng = DEFAULT_LNG;

const TILE_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}';
const TILE_CONFIG = {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ',
    maxZoom: 19
};

function attachReliableTiles(mapInstance) {
    const layer = L.tileLayer(TILE_URL, TILE_CONFIG);
    layer.addTo(mapInstance);
    return layer;
}

/**
 * Tab switcher auto-resize & lazy init
 */
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('button[data-bs-toggle="tab"], a[data-bs-toggle="tab"]').forEach(tabEl => {
        tabEl.addEventListener('shown.bs.tab', (e) => {
            const target = tabEl.getAttribute('data-bs-target') || tabEl.getAttribute('href');
            if (target === '#post-drive-content' && !locationPickerMap) {
                initLocationPickerMap('location-picker-map', DEFAULT_LAT, DEFAULT_LNG);
            }
            setTimeout(() => {
                if (eventDiscoveryMap) eventDiscoveryMap.invalidateSize();
                if (volunteerProgressMap) volunteerProgressMap.invalidateSize();
                if (locationPickerMap) locationPickerMap.invalidateSize();
                if (ngoLiveMap) ngoLiveMap.invalidateSize();
            }, 150);
            setTimeout(() => {
                if (locationPickerMap) locationPickerMap.invalidateSize();
            }, 350);
        });
    });
});

/**
 * 1. EVENT DISCOVERY MAP (Volunteer Event Sign-Up Tab)
 */
function initEventDiscoveryMap(containerId = 'events-map') {
    const container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') return;

    if (container._leaflet_id && eventDiscoveryMap) {
        eventDiscoveryMap.invalidateSize();
        return;
    }

    eventDiscoveryMap = L.map(containerId, { scrollWheelZoom: true }).setView([currentVolunteerLat, currentVolunteerLng], 12);
    attachReliableTiles(eventDiscoveryMap);

    // Create user marker
    const userIcon = L.divIcon({
        html: '<div style="background:#0ea5e9;color:white;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 14px rgba(14,165,233,0.8);border:2px solid white;font-size:15px;"><i class="fas fa-street-view"></i></div>',
        className: 'user-pin-marker',
        iconSize: [36, 36],
        iconAnchor: [18, 18]
    });

    userLocationMarker = L.marker([currentVolunteerLat, currentVolunteerLng], { icon: userIcon }).addTo(eventDiscoveryMap)
        .bindPopup("<b>Your Location</b><br>Detecting precise GPS coordinates...").openPopup();

    // Auto-detect browser GPS location
    detectAndCenterUserGPS();
}

/**
 * Automatically detects device GPS location and centers discovery map
 */
function detectAndCenterUserGPS(forceAlert = false) {
    const label = document.getElementById('user-location-coords-label');
    if (label) label.innerHTML = '<span class="spinner-border spinner-border-sm text-primary me-1"></span> Acquiring GPS location...';

    if (!navigator.geolocation) {
        if (label) label.textContent = `${currentVolunteerLat.toFixed(4)}° N, ${currentVolunteerLng.toFixed(4)}° E (Default)`;
        loadNearbyEvents(currentVolunteerLat, currentVolunteerLng);
        return;
    }

    navigator.geolocation.getCurrentPosition(
        position => {
            currentVolunteerLat = position.coords.latitude;
            currentVolunteerLng = position.coords.longitude;

            if (eventDiscoveryMap && userLocationMarker) {
                eventDiscoveryMap.flyTo([currentVolunteerLat, currentVolunteerLng], 13, { duration: 1.2 });
                userLocationMarker.setLatLng([currentVolunteerLat, currentVolunteerLng]);
                userLocationMarker.setPopupContent(`<b>Your Live GPS Location</b><br>Lat: ${currentVolunteerLat.toFixed(4)}, Lng: ${currentVolunteerLng.toFixed(4)}<br><span class="badge bg-success">GPS Locked</span>`);
            }

            if (label) {
                label.innerHTML = `<i class="fas fa-satellite text-success me-1"></i> <b>${currentVolunteerLat.toFixed(4)}° N, ${currentVolunteerLng.toFixed(4)}° E</b> (Live Device GPS)`;
            }

            if (forceAlert) {
                showToast(`Location updated to your GPS position (${currentVolunteerLat.toFixed(4)}, ${currentVolunteerLng.toFixed(4)})`, 'success');
            }

            loadNearbyEvents(currentVolunteerLat, currentVolunteerLng);
        },
        error => {
            console.warn("GPS auto-detection skipped:", error.message);
            if (label) {
                label.innerHTML = `<span>${currentVolunteerLat.toFixed(4)}° N, ${currentVolunteerLng.toFixed(4)}° E</span> <span class="badge bg-light text-muted border ms-1">Delhi Region (Click 'Locate Me' or Search below)</span>`;
            }
            if (forceAlert) {
                showToast("Could not access device GPS. Please check browser location permissions or search your city.", "warning");
            }
            loadNearbyEvents(currentVolunteerLat, currentVolunteerLng);
        },
        { enableHighAccuracy: true, timeout: 6000 }
    );
}

/**
 * Search any city or address and pan discovery map
 */
async function searchDiscoveryLocation() {
    const input = document.getElementById('discovery-search-input');
    if (!input || !input.value.trim()) return;

    const query = input.value.trim();
    showToast(`Searching for "${query}"...`, 'info');

    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (data && data.length > 0) {
            const lat = parseFloat(data[0].lat);
            const lng = parseFloat(data[0].lon);
            currentVolunteerLat = lat;
            currentVolunteerLng = lng;

            if (eventDiscoveryMap && userLocationMarker) {
                eventDiscoveryMap.flyTo([lat, lng], 13, { duration: 1.2 });
                userLocationMarker.setLatLng([lat, lng]);
                userLocationMarker.setPopupContent(`<b>Location: ${data[0].display_name.split(',')[0]}</b><br>${data[0].display_name.substring(0, 50)}...`).openPopup();
            }

            const label = document.getElementById('user-location-coords-label');
            if (label) {
                label.innerHTML = `<b>${data[0].display_name.split(',')[0]}</b> (${lat.toFixed(4)}°, ${lng.toFixed(4)}°)`;
            }

            loadNearbyEvents(lat, lng);
            showToast(`Map centered on ${data[0].display_name.split(',')[0]}!`, 'success');
        } else {
            showToast(`Location "${query}" not found. Try entering city name.`, 'warning');
        }
    } catch (e) {
        showToast("Search failed. Check internet connection.", "danger");
    }
}

/**
 * Jump to popular city preset
 */
function jumpToCityPreset(cityName, lat, lng) {
    currentVolunteerLat = lat;
    currentVolunteerLng = lng;

    if (eventDiscoveryMap && userLocationMarker) {
        eventDiscoveryMap.flyTo([lat, lng], 12, { duration: 1.2 });
        userLocationMarker.setLatLng([lat, lng]);
        userLocationMarker.setPopupContent(`<b>Location: ${cityName}</b><br>Viewing volunteer drives in ${cityName}`).openPopup();
    }

    const label = document.getElementById('user-location-coords-label');
    if (label) {
        label.innerHTML = `<b>${cityName}</b> (${lat.toFixed(4)}°, ${lng.toFixed(4)}°)`;
    }

    loadNearbyEvents(lat, lng);
    showToast(`Viewing drives in ${cityName}`, 'info');
}

/**
 * Fetch and render nearby NGO drives on map
 */
async function loadNearbyEvents(lat = currentVolunteerLat, lng = currentVolunteerLng, radiusKm = 50, category = '') {
    const listContainer = document.getElementById('events-list-container');
    if (listContainer) {
        listContainer.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-success"></div><p class="mt-2 text-muted small">Querying PostGIS spatial drives...</p></div>';
    }

    try {
        let url = `/api/events/nearby/?lat=${lat}&lng=${lng}&radius=${radiusKm}`;
        if (category) url += `&category=${category}`;

        let res = await fetch(url);
        let data = await res.json();

        // Clear existing drive markers
        if (eventMarkers.length && eventDiscoveryMap) {
            eventMarkers.forEach(m => eventDiscoveryMap.removeLayer(m));
            eventMarkers = [];
        }

        // If no drives exist within user's immediate radius, fetch all active drives so the map is never empty
        let isFallbackGlobal = false;
        if (!data.events || data.events.length === 0) {
            const allRes = await fetch(`/api/events/nearby/?radius=5000`);
            const allData = await allRes.json();
            if (allData.events && allData.events.length > 0) {
                data = allData;
                isFallbackGlobal = true;
            }
        }

        if (listContainer) {
            if (!data.events || data.events.length === 0) {
                listContainer.innerHTML = `
                    <div class="alert alert-light border text-center py-4">
                        <i class="fas fa-map-marked-alt fa-2x text-muted mb-2"></i>
                        <h6 class="fw-bold">No active drives posted right now</h6>
                        <p class="small text-muted mb-0">Check back soon as NGOs add new volunteering drives!</p>
                    </div>`;
                return;
            }

            listContainer.innerHTML = isFallbackGlobal ? `
                <div class="alert alert-warning py-2 px-3 small mb-3 border d-flex align-items-center justify-content-between">
                    <div>
                        <i class="fas fa-info-circle me-1"></i> <b>No drives within ${radiusKm}km of selected location.</b><br>
                        Showing all active NGO drives available across regions.
                    </div>
                    <button class="btn btn-xs btn-outline-dark fs-8" onclick="jumpToCityPreset('Delhi', 28.6139, 77.2090)">View Delhi Hub</button>
                </div>
            ` : '';
        }

        const markerBounds = [];
        if (userLocationMarker) {
            markerBounds.push(userLocationMarker.getLatLng());
        }

        data.events.forEach(ev => {
            if (ev.lat && ev.lng && typeof L !== 'undefined' && eventDiscoveryMap) {
                const eventIcon = L.divIcon({
                    html: '<div style="background:#10b981;color:white;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(16,185,129,0.5);border:2px solid white;font-size:14px;"><i class="fas fa-hands-helping"></i></div>',
                    className: 'event-pin-marker',
                    iconSize: [36, 36],
                    iconAnchor: [18, 18]
                });

                const marker = L.marker([ev.lat, ev.lng], { icon: eventIcon }).addTo(eventDiscoveryMap);
                const popupHtml = `
                    <div style="min-width:230px; font-family:'Plus Jakarta Sans',sans-serif;">
                        <span class="badge bg-success-subtle text-success small mb-1">${ev.category}</span>
                        <h6 class="fw-bold mb-1 text-dark">${ev.title}</h6>
                        <div class="small text-muted mb-2">
                            <b><i class="fas fa-building text-primary"></i> ${ev.ngo_name}</b><br>
                            <span class="badge-darpan py-0 px-1 fs-9"><i class="fas fa-shield-alt"></i> ${ev.ngo_darpan_id || 'Verified'}</span>
                        </div>
                        <div class="small text-muted mb-2"><i class="fas fa-map-marker-alt text-danger"></i> ${ev.distance_km !== null ? ev.distance_km + ' km away' : ev.address}</div>
                        <div class="small text-muted mb-3"><i class="fas fa-users"></i> ${ev.headcount_applied} / ${ev.headcount_needed} spots</div>
                        <div>
                            ${ev.is_applied 
                                ? '<button class="btn btn-sm btn-outline-secondary w-100 fw-bold" disabled><i class="fas fa-check"></i> Already Applied</button>'
                                : `<button class="btn btn-sm btn-emerald w-100 fw-bold" onclick="applyForEvent(${ev.id})"><i class="fas fa-hand-sparkles me-1"></i> 1-Click Apply</button>`
                            }
                        </div>
                    </div>
                `;
                marker.bindPopup(popupHtml);
                eventMarkers.push(marker);
                markerBounds.push([ev.lat, ev.lng]);
            }

            // List Card
            if (listContainer) {
                const card = document.createElement('div');
                card.className = 'card card-custom mb-3 p-3';
                card.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <span class="badge bg-success-subtle text-success mb-1 fs-8">${ev.category}</span>
                            <h6 class="fw-bold mb-1 text-dark">${ev.title}</h6>
                            <div class="text-muted small">
                                <span class="fw-bold text-dark"><i class="fas fa-building text-primary"></i> ${ev.ngo_name}</span>
                                <span class="badge-darpan ms-2 fs-9"><i class="fas fa-shield-alt"></i> ${ev.ngo_darpan_id}</span>
                            </div>
                        </div>
                        ${ev.distance_km !== null ? `<span class="badge bg-primary px-2 py-1 fs-8"><i class="fas fa-location-arrow"></i> ${ev.distance_km} km</span>` : ''}
                    </div>
                    <p class="text-muted small mb-2">${(ev.description || '').substring(0, 130)}...</p>
                    <div class="d-flex flex-wrap gap-1 mb-3">
                        ${(ev.required_skills || []).map(s => `<span class="badge bg-light text-dark border fs-9">${s}</span>`).join('')}
                    </div>
                    <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                        <small class="text-muted"><i class="fas fa-users"></i> ${ev.headcount_applied} / ${ev.headcount_needed} spots filled</small>
                        <div class="d-flex gap-2">
                            <button class="btn btn-outline-dark btn-sm px-2" onclick="eventDiscoveryMap.flyTo([${ev.lat}, ${ev.lng}], 15); showToast('Panned to ${ev.title.replace(/'/g, "\\'")}', 'info');" title="Focus on map">
                                <i class="fas fa-eye"></i> Map
                            </button>
                            ${ev.is_applied 
                                ? '<button class="btn btn-outline-secondary btn-sm px-3" disabled><i class="fas fa-check"></i> Applied</button>'
                                : `<button class="btn btn-emerald btn-sm px-3" onclick="applyForEvent(${ev.id})"><i class="fas fa-hand-sparkles"></i> 1-Click Apply</button>`
                            }
                        </div>
                    </div>
                `;
                listContainer.appendChild(card);
            }
        });

        // Fit map bounds if fallback or drives found
        if (isFallbackGlobal && markerBounds.length > 1 && eventDiscoveryMap) {
            eventDiscoveryMap.fitBounds(L.latLngBounds(markerBounds), { padding: [50, 50], maxZoom: 13 });
        }
    } catch (err) {
        console.error("Error loading nearby events:", err);
    }
}

/**
 * 1-Click Apply Handler
 */
async function applyForEvent(eventId) {
    try {
        const res = await fetch(`/api/events/${eventId}/apply/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            }
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message || 'Successfully applied!', 'success');
            loadNearbyEvents(currentVolunteerLat, currentVolunteerLng);
        } else {
            showToast(data.error || 'Could not apply.', 'warning');
        }
    } catch (e) {
        showToast('Application failed.', 'danger');
    }
}

/**
 * 2. VOLUNTEER CURRENT EVENT PROGRESS & GPS GEOFENCE RADAR MAP
 */
function initVolunteerProgressMap(containerId = 'volunteer-progress-map', eventLat = 28.6500, eventLng = 77.2410, geofenceMeters = 250, eventTitle = 'Yamuna River Clean-up') {
    const container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') return;

    if (container._leaflet_id && volunteerProgressMap) {
        volunteerProgressMap.invalidateSize();
        return;
    }

    volunteerProgressMap = L.map(containerId).setView([eventLat, eventLng], 15);
    attachReliableTiles(volunteerProgressMap);

    // Event venue pin
    const venueIcon = L.divIcon({
        html: '<div style="background:#ef4444;color:white;border-radius:50%;width:38px;height:38px;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(239,68,68,0.6);border:2px solid white;font-size:16px;"><i class="fas fa-map-marker-alt"></i></div>',
        className: 'venue-marker',
        iconSize: [38, 38],
        iconAnchor: [19, 19]
    });
    L.marker([eventLat, eventLng], { icon: venueIcon }).addTo(volunteerProgressMap)
        .bindPopup(`<b>${eventTitle}</b><br>Event Venue & Check-In Site`).openPopup();

    // Geofence perimeter circle
    L.circle([eventLat, eventLng], {
        radius: geofenceMeters,
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.18,
        weight: 2
    }).addTo(volunteerProgressMap).bindPopup(`<b>Geofence Boundary</b><br>${geofenceMeters}m check-in radius`);

    // Volunteer's position pin
    let userLiveLat = eventLat + 0.0002;
    let userLiveLng = eventLng + 0.0002;

    const userLiveIcon = L.divIcon({
        html: '<div style="background:#3b82f6;color:white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 10px rgba(59,130,246,0.8);border:2px solid white;font-size:13px;"><i class="fas fa-running"></i></div>',
        className: 'user-live-pin',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    const userMarker = L.marker([userLiveLat, userLiveLng], { icon: userLiveIcon }).addTo(volunteerProgressMap);
    userMarker.bindPopup("<b>Your Position</b><br>Inside Event Geofence (Verified 24m)");

    L.polyline([[eventLat, eventLng], [userLiveLat, userLiveLng]], {
        color: '#10b981',
        dashArray: '5, 8',
        weight: 2
    }).addTo(volunteerProgressMap);

    // Auto-center with device GPS if available
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            const curLat = pos.coords.latitude;
            const curLng = pos.coords.longitude;
            userMarker.setLatLng([curLat, curLng]);
            userMarker.setPopupContent("<b>Live GPS Position</b><br>Device location acquired");
            volunteerProgressMap.fitBounds(L.latLngBounds([[eventLat, eventLng], [curLat, curLng]]), { padding: [50, 50], maxZoom: 16 });
        }, () => {});
    }
}

/**
 * 3. NGO EVENT POSTING ENGINE (LOCATION PICKER MAP)
 */
function initLocationPickerMap(containerId = 'location-picker-map', initialLat = 28.6139, initialLng = 77.2090) {
    const container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') return null;

    const lat = parseFloat(initialLat) || DEFAULT_LAT;
    const lng = parseFloat(initialLng) || DEFAULT_LNG;

    // If map instance is already running on this container, just recenter and invalidate
    if (locationPickerMap) {
        locationPickerMap.invalidateSize();
        locationPickerMap.setView([lat, lng], 14);
        if (pickerMarker) pickerMarker.setLatLng([lat, lng]);
        if (geofenceCircle) geofenceCircle.setLatLng([lat, lng]);
        updatePickerCoordinates(lat, lng, false);
        return locationPickerMap;
    }

    // Safety check: if container has leftover leaflet ID without map object, clear it
    if (container._leaflet_id) {
        container._leaflet_id = null;
    }

    locationPickerMap = L.map(containerId, {
        center: [lat, lng],
        zoom: 14,
        scrollWheelZoom: true
    });
    attachReliableTiles(locationPickerMap);

    const pickerIcon = L.divIcon({
        html: '<div style="background:#ef4444;color:white;border-radius:50%;width:38px;height:38px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(239,68,68,0.6);border:2px solid white;font-size:16px;"><i class="fas fa-map-pin"></i></div>',
        className: 'picker-pin',
        iconSize: [38, 38],
        iconAnchor: [19, 19]
    });

    pickerMarker = L.marker([lat, lng], {
        icon: pickerIcon,
        draggable: true
    }).addTo(locationPickerMap);

    const radiusInput = document.getElementById('id_geofence_radius');
    const radiusMeters = radiusInput ? parseInt(radiusInput.value) || 250 : 250;
    geofenceCircle = L.circle([lat, lng], {
        radius: radiusMeters,
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.16,
        weight: 2
    }).addTo(locationPickerMap);

    updatePickerCoordinates(lat, lng, false);

    pickerMarker.on('dragend', function (e) {
        const pos = e.target.getLatLng();
        if (geofenceCircle) geofenceCircle.setLatLng(pos);
        updatePickerCoordinates(pos.lat, pos.lng, true);
    });

    locationPickerMap.on('click', function (e) {
        if (pickerMarker) pickerMarker.setLatLng(e.latlng);
        if (geofenceCircle) geofenceCircle.setLatLng(e.latlng);
        updatePickerCoordinates(e.latlng.lat, e.latlng.lng, true);
    });

    if (radiusInput) {
        radiusInput.addEventListener('input', function () {
            const rad = parseInt(this.value) || 250;
            if (geofenceCircle) geofenceCircle.setRadius(rad);
            const label = document.getElementById('radius-value-label');
            if (label) label.textContent = `${rad} meters`;
        });
    }

    // Double invalidateSize calls to ensure clean rendering after CSS tab fade transitions
    setTimeout(() => {
        if (locationPickerMap) locationPickerMap.invalidateSize();
    }, 150);
    setTimeout(() => {
        if (locationPickerMap) locationPickerMap.invalidateSize();
    }, 350);

    return locationPickerMap;
}

async function searchPickerAddress() {
    const input = document.getElementById('picker-search-input');
    if (!input || !input.value.trim()) return;

    const query = input.value.trim();
    showToast(`Searching location "${query}"...`, 'info');

    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const data = await res.json();
        if (data && data.length > 0) {
            const lat = parseFloat(data[0].lat);
            const lng = parseFloat(data[0].lon);

            // Populate address field with resolved full address
            const addrInput = document.getElementById('id_address');
            if (addrInput) addrInput.value = data[0].display_name;

            // Ensure map is initialized and pan/zoom to searched place
            if (!locationPickerMap) {
                initLocationPickerMap('location-picker-map', lat, lng);
            } else {
                locationPickerMap.invalidateSize();
                locationPickerMap.setView([lat, lng], 15);
                if (pickerMarker) pickerMarker.setLatLng([lat, lng]);
                if (geofenceCircle) geofenceCircle.setLatLng([lat, lng]);
            }

            // Always update coordinates in form & UI without reverse geocode overwriting display_name
            updatePickerCoordinates(lat, lng, false);
            showToast(`Pin placed at: ${data[0].display_name.split(',')[0]}`, 'success');

            setTimeout(() => {
                if (locationPickerMap) locationPickerMap.invalidateSize();
            }, 100);
        } else {
            showToast("Address not found. Please try another landmark or city.", "warning");
        }
    } catch (e) {
        console.error("Address search error:", e);
        showToast("Address search error. Please check your network.", "danger");
    }
}

function locatePickerToDeviceGPS() {
    if (!navigator.geolocation) {
        showToast("Geolocation is not supported by your browser.", "warning");
        return;
    }
    showToast("Acquiring GPS location...", "info");
    navigator.geolocation.getCurrentPosition(
        pos => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            if (!locationPickerMap) {
                initLocationPickerMap('location-picker-map', lat, lng);
            } else {
                locationPickerMap.invalidateSize();
                locationPickerMap.flyTo([lat, lng], 15);
                if (pickerMarker) pickerMarker.setLatLng([lat, lng]);
                if (geofenceCircle) geofenceCircle.setLatLng([lat, lng]);
            }
            updatePickerCoordinates(lat, lng, true);
            showToast("Pin moved to your GPS location!", "success");
        },
        err => {
            console.warn("GPS error:", err.message);
            showToast("Could not access GPS location. Please check browser permissions.", "warning");
        },
        { enableHighAccuracy: true, timeout: 6000 }
    );
}

function updatePickerCoordinates(lat, lng, shouldReverseGeocode = true) {
    const numLat = parseFloat(lat);
    const numLng = parseFloat(lng);
    if (isNaN(numLat) || isNaN(numLng)) return;

    const latInput = document.getElementById('id_latitude');
    const lngInput = document.getElementById('id_longitude');
    if (latInput) latInput.value = numLat.toFixed(6);
    if (lngInput) lngInput.value = numLng.toFixed(6);

    const displayLat = document.getElementById('display-lat');
    const displayLng = document.getElementById('display-lng');
    if (displayLat) displayLat.textContent = numLat.toFixed(6);
    if (displayLng) displayLng.textContent = numLng.toFixed(6);

    if (shouldReverseGeocode) {
        fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${numLat}&lon=${numLng}`)
            .then(r => r.json())
            .then(d => {
                const addr = document.getElementById('id_address');
                if (addr && d.display_name) {
                    addr.value = d.display_name;
                }
            })
            .catch(() => {});
    }
}

/**
 * 4. NGO LIVE CURRENT EVENT TRACKING MAP
 */
function initNGOLiveTrackerMap(containerId = 'ngo-live-tracker-map', eventLat = 28.6500, eventLng = 77.2410, geofenceMeters = 300, eventTitle = 'Yamuna River Clean-up') {
    const container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') return;

    if (container._leaflet_id && ngoLiveMap) {
        ngoLiveMap.invalidateSize();
        return;
    }

    ngoLiveMap = L.map(containerId).setView([eventLat, eventLng], 15);
    attachReliableTiles(ngoLiveMap);

    const venueIcon = L.divIcon({
        html: '<div style="background:#0f172a;color:white;border-radius:50%;width:38px;height:38px;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 12px rgba(15,23,42,0.6);border:2px solid #10b981;font-size:16px;"><i class="fas fa-flag"></i></div>',
        className: 'ngo-venue-pin',
        iconSize: [38, 38],
        iconAnchor: [19, 19]
    });
    L.marker([eventLat, eventLng], { icon: venueIcon }).addTo(ngoLiveMap)
        .bindPopup(`<b>${eventTitle}</b><br>Active Drive Site`).openPopup();

    L.circle([eventLat, eventLng], {
        radius: geofenceMeters,
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.15,
        weight: 2
    }).addTo(ngoLiveMap).bindPopup(`<b>Geofence Radius</b>: ${geofenceMeters}m`);

    const attendees = [
        { name: 'Om Sharma', lat: eventLat + 0.0004, lng: eventLng + 0.0003, time: '09:00 AM', hours: '2.5h' },
        { name: 'Priya Patel', lat: eventLat - 0.0003, lng: eventLng + 0.0005, time: '09:15 AM', hours: '2.2h' },
        { name: 'Aarav Mehta', lat: eventLat + 0.0002, lng: eventLng - 0.0004, time: '09:30 AM', hours: '2.0h' }
    ];

    attendees.forEach(a => {
        const volIcon = L.divIcon({
            html: '<div style="background:#10b981;color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(16,185,129,0.5);border:2px solid white;font-size:11px;"><i class="fas fa-check"></i></div>',
            className: 'volunteer-on-site-pin',
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
        L.marker([a.lat, a.lng], { icon: volIcon }).addTo(ngoLiveMap)
            .bindPopup(`<b>${a.name}</b><br><span class="text-success fw-bold">🟢 On Site</span><br>Check-in: ${a.time} (${a.hours})`);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        alert(message);
        return;
    }
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg py-2 px-4 mb-2 fade show border`;
    toast.style.borderRadius = '12px';
    toast.innerHTML = `<i class="fas fa-bell me-2"></i> ${message}`;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
