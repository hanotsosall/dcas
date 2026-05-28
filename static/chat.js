let chatInterval = null;

async function loadChatMessages() {
    try {
        const res = await fetch('/api/chat/messages');
        const messages = await res.json();
        const container = document.getElementById('chatMessages');
        if (!container) return;
        container.innerHTML = messages.map(m => `
            <div class="chat-message">
                <span class="chat-name">${escapeHtml(m.username)}</span>
                <span class="chat-time">${new Date(m.created_at).toLocaleTimeString()}</span>
                <div class="chat-text">${escapeHtml(m.message)}</div>
            </div>
        `).join('');
        container.scrollTop = container.scrollHeight;
    } catch(e) {}
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;
    try {
        await fetch('/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        input.value = '';
        loadChatMessages();
    } catch(e) {}
}

function escapeHtml(str) {
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

document.getElementById('chatSendBtn')?.addEventListener('click', sendChatMessage);
document.getElementById('chatInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatMessage();
});
if (document.getElementById('chatMessages')) {
    loadChatMessages();
    chatInterval = setInterval(loadChatMessages, 3000);
}
