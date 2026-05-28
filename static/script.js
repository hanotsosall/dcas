// ========================
// DRAGON GOD CASINO – ОСНОВНОЙ ФРОНТЕНД
// ========================

// ---------- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ----------
let currentUser = null;
let mainBalance = 0;
let bonusBalance = 0;
let freespinsLeft = 0;
let isSpinning = false;
let crashInterval = null;
let crashActive = false;
let currentCrashSession = null;
let crashBetAmount = 0;
let crashHistory = [];
let currentRouletteBet = null;
let currentRouletteBetType = null;

// ---------- ЭЛЕМЕНТЫ СЛОТОВ ----------
const canvas = document.getElementById('slotCanvas');
const ctx = canvas?.getContext('2d');
const REEL_W = 130;
const SYMB_H = 130;
const REELS = 5;
const ROWS = 3;

// ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
function formatNumber(n) { return Math.floor(n); }

function showNotification(msg, type = 'info') {
    const div = document.createElement('div');
    div.className = `notification ${type}`;
    div.innerText = msg;
    div.style.cssText = `
        position: fixed; bottom: 20px; right: 20px; z-index: 9999;
        background: ${type === 'error' ? '#e74c3c' : (type === 'win' ? '#2ecc71' : '#f39c12')};
        color: black; padding: 12px 24px; border-radius: 40px;
        font-weight: bold; font-family: monospace; box-shadow: 0 0 10px black;
        animation: slideIn 0.3s ease-out;
    `;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 3000);
}

// ---------- МОБИЛЬНОЕ МЕНЮ ----------
const menuToggle = document.getElementById('mobileMenuToggle');
const sidebar = document.getElementById('sidebar');
if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        menuToggle.textContent = sidebar.classList.contains('open') ? '✕' : '☰';
    });
    document.querySelectorAll('.nav-item').forEach(link => {
        link.addEventListener('click', () => {
            sidebar.classList.remove('open');
            if (menuToggle) menuToggle.textContent = '☰';
        });
    });
}

// ---------- ОТРИСОВКА СЛОТОВ ----------
function drawReels(reels) {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let col = 0; col < REELS; col++) {
        for (let row = 0; row < ROWS; row++) {
            const sym = reels[col][row];
            const x = 25 + col * (REEL_W + 10);
            const y = 30 + row * SYMB_H;
            ctx.fillStyle = sym.color;
            ctx.fillRect(x, y, REEL_W - 8, SYMB_H - 10);
            ctx.fillStyle = '#ffffff';
            ctx.font = '52px "Segoe UI Emoji", "Apple Color Emoji"';
            ctx.fillText(sym.name, x + 25, y + 80);
            ctx.font = 'bold 12px monospace';
            ctx.fillStyle = '#000000aa';
            ctx.fillText(sym.name, x + 28, y + 95);
        }
    }
}

async function animateSpin(finalReels) {
    // Анимация падения столбцов с задержкой
    const emptyReels = Array(5).fill().map(() => Array(3).fill({ name: '✨', color: '#555' }));
    drawReels(emptyReels);
    await new Promise(r => setTimeout(r, 100));
    for (let col = 0; col < REELS; col++) {
        for (let step = 0; step < 8; step++) {
            const tempReels = finalReels.map((c, idx) => (idx <= col ? c : emptyReels[idx]));
            drawReels(tempReels);
            await new Promise(r => setTimeout(r, 40));
        }
    }
    drawReels(finalReels);
}

// ---------- АВТОРИЗАЦИЯ ----------
async function login(username, password) {
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        currentUser = data.user;
        mainBalance = data.user.balance;
        bonusBalance = data.user.bonus_balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        document.getElementById('bonusBalance').innerText = formatNumber(bonusBalance);
        document.getElementById('usernameDisplay').innerText = data.user.username;
        document.getElementById('logoutBtn').style.display = 'inline-block';
        document.getElementById('authPage').style.display = 'none';
        document.getElementById('gameArea').style.display = 'block';
        document.getElementById('profileUsername').innerText = data.user.username;
        showNotification(`Добро пожаловать, ${data.user.username}!`, 'win');
        // Пустые барабаны
        const empty = Array(5).fill().map(() => Array(3).fill({ name: '🐉', color: '#9b59b6' }));
        drawReels(empty);
        loadReferralLink();
        loadProfileStats();
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

async function register(username, password, email, ref) {
    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email, ref_code: ref })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        showNotification('Регистрация успешна! Вы автоматически вошли.', 'win');
        login(username, password);
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    location.reload();
}

// ---------- СЛОТЫ ----------
async function spinSlots(bet, isFree = false) {
    if (isSpinning) return;
    if (!currentUser) return;
    const totalBalance = mainBalance + bonusBalance;
    if (!isFree && totalBalance < bet) {
        showNotification('Не хватает самоцветов', 'error');
        return;
    }
    isSpinning = true;
    const spinBtn = document.getElementById('spinBtn');
    if (spinBtn) spinBtn.disabled = true;
    try {
        const res = await fetch('/api/spin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bet, is_freespin: isFree })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        await animateSpin(data.reels);
        mainBalance = data.balance;
        bonusBalance = data.bonus_balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        document.getElementById('bonusBalance').innerText = formatNumber(bonusBalance);
        if (data.win > 0) {
            showNotification(`🎉 ВЫИГРЫШ: ${data.win} 🎉`, 'win');
            if (data.win >= 5000) {
                document.getElementById('winAnimation').innerHTML = '🔥 ДЖЕКПОТ! 🔥';
                setTimeout(() => document.getElementById('winAnimation').innerHTML = '', 2000);
            }
        }
        if (data.bonus_trigger && !isFree) {
            freespinsLeft = 10;
            const counter = document.getElementById('freespinCounter');
            counter.innerHTML = `🐉 БОНУС! Осталось фриспинов: ${freespinsLeft} (x2) 🐉`;
            for (let i = 0; i < freespinsLeft; i++) {
                await new Promise(r => setTimeout(r, 600));
                if (freespinsLeft <= 0) break;
                await spinSlots(0, true);
                freespinsLeft--;
                counter.innerHTML = `🎲 Фриспин x2 | Осталось: ${freespinsLeft}`;
                if (freespinsLeft === 0) counter.innerHTML = '';
            }
        }
    } catch (err) {
        showNotification(err.message, 'error');
    } finally {
        isSpinning = false;
        if (spinBtn) spinBtn.disabled = false;
    }
}

// ---------- РЕФЕРАЛКА ----------
async function loadReferralLink() {
    try {
        const res = await fetch('/api/referral/link');
        const data = await res.json();
        document.getElementById('referralLink').value = data.link;
    } catch (e) {}
}

async function loadProfileStats() {
    if (!currentUser) return;
    try {
        const res = await fetch('/api/user');
        const data = await res.json();
        document.getElementById('profileVip').innerText = data.vip_level || 0;
        document.getElementById('profileTotalWin').innerText = data.total_win || 0;
        document.getElementById('profileTotalBet').innerText = data.total_bet || 0;
    } catch (e) {}
}

// ---------- БОНУС-КОД ----------
async function applyBonusCode() {
    const code = document.getElementById('bonusCodeInput').value.trim();
    if (!code) return showNotification('Введите код', 'error');
    const res = await fetch('/api/bonus/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
    });
    const data = await res.json();
    if (data.error) showNotification(data.error, 'error');
    else {
        showNotification(`+${data.amount} бонусных самоцветов!`, 'win');
        bonusBalance += data.amount;
        document.getElementById('bonusBalance').innerText = formatNumber(bonusBalance);
    }
}

// ---------- НАВИГАЦИЯ ----------
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = item.getAttribute('data-page') + 'Page';
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(pageId).classList.add('active');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            if (pageId === 'roulettePage') initRouletteBoard();
            if (pageId === 'crashPage') updateCrashHistory();
            if (pageId === 'olympusPage' && typeof drawOlympusGrid === 'function') {
                // инициализация олимпа, если пусто
                if (!window.olympusGrid) drawOlympusGrid(Array(5).fill().map(()=>Array(5).fill('⚡')));
            }
        });
    });
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.auth-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(tabName + 'Panel').classList.add('active');
        });
    });
}

// ---------- ПОДКЛЮЧЕНИЕ КНОПОК ----------
document.getElementById('doLoginBtn')?.addEventListener('click', () => {
    login(document.getElementById('loginUsername').value, document.getElementById('loginPassword').value);
});
document.getElementById('doRegBtn')?.addEventListener('click', () => {
    register(
        document.getElementById('regUsername').value,
        document.getElementById('regPassword').value,
        document.getElementById('regEmail').value,
        document.getElementById('regReferral').value
    );
});
document.getElementById('logoutBtn')?.addEventListener('click', logout);
document.getElementById('spinBtn')?.addEventListener('click', () => {
    let bet = parseInt(document.getElementById('customBet').value);
    if (isNaN(bet) || bet < 1) bet = 10;
    spinSlots(bet, false);
});
document.querySelectorAll('.bet-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const val = parseInt(btn.getAttribute('data-bet'));
        if (!isNaN(val)) document.getElementById('customBet').value = val;
    });
});
document.getElementById('applyBonusBtn')?.addEventListener('click', applyBonusCode);
document.getElementById('copyLinkBtn')?.addEventListener('click', () => {
    const inp = document.getElementById('referralLink');
    inp.select();
    document.execCommand('copy');
    showNotification('Ссылка скопирована', 'info');
});

// Запуск навигации
initNavigation();

// Симуляция онлайн-счётчика
setInterval(() => {
    const onlineSpan = document.getElementById('onlineCount');
    if (onlineSpan) {
        let cur = parseInt(onlineSpan.innerText.replace(/,/g, ''));
        if (isNaN(cur)) cur = 1234;
        cur += Math.floor(Math.random() * 5) - 2;
        if (cur < 200) cur = 1234;
        onlineSpan.innerText = cur.toLocaleString();
    }
}, 10000);

console.log('Dragon God Casino – основной скрипт загружен');
