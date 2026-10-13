/**
 * Community Feed & Social Interactions Client
 */

document.addEventListener('DOMContentLoaded', () => {
    loadCommunityFeed();

    const postForm = document.getElementById('create-post-form');
    if (postForm) {
        postForm.addEventListener('submit', handleCreatePost);
    }
});

async function loadCommunityFeed() {
    const feedContainer = document.getElementById('feed-container');
    if (!feedContainer) return;

    try {
        const res = await fetch('/api/feed/');
        const data = await res.json();

        if (!data.posts || data.posts.length === 0) {
            feedContainer.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-comments fa-3x mb-3 text-secondary"></i>
                    <h5>The Community Feed is quiet</h5>
                    <p>Be the first volunteer to share an update or complete a drive!</p>
                </div>
            `;
            return;
        }

        feedContainer.innerHTML = '';
        data.posts.forEach(post => {
            const card = renderPostElement(post);
            feedContainer.appendChild(card);
        });
    } catch (err) {
        feedContainer.innerHTML = '<div class="alert alert-danger">Error loading community feed.</div>';
    }
}

function renderPostElement(post) {
    const div = document.createElement('div');
    const isStravaCard = post.post_type === 'ACTIVITY_CARD';

    if (isStravaCard && post.activity_metadata) {
        const meta = post.activity_metadata;
        div.className = 'strava-activity-card mb-4';
        div.innerHTML = `
            <div class="strava-card-header">
                <div class="d-flex align-items-center gap-2">
                    <img src="${post.author_avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=60&auto=format&fit=crop&q=80'}" class="rounded-circle" width="42" height="42" style="object-fit:cover;">
                    <div>
                        <div class="fw-bold text-dark">${post.author_name || post.author_username}</div>
                        <div class="small text-muted">${new Date(post.created_at).toLocaleDateString()} &bull; <i class="fas fa-check-circle text-success"></i> GPS Verified</div>
                    </div>
                </div>
                <span class="badge bg-success-subtle text-success fs-7"><i class="fas fa-bolt"></i> Strava Activity Card</span>
            </div>
            <div class="strava-card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="strava-hours-hero">
                        <span class="strava-hours-num">${meta.duration_hours}</span>
                        <span class="strava-hours-label">Hours Donated</span>
                    </div>
                    <div>
                        ${meta.new_streak_days ? `<span class="badge bg-warning text-dark px-3 py-2 fw-bold"><i class="fas fa-fire text-danger"></i> ${meta.new_streak_days} Day Streak</span>` : ''}
                    </div>
                </div>

                <h5 class="fw-bold text-dark mb-1">${meta.event_title}</h5>
                <div class="text-muted small mb-3">
                    <i class="fas fa-building text-primary"></i> <b>${meta.ngo_name}</b>
                    <span class="badge-darpan ms-2"><i class="fas fa-shield-alt"></i> ${meta.ngo_darpan_id || 'Verified'}</span>
                </div>

                <p class="text-dark mb-3">${post.content}</p>

                ${post.media_url ? `
                    <div class="mb-3 rounded overflow-hidden" style="max-height:360px;">
                        <img src="${post.media_url}" class="w-100 h-100" style="object-fit:cover;">
                    </div>` : ''
                }

                ${meta.badges_unlocked && meta.badges_unlocked.length ? `
                    <div class="p-2 bg-warning-subtle text-warning-emphasis rounded mb-3 small fw-bold">
                        🏆 Badges Unlocked: ${meta.badges_unlocked.join(', ')}
                    </div>` : ''
                }

                <div class="d-flex justify-content-between align-items-center pt-3 border-top">
                    <div class="d-flex gap-3">
                        <button class="btn btn-sm ${post.is_liked ? 'btn-danger' : 'btn-outline-danger'} px-3" onclick="toggleLike(${post.id}, this)">
                            <i class="${post.is_liked ? 'fas' : 'far'} fa-heart"></i> <span class="like-count">${post.likes_count}</span>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary px-3" onclick="toggleComments(${post.id})">
                            <i class="far fa-comment"></i> ${post.comments_count}
                        </button>
                    </div>
                    <button class="btn btn-sm btn-outline-primary" onclick="sharePost('${post.content.replace(/'/g, "\\'")}')">
                        <i class="fas fa-share-alt"></i> Share
                    </button>
                </div>

                <!-- Comments section -->
                <div id="comments-section-${post.id}" class="mt-3 pt-3 border-top d-none">
                    <div class="comments-list mb-2" id="comments-list-${post.id}">
                        ${(post.comments || []).map(c => `
                            <div class="bg-light p-2 rounded mb-2 small">
                                <b>${c.author_name || c.author_username}:</b> ${c.text}
                            </div>
                        `).join('')}
                    </div>
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control" id="comment-input-${post.id}" placeholder="Write a supportive comment...">
                        <button class="btn btn-primary" onclick="submitComment(${post.id})">Post</button>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Standard User Reflection Post
        div.className = 'card card-custom mb-4';
        div.innerHTML = `
            <div class="card-body">
                <div class="d-flex align-items-center gap-2 mb-3">
                    <img src="${post.author_avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=60&auto=format&fit=crop&q=80'}" class="rounded-circle" width="40" height="40" style="object-fit:cover;">
                    <div>
                        <div class="fw-bold text-dark">${post.author_name || post.author_username}</div>
                        <div class="small text-muted">${new Date(post.created_at).toLocaleDateString()}</div>
                    </div>
                </div>

                <p class="text-dark mb-3">${post.content}</p>

                ${post.media_url ? `
                    <div class="mb-3 rounded overflow-hidden" style="max-height:360px;">
                        <img src="${post.media_url}" class="w-100 h-100" style="object-fit:cover;">
                    </div>` : ''
                }

                <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                    <div class="d-flex gap-3">
                        <button class="btn btn-sm ${post.is_liked ? 'btn-danger' : 'btn-outline-danger'} px-3" onclick="toggleLike(${post.id}, this)">
                            <i class="${post.is_liked ? 'fas' : 'far'} fa-heart"></i> <span class="like-count">${post.likes_count}</span>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary px-3" onclick="toggleComments(${post.id})">
                            <i class="far fa-comment"></i> ${post.comments_count}
                        </button>
                    </div>
                    <button class="btn btn-sm btn-outline-primary" onclick="sharePost('${post.content.replace(/'/g, "\\'")}')">
                        <i class="fas fa-share-alt"></i> Share
                    </button>
                </div>

                <!-- Comments section -->
                <div id="comments-section-${post.id}" class="mt-3 pt-3 border-top d-none">
                    <div class="comments-list mb-2" id="comments-list-${post.id}">
                        ${(post.comments || []).map(c => `
                            <div class="bg-light p-2 rounded mb-2 small">
                                <b>${c.author_name || c.author_username}:</b> ${c.text}
                            </div>
                        `).join('')}
                    </div>
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control" id="comment-input-${post.id}" placeholder="Write a supportive comment...">
                        <button class="btn btn-primary" onclick="submitComment(${post.id})">Post</button>
                    </div>
                </div>
            </div>
        `;
    }
    return div;
}

async function toggleLike(postId, btn) {
    try {
        const res = await fetch(`/api/feed/posts/${postId}/like/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            }
        });
        const data = await res.json();
        if (res.ok) {
            btn.querySelector('.like-count').textContent = data.likes_count;
            if (data.is_liked) {
                btn.classList.remove('btn-outline-danger');
                btn.classList.add('btn-danger');
                btn.querySelector('i').className = 'fas fa-heart';
            } else {
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-outline-danger');
                btn.querySelector('i').className = 'far fa-heart';
            }
        }
    } catch (e) {
        console.error("Like error:", e);
    }
}

function toggleComments(postId) {
    const sec = document.getElementById(`comments-section-${postId}`);
    if (sec) sec.classList.toggle('d-none');
}

async function submitComment(postId) {
    const input = document.getElementById(`comment-input-${postId}`);
    if (!input || !input.value.trim()) return;

    try {
        const res = await fetch(`/api/feed/posts/${postId}/comment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({ text: input.value.trim() })
        });
        const data = await res.json();
        if (res.ok) {
            const list = document.getElementById(`comments-list-${postId}`);
            const comment = data.comment;
            const newDiv = document.createElement('div');
            newDiv.className = 'bg-light p-2 rounded mb-2 small';
            newDiv.innerHTML = `<b>${comment.author_name || comment.author_username}:</b> ${comment.text}`;
            list.appendChild(newDiv);
            input.value = '';
        }
    } catch (e) {
        alert("Could not post comment.");
    }
}

async function handleCreatePost(e) {
    e.preventDefault();
    const content = document.getElementById('post-content').value.trim();
    const mediaUrl = document.getElementById('post-media-url').value.trim();

    if (!content) return;

    try {
        const res = await fetch('/api/feed/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({
                content: content,
                media_url: mediaUrl
            })
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Reflection shared to community feed!", "success");
            document.getElementById('post-content').value = '';
            document.getElementById('post-media-url').value = '';
            loadCommunityFeed();
        } else {
            alert(data.error || "Failed to create post.");
        }
    } catch (err) {
        alert("Error creating post.");
    }
}

function sharePost(text) {
    if (navigator.share) {
        navigator.share({
            title: 'Local Lend a Hand Volunteer Activity',
            text: text,
            url: window.location.href
        }).catch(() => {});
    } else {
        navigator.clipboard.writeText(text + " - Check it out on Local Lend a Hand!");
        showToast("Activity card copied to clipboard!", "info");
    }
}
