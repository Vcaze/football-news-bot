const queueContainer = document.getElementById('queue-container');
const historyContainer = document.getElementById('history-container');
const queueCount = document.getElementById('queue-count');
const authModal = document.getElementById('auth-modal');
const ghTokenInput = document.getElementById('gh-token-input');
const saveTokenBtn = document.getElementById('save-token-btn');
const closeModalBtn = document.getElementById('close-modal-btn');

// Replace this with your actual GitHub username and repository name once hosted!
const GITHUB_OWNER = 'Vcaze';
const GITHUB_REPO = 'football-news-bot';

let queueData = [];
let historyData = [];

// Load data immediately and then every 30 seconds
async function loadData() {
    try {
        // Fetch bypasses cache to get fresh data
        const qRes = await fetch('queue.json?t=' + Date.now());
        if (qRes.ok) {
            queueData = await qRes.json();
            renderQueue();
        }

        const hRes = await fetch('history.json?t=' + Date.now());
        if (hRes.ok) {
            historyData = await hRes.json();
            renderHistory();
        }
    } catch (e) {
        console.error("Error loading data", e);
    }
}

function renderQueue() {
    queueContainer.innerHTML = '';
    queueCount.textContent = queueData.length;

    if (queueData.length === 0) {
        queueContainer.innerHTML = '<div class="tweet-card" style="text-align:center; color: var(--text-muted)">No tweets currently pending.</div>';
        return;
    }

    queueData.forEach(item => {
        const el = document.createElement('div');
        el.className = 'tweet-card';
        el.innerHTML = `
            <div class="tweet-meta">
                <span>Created: ${new Date(item.created_at).toLocaleTimeString()}</span>
                <span>Source: ${item.article_title}</span>
            </div>
            <div class="tweet-text">${item.tweet_text}</div>
            <a href="${item.source_url}" target="_blank" class="source-link">Read Original Article ↗</a>
            <div style="margin-top: 1rem;" class="tweet-actions">
                <span class="countdown" id="cd-${item.id}">Calculating...</span>
                <button class="btn danger" onclick="attemptCancel('${item.id}')">Cancel Tweet</button>
            </div>
        `;
        queueContainer.appendChild(el);
    });
}

function renderHistory() {
    historyContainer.innerHTML = '';

    if (historyData.length === 0) {
        historyContainer.innerHTML = '<div class="tweet-card" style="text-align:center; color: var(--text-muted)">No history yet.</div>';
        return;
    }

    historyData.slice(0, 10).forEach(item => { // Show last 10
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

// Countdown Timer Logic
setInterval(() => {
    queueData.forEach(item => {
        const el = document.getElementById(`cd-${item.id}`);
        if (!el) return;

        const scheduledTime = new Date(item.scheduled_for).getTime();
        const now = new Date().getTime();
        const diff = scheduledTime - now;

        if (diff <= 0) {
            el.textContent = "Processing now...";
            el.style.color = "var(--success)";
        } else {
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            el.textContent = `Posts in: ${minutes}m ${seconds}s`;
        }
    });
}, 1000);

// --- CANCELLATION LOGIC ---

function attemptCancel(tweetId) {
    const token = localStorage.getItem('gh_token');
    if (!token) {
        authModal.classList.add('active');
        // Store the ID we were trying to cancel
        authModal.dataset.pendingCancelId = tweetId;
        return;
    }

    triggerCancelWorkflow(tweetId, token);
}

async function triggerCancelWorkflow(tweetId, token) {
    if (!confirm("Are you sure you want to cancel this tweet? It will be removed from the queue permanently.")) return;

    try {
        const response = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/dispatches`, {
            method: 'POST',
            headers: {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': `token ${token}`
            },
            body: JSON.stringify({
                event_type: 'cancel-tweet',
                client_payload: { tweet_id: tweetId }
            })
        });

        if (response.ok) {
            alert("Cancellation request sent! The queue will update shortly.");
            // Optimistically remove from UI
            queueData = queueData.filter(i => i.id !== tweetId);
            renderQueue();
        } else {
            console.error(await response.text());
            alert("Failed to cancel. Check console or token permissions.");
            localStorage.removeItem('gh_token'); // Might be invalid
        }
    } catch (e) {
        alert("Network error occurred.");
    }
}

// Modal Handlers
saveTokenBtn.addEventListener('click', () => {
    const token = ghTokenInput.value.trim();
    if (token) {
        localStorage.setItem('gh_token', token);
        authModal.classList.remove('active');

        // Resume cancellation if we were interrupting one
        const pendingId = authModal.dataset.pendingCancelId;
        if (pendingId) {
            triggerCancelWorkflow(pendingId, token);
            delete authModal.dataset.pendingCancelId;
        }
    }
});

closeModalBtn.addEventListener('click', () => {
    authModal.classList.remove('active');
});

// Initial Load
loadData();
setInterval(loadData, 30000); // refresh json every 30s
