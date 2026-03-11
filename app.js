const autoContainer = document.getElementById('auto-container');
const manualContainer = document.getElementById('manual-container');
const historyContainer = document.getElementById('history-container');
const autoCount = document.getElementById('auto-count');
const manualCount = document.getElementById('manual-count');

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
        const no = () => { cleanup(); resolve(false); };

        function cleanup() {
            confirmModal.classList.remove('active');
            confirmYesBtn.removeEventListener('click', yes);
            confirmNoBtn.removeEventListener('click', no);
        }

        confirmYesBtn.addEventListener('click', yes);
        confirmNoBtn.addEventListener('click', no);
    });
}

// ── Toast notification ───────────────────────────────────────────────────────
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
        if (qRes.ok) { queueData = await qRes.json(); renderQueues(); }

        const hRes = await fetch('history.json?t=' + Date.now());
        if (hRes.ok) { historyData = await hRes.json(); renderHistory(); }
    } catch (e) {
        console.error('Error loading data', e);
    }
}

// ── Render Queues (Separated) ───────────────────────────────────────────────
function renderQueues() {
    autoContainer.innerHTML = '';
    manualContainer.innerHTML = '';

    const autoItems = queueData.filter(i => i.type === 'auto' || !i.type);
    const manualItems = queueData.filter(i => i.type === 'manual');

    autoCount.textContent = autoItems.length;
    manualCount.textContent = manualItems.length;

    if (autoItems.length === 0) {
        autoContainer.innerHTML = '<div class="tweet-card empty-state">No automatic tweets pending.</div>';
    } else {
        autoItems.forEach(item => autoContainer.appendChild(createTweetCard(item)));
    }

    if (manualItems.length === 0) {
        manualContainer.innerHTML = '<div class="tweet-card empty-state">No review items in pool.</div>';
    } else {
        manualItems.forEach(item => manualContainer.appendChild(createTweetCard(item)));
    }
}

function createTweetCard(item) {
    const el = document.createElement('div');
    el.className = 'tweet-card';
    const isAuto = item.type === 'auto' || !item.type;

    el.innerHTML = `
        <div class="tweet-meta">
            <span>Fetched: ${new Date(item.created_at).toLocaleTimeString()}</span>
        </div>
        <div class="tweet-source-title">${item.article_title}</div>
        <div class="tweet-text">${item.tweet_text}</div>
        <a href="${item.source_url}" target="_blank" class="source-link">Read Original Article ↗</a>
        <div style="margin-top: 1rem;" class="tweet-actions">
            <span class="countdown" id="cd-${item.id}">${isAuto ? 'Posting soon...' : 'Expires soon...'}</span>
            <div class="action-buttons">
                <button class="btn publish" onclick="attemptPublishNow('${item.id}')">⚡ Publish Now</button>
                <button class="btn danger" onclick="attemptCancel('${item.id}')">✕ Cancel</button>
            </div>
        </div>
    `;
    return el;
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

        const isAuto = item.type === 'auto' || !item.type;
        const targetTimeStr = isAuto ? item.scheduled_for : item.expires_at;
        if (!targetTimeStr) {
            el.textContent = isAuto ? 'Posting soon...' : 'Manual Review';
            return;
        }

        const targetTime = new Date(targetTimeStr).getTime();
        const diff = targetTime - Date.now();

        if (diff <= 0) {
            el.textContent = isAuto ? 'Posting now...' : 'Expired (will be removed)';
            el.style.color = isAuto ? 'var(--success)' : 'var(--danger)';
        } else {
            const h = Math.floor(diff / 3600000);
            const m = Math.floor((diff % 3600000) / 60000);
            const s = Math.floor((diff % 60000) / 1000);

            let timeStr = `${m}m ${s}s`;
            if (h > 0) timeStr = `${h}h ${timeStr}`;

            el.textContent = isAuto ? `Posts in: ${timeStr}` : `Expires in: ${timeStr}`;
        }
    });
}, 1000);

// ── API Triggers ──────────────────────────────────────────────────────────────
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

// ── Actions ───────────────────────────────────────────────────────────────────
async function attemptPublishNow(tweetId) {
    const confirmed = await showConfirm(
        'Publish Now?',
        'Post this tweet to X immediately?',
        '⚡ Yes, post it now',
        'publish'
    );
    if (!confirmed) return;

    let token = localStorage.getItem('gh_token');
    if (!token) {
        authModal.classList.add('active');
        authModal.dataset.pendingAction = JSON.stringify({ type: 'publish', id: tweetId });
        return;
    }

    const ok = await triggerDispatch('publish-now', { tweet_id: tweetId }, token);
    if (ok) {
        showToast('✅ Publish request sent!', 'success');
        queueData = queueData.filter(i => i.id !== tweetId);
        renderQueues();
    } else {
        showToast('❌ Failed to publish.', 'error');
        localStorage.removeItem('gh_token');
    }
}

async function attemptCancel(tweetId) {
    const item = queueData.find(i => i.id === tweetId);
    const isManual = item && item.type === 'manual';

    // Only show confirm if it's an 'auto' tweet (to prevent accidents)
    if (!isManual) {
        const confirmed = await showConfirm(
            'Cancel Tweet?',
            'Remove this tweet permanently?',
            '✕ Yes, cancel it',
            'danger'
        );
        if (!confirmed) return;
    }

    let token = localStorage.getItem('gh_token');
    if (!token) {
        authModal.classList.add('active');
        authModal.dataset.pendingAction = JSON.stringify({ type: 'cancel', id: tweetId });
        return;
    }

    const ok = await triggerDispatch('cancel-tweet', { tweet_id: tweetId }, token);
    if (ok) {
        showToast('🗑 Tweet removed.', 'success');
        queueData = queueData.filter(i => i.id !== tweetId);
        renderQueues();
    } else {
        showToast('❌ Failed to cancel.', 'error');
        localStorage.removeItem('gh_token');
    }
}

// ── Auth Modal Handlers ───────────────────────────────────────────────────────
saveTokenBtn.addEventListener('click', async () => {
    const token = ghTokenInput.value.trim();
    if (!token) return;
    localStorage.setItem('gh_token', token);
    authModal.classList.remove('active');
    const pendingRaw = authModal.dataset.pendingAction;
    if (pendingRaw) {
        delete authModal.dataset.pendingAction;
        const pending = JSON.parse(pendingRaw);
        if (pending.type === 'publish') await attemptPublishNow(pending.id);
        else if (pending.type === 'cancel') await attemptCancel(pending.id);
    }
});

closeModalBtn.addEventListener('click', () => authModal.classList.remove('active'));

// ── Init ──────────────────────────────────────────────────────────────────────
loadData();
setInterval(loadData, 30000);
