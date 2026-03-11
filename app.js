const queueContainer = document.getElementById('queue-container');
const historyContainer = document.getElementById('history-container');
const queueCount = document.getElementById('queue-count');
const authModal = document.getElementById('auth-modal');
const ghTokenInput = document.getElementById('gh-token-input');
const saveTokenBtn = document.getElementById('save-token-btn');
const closeModalBtn = document.getElementById('close-modal-btn');
const confirmModal = document.getElementById('confirm-modal');
const confirmTitle = document.getElementById('confirm-title');
const confirmMessage = document.getElementById('confirm-message');
const confirmYesBtn = document.getElementById('confirm-yes-btn');
const confirmNoBtn = document.getElementById('confirm-no-btn');

const GITHUB_OWNER = 'Vcaze';
const GITHUB_REPO = 'football-news-bot';

let queueData = [];
let historyData = [];

// ── Custom in-page confirm (returns a Promise<boolean>) ──────────────────────
function showConfirm(title, message, yesBtnLabel = 'Yes, proceed', yesBtnClass = 'primary') {
    return new Promise(resolve => {
        confirmTitle.textContent = title;
        confirmMessage.textContent = message;
        confirmYesBtn.textContent = yesBtnLabel;
        confirmYesBtn.className = `btn ${yesBtnClass}`;
        confirmModal.classList.add('active');

        const yes = () => { cleanup(); resolve(true); };
        const no  = () => { cleanup(); resolve(false); };

        function cleanup() {
            confirmModal.classList.remove('active');
            confirmYesBtn.removeEventListener('click', yes);
            confirmNoBtn.removeEventListener('click', no);
        }

        confirmYesBtn.addEventListener('click', yes);
        confirmNoBtn.addEventListener('click', no);
    });
}

// ── Toast notification (replaces alert()) ────────────────────────────────────
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('visible'), 10);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// ── Data Loading ─────────────────────────────────────────────────────────────
async function loadData() {
    try {
        const qRes = await fetch('queue.json?t=' + Date.now());
        if (qRes.ok) { queueData = await qRes.json(); renderQueue(); }

        const hRes = await fetch('history.json?t=' + Date.now());
        if (hRes.ok) { historyData = await hRes.json(); renderHistory(); }
    } catch (e) {
        console.error('Error loading data', e);
    }
}

// ── Render Queue ─────────────────────────────────────────────────────────────
function renderQueue() {
    queueContainer.innerHTML = '';
    queueCount.textContent = queueData.length;

    if (queueData.length === 0) {
        queueContainer.innerHTML = '<div class="tweet-card empty-state">No tweets currently pending.</div>';
        return;
    }

    queueData.forEach(item => {
        const el = document.createElement('div');
        el.className = 'tweet-card';
        el.innerHTML = `
            <div class="tweet-meta">
                <span>Queued: ${new Date(item.created_at).toLocaleTimeString()}</span>
            </div>
            <div class="tweet-source-title">${item.article_title}</div>
            <div class="tweet-text">${item.tweet_text}</div>
            <a href="${item.source_url}" target="_blank" class="source-link">Read Original Article ↗</a>
            <div style="margin-top: 1rem;" class="tweet-actions">
                <span class="countdown" id="cd-${item.id}">Calculating...</span>
                <div class="action-buttons">
                    <button class="btn publish" onclick="attemptPublishNow('${item.id}')">⚡ Publish Now</button>
                    <button class="btn danger" onclick="attemptCancel('${item.id}')">✕ Cancel</button>
                </div>
            </div>
        `;
        queueContainer.appendChild(el);
    });
}

// ── Render History ────────────────────────────────────────────────────────────
function renderHistory() {
    historyContainer.innerHTML = '';

    if (historyData.length === 0) {
        historyContainer.innerHTML = '<div class="tweet-card empty-state">No history yet.</div>';
        return;
    }

    historyData.slice(0, 15).forEach(item => {
        const el = document.createElement('div');
        el.className = 'tweet-card posted';
        el.innerHTML = `
            <div class="tweet-meta">
                <span>Posted: ${new Date(item.posted_at || item.created_at).toLocaleString()}</span>
            </div>
            <div class="tweet-text">${item.tweet_text}</div>
            ${item.posted_tweet_url ? `<a href="${item.posted_tweet_url}" target="_blank" class="source-link">View on X ↗</a>` : ''}
        `;
        historyContainer.appendChild(el);
    });
}

// ── Countdown Timers ──────────────────────────────────────────────────────────
setInterval(() => {
    queueData.forEach(item => {
        const el = document.getElementById(`cd-${item.id}`);
        if (!el) return;
        const diff = new Date(item.scheduled_for).getTime() - Date.now();
        if (diff <= 0) {
            el.textContent = 'Posting soon...';
            el.style.color = 'var(--success)';
        } else {
            const m = Math.floor(diff / 60000);
            const s = Math.floor((diff % 60000) / 1000);
            el.textContent = `Posts in: ${m}m ${s}s`;
        }
    });
}, 1000);

// ── Auth helper ───────────────────────────────────────────────────────────────
function getToken() {
    return localStorage.getItem('gh_token');
}

function requestToken(onSuccess) {
    authModal.classList.add('active');
    authModal.dataset.onSuccess = onSuccess;
}

// ── GitHub API trigger ────────────────────────────────────────────────────────
async function triggerDispatch(eventType, payload, token) {
    const response = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/dispatches`, {
        method: 'POST',
        headers: {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': `token ${token}`
        },
        body: JSON.stringify({ event_type: eventType, client_payload: payload })
    });
    return response.ok;
}

// ── Publish Now ───────────────────────────────────────────────────────────────
async function attemptPublishNow(tweetId) {
    const confirmed = await showConfirm(
        'Publish Now?',
        'Post this tweet to X immediately, skipping the 10-minute window?',
        '⚡ Yes, post it now',
        'publish'
    );
    if (!confirmed) return;

    let token = getToken();
    if (!token) {
        authModal.classList.add('active');
        authModal.dataset.pendingAction = JSON.stringify({ type: 'publish', id: tweetId });
        return;
    }

    const ok = await triggerDispatch('publish-now', { tweet_id: tweetId }, token);
    if (ok) {
        showToast('✅ Publish request sent! Tweet will appear on X shortly.', 'success');
        queueData = queueData.filter(i => i.id !== tweetId);
        renderQueue();
    } else {
        showToast('❌ Failed to publish. Check your GitHub token permissions.', 'error');
        localStorage.removeItem('gh_token');
    }
}

// ── Cancel Tweet ──────────────────────────────────────────────────────────────
async function attemptCancel(tweetId) {
    const confirmed = await showConfirm(
        'Cancel Tweet?',
        'Remove this tweet from the queue permanently. It will not be posted.',
        '✕ Yes, cancel it',
        'danger'
    );
    if (!confirmed) return;

    let token = getToken();
    if (!token) {
        authModal.classList.add('active');
        authModal.dataset.pendingAction = JSON.stringify({ type: 'cancel', id: tweetId });
        return;
    }

    const ok = await triggerDispatch('cancel-tweet', { tweet_id: tweetId }, token);
    if (ok) {
        showToast('🗑 Tweet cancelled and removed from queue.', 'success');
        queueData = queueData.filter(i => i.id !== tweetId);
        renderQueue();
    } else {
        showToast('❌ Failed to cancel. Check your GitHub token permissions.', 'error');
        localStorage.removeItem('gh_token');
    }
}

// ── Auth Modal Handlers ───────────────────────────────────────────────────────
saveTokenBtn.addEventListener('click', async () => {
    const token = ghTokenInput.value.trim();
    if (!token) return;

    localStorage.setItem('gh_token', token);
    authModal.classList.remove('active');
    ghTokenInput.value = '';

    // Resume pending action if any
    const pendingRaw = authModal.dataset.pendingAction;
    if (pendingRaw) {
        delete authModal.dataset.pendingAction;
        const pending = JSON.parse(pendingRaw);
        if (pending.type === 'publish') await attemptPublishNow(pending.id);
        else if (pending.type === 'cancel') await attemptCancel(pending.id);
    }
});

closeModalBtn.addEventListener('click', () => {
    authModal.classList.remove('active');
});

// ── Init ──────────────────────────────────────────────────────────────────────
loadData();
setInterval(loadData, 30000);
