let currentUser = null;
let mainBalance = 0;
let freespinsLeft = 0;
let isSpinning = false;

const canvas = document.getElementById('slotCanvas');
const ctx = canvas.getContext('2d');
const REEL_W = 130;
const SYMB_H = 130;
const REELS = 5;
const ROWS = 3;

function formatNumber(num) { return num.toFixed(0); }
function showNotification(msg, type) {
    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.innerText = msg;
    notif.style.position = 'fixed';
    notif.style.bottom = '20px';
    notif.style.right = '20px';
    notif.style.background = type === 'error' ? '#e74c3c' : (type === 'win' ? '#2ecc71' : '#f39c12');
    notif.style.color = 'white';
    notif.style.padding = '12px 24px';
    notif.style.borderRadius = '40px';
    notif.style.zIndex = '9999';
    notif.style.fontWeight = 'bold';
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}

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
            ctx.font = '56px "Segoe UI Emoji"';
            ctx.fillText(sym.name, x + 25, y + 85);
        }
    }
}

async function animateSpin(finalReels) {
    // Показываем пустые барабаны
    const emptyReels = Array(5).fill().map(() => Array(3).fill({ name: '✨', color: '#555' }));
    drawReels(emptyReels);
    await new Promise(r => setTimeout(r, 100));
    // Анимация "падения" каждого столбца с задержкой
    for (let col = 0; col < REELS; col++) {
        for (let step = 0; step < 8; step++) {
            const tempReels = finalReels.map((c, idx) => {
                if (idx <= col) return c;
                return emptyReels[idx];
            });
            drawReels(tempReels);
            await new Promise(r => setTimeout(r, 40));
        }
    }
    drawReels(finalReels);
}

function showWinMessage(amount, isJackpot = false) {
    const msgDiv = document.getElementById('winAnimation');
    if (!msgDiv) return;
    msgDiv.innerHTML = isJackpot ? `🔥🔥🔥 ДЖЕКПОТ ${amount}! 🔥🔥🔥` : `✨ ВЫИГРЫШ: +${amount} ✨`;
    msgDiv.style.animation = 'none';
    setTimeout(() => msgDiv.style.animation = 'glow 0.5s', 5);
    setTimeout(() => { if (msgDiv.innerHTML.includes('ВЫИГРЫШ')) msgDiv.innerHTML = ''; }, 2000);
}

async function spinSlots(bet, isFree = false) {
    if (isSpinning) return;
    if (!currentUser) return;
    if (!isFree && bet > mainBalance) { showNotification('Не хватает', 'error'); return; }
    isSpinning = true;
    const spinBtn = document.getElementById('spinBtn');
    spinBtn.disabled = true;
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
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        showWinMessage(data.win, data.win >= 5000);
        if (data.bonus_trigger && !isFree) {
            freespinsLeft = 10;
            const counter = document.getElementById('freespinCounter');
            counter.innerHTML = `🐉 БОНУС! Осталось фриспинов: ${freespinsLeft} (x2)`;
            for (let i = 0; i < freespinsLeft; i++) {
                await new Promise(r => setTimeout(r, 600));
                if (freespinsLeft <= 0) break;
                await spinSlots(0, true);
                freespinsLeft--;
                counter.innerHTML = `🎲 Фриспин x2 | Осталось: ${freespinsLeft}`;
                if (freespinsLeft === 0) counter.innerHTML = '';
            }
        }
    } catch (err) { showNotification(err.message, 'error'); }
    finally { isSpinning = false; spinBtn.disabled = false; }
}
// ========== АВТОРИЗАЦИЯ ==========
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
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        document.getElementById('usernameDisplay').innerText = data.user.username;
        document.getElementById('logoutBtn').style.display = 'inline-block';
        document.getElementById('authPage').classList.remove('active');
        document.getElementById('slotsPage').classList.add('active');
        document.querySelector('.nav-item[data-page="slots"]').classList.add('active');
        document.getElementById('profileUsername').innerText = data.user.username;
        showNotification(`Добро пожаловать, ${data.user.username}!`, 'info');
        const emptyReels = Array(5).fill().map(() => Array(3).fill({ name: '🐉', color: '#9b59b6' }));
        drawReels(emptyReels);
        loadProfileStats();
        loadReferralLink();
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

async function register(username, password, email, referral) {
    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email, ref_code: referral })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        showNotification('Регистрация успешна! Вы автоматически вошли.', 'win');
        currentUser = data.user;
        mainBalance = data.user.balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        document.getElementById('usernameDisplay').innerText = data.user.username;
        document.getElementById('logoutBtn').style.display = 'inline-block';
        document.getElementById('authPage').classList.remove('active');
        document.getElementById('slotsPage').classList.add('active');
        document.getElementById('profileUsername').innerText = data.user.username;
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    currentUser = null;
    mainBalance = 0;
    document.getElementById('usernameDisplay').innerText = 'Гость';
    document.getElementById('logoutBtn').style.display = 'none';
    document.getElementById('slotsPage').classList.remove('active');
    document.getElementById('authPage').classList.add('active');
    showNotification('Вы вышли', 'info');
}

// ========== РУЛЕТКА ==========
let currentRouletteBet = null;
let currentRouletteBetType = null;

function initRouletteBoard() {
    const board = document.getElementById('rouletteBoard');
    if (!board) return;
    board.innerHTML = '';
    for (let i = 0; i <= 36; i++) {
        const cell = document.createElement('div');
        cell.className = 'roulette-cell';
        cell.innerText = i;
        if (i === 0) cell.style.background = '#2ecc71';
        else if ([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(i)) cell.style.background = '#e74c3c';
        else cell.style.background = '#2c3e50';
        cell.onclick = (function(num) { return () => selectRouletteBet('number', num); })(i);
        board.appendChild(cell);
    }
    const extras = document.createElement('div');
    extras.className = 'roulette-extras';
    extras.innerHTML = `
        <button data-color="red">🔴 КРАСНОЕ (x2)</button>
        <button data-color="black">⚫ ЧЁРНОЕ (x2)</button>
        <button data-parity="even">ЧЁТ (x2)</button>
        <button data-parity="odd">НЕЧЁТ (x2)</button>
        <button data-dozen="0">1-12 (x3)</button>
        <button data-dozen="1">13-24 (x3)</button>
        <button data-dozen="2">25-36 (x3)</button>
    `;
    board.appendChild(extras);
    document.querySelectorAll('[data-color]').forEach(btn => {
        btn.onclick = () => selectRouletteBet('color', btn.getAttribute('data-color'));
    });
    document.querySelectorAll('[data-parity]').forEach(btn => {
        btn.onclick = () => selectRouletteBet('evenodd', btn.getAttribute('data-parity'));
    });
    document.querySelectorAll('[data-dozen]').forEach(btn => {
        btn.onclick = () => selectRouletteBet('dozen', parseInt(btn.getAttribute('data-dozen')));
    });
}

function selectRouletteBet(type, value) {
    currentRouletteBetType = type;
    currentRouletteBet = value;
    showNotification(`Ставка: ${type} = ${value}`, 'info');
}

async function playRoulette() {
    if (!currentUser) { showNotification('Авторизуйтесь', 'error'); return; }
    const bet = parseInt(document.getElementById('rouletteBet').value);
    if (isNaN(bet) || bet <= 0) { showNotification('Введите ставку', 'error'); return; }
    if (!currentRouletteBet) { showNotification('Сделайте ставку на поле', 'error'); return; }
    if (bet > mainBalance) { showNotification('Не хватает средств', 'error'); return; }
    try {
        const res = await fetch('/api/roulette', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bet, bet_type: currentRouletteBetType, value: currentRouletteBet })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        mainBalance = data.balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        showWinMessage(data.win);
        const wheel = document.getElementById('rouletteWheel');
        wheel.innerHTML = `<div class="wheel-result">${data.result.number}</div>`;
        wheel.style.animation = 'spin 0.8s ease-out';
        setTimeout(() => wheel.style.animation = '', 800);
        if (data.win > 0) showNotification(`Выигрыш ${data.win}!`, 'win');
        else showNotification(`Выпало ${data.result.number} – проигрыш`, 'error');
    } catch (err) { showNotification(err.message, 'error'); }
}

// ========== КРАШ ==========
let crashActive = false;
let crashBetAmount = 0;
let crashCurrentMultiplier = 1.0;
let crashInterval = null;
let crashHistory = [];

async function updateCrashStatus() {
    try {
        const res = await fetch('/api/crash/status');
        const data = await res.json();
        if (data.running) {
            document.getElementById('crashMultiplier').innerText = data.multiplier.toFixed(2) + 'x';
            crashCurrentMultiplier = data.multiplier;
        } else {
            document.getElementById('crashMultiplier').innerText = '💥 CRASHED 💥';
        }
    } catch (e) {}
}

async function startCrashBet() {
    if (!currentUser) { showNotification('Авторизуйтесь', 'error'); return; }
    const bet = parseInt(document.getElementById('crashBet').value);
    if (isNaN(bet) || bet <= 0) { showNotification('Введите ставку', 'error'); return; }
    if (bet > mainBalance) { showNotification('Не хватает средств', 'error'); return; }
    try {
        const res = await fetch('/api/crash/bet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bet })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        mainBalance = data.balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        crashActive = true;
        crashBetAmount = bet;
        window.currentCrashSession = data.session_id;
        document.getElementById('crashBetBtn').disabled = true;
        document.getElementById('crashCashoutBtn').disabled = false;
        crashCurrentMultiplier = 1.0;
        document.getElementById('crashMultiplier').innerText = '1.00x';
        if (crashInterval) clearInterval(crashInterval);
        crashInterval = setInterval(() => {
            if (!crashActive) return;
            updateCrashStatus();
        }, 300);
    } catch (err) { showNotification(err.message, 'error'); }
}

async function cashoutCrash() {
    if (!crashActive) return;
    try {
        const res = await fetch('/api/crash/cashout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: window.currentCrashSession })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        mainBalance = data.balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        showWinMessage(data.win);
        crashHistory.unshift(crashCurrentMultiplier);
        updateCrashHistory();
        crashActive = false;
        clearInterval(crashInterval);
        document.getElementById('crashBetBtn').disabled = false;
        document.getElementById('crashCashoutBtn').disabled = true;
    } catch (err) { showNotification(err.message, 'error'); }
}

function updateCrashHistory() {
    const historyDiv = document.getElementById('crashHistory');
    if (!historyDiv) return;
    historyDiv.innerHTML = crashHistory.slice(0, 15).map(x => `<span class="crash-hist-item">${x.toFixed(2)}x</span>`).join('');
}

// ========== КОСТИ (DICE) ==========
let dicePrediction = 'under';
let diceTarget = 50;

function initDice() {
    document.querySelectorAll('.dice-pred-btn').forEach(btn => {
        btn.onclick = () => {
            dicePrediction = btn.getAttribute('data-pred');
            document.getElementById('diceTargetContainer').style.display = dicePrediction === 'number' ? 'block' : 'none';
        };
    });
    document.getElementById('diceTarget')?.addEventListener('input', (e) => {
        diceTarget = parseInt(e.target.value) || 50;
        if (diceTarget < 1) diceTarget = 1;
        if (diceTarget > 100) diceTarget = 100;
    });
}

async function playDice() {
    if (!currentUser) { showNotification('Авторизуйтесь', 'error'); return; }
    const bet = parseInt(document.getElementById('diceBet').value);
    if (isNaN(bet) || bet <= 0) { showNotification('Введите ставку', 'error'); return; }
    if (bet > mainBalance) { showNotification('Не хватает средств', 'error'); return; }
    const target = dicePrediction === 'number' ? diceTarget : 50;
    try {
        const res = await fetch('/api/dice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bet, prediction: dicePrediction, target })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        mainBalance = data.balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        const roll = data.result.roll;
        document.getElementById('diceResult').innerHTML = `🎲 ${roll}`;
        if (data.win > 0) {
            showWinMessage(data.win);
            document.getElementById('diceResult').style.animation = 'bounce 0.5s';
            setTimeout(() => document.getElementById('diceResult').style.animation = '', 500);
        } else {
            showNotification(`Выпало ${roll} – проигрыш`, 'error');
        }
    } catch (err) { showNotification(err.message, 'error'); }
}

// ========== ПРОФИЛЬ И РЕФЕРАЛЫ ==========
async function loadProfileStats() {
    if (!currentUser) return;
    const res = await fetch('/api/user');
    const data = await res.json();
    if (data.id) {
        document.getElementById('profileVip').innerText = data.vip_level || 0;
        document.getElementById('profileTotalWin').innerText = data.total_win || 0;
        document.getElementById('profileTotalBet').innerText = data.total_bet || 0;
    }
}

async function loadReferralLink() {
    if (!currentUser) return;
    const res = await fetch('/api/referral/link');
    const data = await res.json();
    document.getElementById('referralLink').value = data.link;
}

async function applyBonusCode() {
    const code = document.getElementById('bonusCodeInput').value;
    if (!code) { showNotification('Введите код', 'error'); return; }
    const res = await fetch('/api/bonus/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
    });
    const data = await res.json();
    if (data.error) showNotification(data.error, 'error');
    else {
        showNotification(`+${data.amount} самоцветов!`, 'win');
        mainBalance += data.amount;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
    }
}

// ========== НАВИГАЦИЯ ==========
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
            if (pageId === 'dicePage') initDice();
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

// ========== КНОПКИ ==========
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
document.getElementById('rouletteSpinBtn')?.addEventListener('click', playRoulette);
document.getElementById('crashBetBtn')?.addEventListener('click', startCrashBet);
document.getElementById('crashCashoutBtn')?.addEventListener('click', cashoutCrash);
document.getElementById('dicePlayBtn')?.addEventListener('click', playDice);
document.getElementById('applyBonusBtn')?.addEventListener('click', applyBonusCode);
document.getElementById('copyLinkBtn')?.addEventListener('click', () => {
    const inp = document.getElementById('referralLink');
    inp.select();
    document.execCommand('copy');
    showNotification('Ссылка скопирована', 'info');
});

// ========== ЗАПУСК ==========
initNavigation();
setInterval(() => {
    const onlineSpan = document.getElementById('onlineCount');
    if (onlineSpan) {
        let cur = parseInt(onlineSpan.innerText.replace(/,/g, ''));
        if (isNaN(cur)) cur = 1234;
        cur += Math.floor(Math.random() * 6) - 2;
        if (cur < 200) cur = 1234;
        onlineSpan.innerText = cur.toLocaleString();
    }
}, 10000);

// Мобильное меню
const menuToggle = document.getElementById('mobileMenuToggle');
const sidebar = document.getElementById('sidebar');
if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        menuToggle.textContent = sidebar.classList.contains('open') ? '✕' : '☰';
    });
    // Закрыть при клике на ссылку
    document.querySelectorAll('.nav-item').forEach(link => {
        link.addEventListener('click', () => {
            sidebar.classList.remove('open');
            menuToggle.textContent = '☰';
        });
    });
}
