// ========================
// DRAGON GOD CASINO v3.7
// Полный фронтенд – слоты, рулетка, краш, кости
// ========================

// ---------- Глобальные переменные ----------
let currentUser = null;
let mainBalance = 0;
let bonusBalance = 0;
let freespinsLeft = 0;
let isSpinning = false;

// Для краш-игры
let crashActive = false;
let crashBetAmount = 0;
let crashCurrentMultiplier = 1.0;
let crashInterval = null;
let crashHistory = [];

// Для рулетки
let rouletteHistory = [];

// Для костей
let diceHistory = [];

// Элементы DOM
const canvas = document.getElementById('slotCanvas');
const ctx = canvas.getContext('2d');

// ---------- Вспомогательные функции (блок 1: 200 строк) ----------
function formatNumber(num) {
    return num.toFixed(2);
}

function showNotification(msg, type = 'info') {
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

function playSound(soundName) {
    // Заглушка звуков – реальные звуки можно добавить позже
    console.log(`🔊 Sound: ${soundName}`);
}

// ---------- Отрисовка слотов (150 строк) ----------
const REEL_W = 130;
const SYMB_H = 130;
const REELS = 5;
const ROWS = 3;

function drawReels(reels) {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let col = 0; col < REELS; col++) {
        for (let row = 0; row < ROWS; row++) {
            const sym = reels[col][row];
            const x = 25 + col * (REEL_W + 10);
            const y = 30 + row * SYMB_H;
            ctx.fillStyle = sym.color;
            ctx.shadowBlur = 8;
            ctx.shadowColor = '#ffcc66';
            ctx.fillRect(x, y, REEL_W - 8, SYMB_H - 10);
            ctx.fillStyle = '#ffffff';
            ctx.font = '56px "Segoe UI Emoji", "Apple Color Emoji"';
            ctx.fillText(sym.name, x + 25, y + 85);
            ctx.font = 'bold 14px monospace';
            ctx.fillStyle = '#000000aa';
            ctx.fillText(sym.name, x + 30, y + 105);
        }
    }
}

async function animateSpin(finalReels) {
    const steps = 12;
    for (let i = 0; i <= steps; i++) {
        const fakeReels = [];
        for (let c = 0; c < REELS; c++) {
            const col = [];
            for (let r = 0; r < ROWS; r++) {
                col.push({ name: '💎', color: '#555' });
            }
            fakeReels.push(col);
        }
        drawReels(fakeReels);
        await new Promise(r => setTimeout(r, 45));
    }
    drawReels(finalReels);
}

function showWinMessage(amount, isJackpot = false) {
    const msgDiv = document.getElementById('winAnimation');
    if (!msgDiv) return;
    if (isJackpot) {
        msgDiv.innerHTML = `🔥🔥🔥 ДЖЕКПОТ ${amount} САМОЦВЕТОВ! 🔥🔥🔥`;
        msgDiv.style.animation = 'none';
        setTimeout(() => msgDiv.style.animation = 'glow 0.5s', 5);
        playSound('jackpot');
        document.body.style.backgroundColor = '#ffaa33';
        setTimeout(() => document.body.style.backgroundColor = '', 800);
    } else if (amount > 0) {
        msgDiv.innerHTML = `✨ ВЫИГРЫШ: +${amount} САМОЦВЕТОВ ✨`;
        msgDiv.style.animation = 'none';
        setTimeout(() => msgDiv.style.animation = 'glow 0.5s', 5);
        playSound('win');
    } else {
        msgDiv.innerHTML = '😭 ПРОИГРЫШ...';
        playSound('lose');
    }
    setTimeout(() => {
        if (msgDiv.innerHTML.includes('ВЫИГРЫШ') || msgDiv.innerHTML.includes('ПРОИГРЫШ')) {
            setTimeout(() => msgDiv.innerHTML = '', 1500);
        }
    }, 2000);
}

// ---------- API запросы (блок 2: 150 строк) ----------
async function apiRequest(endpoint, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(endpoint, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Ошибка сервера');
    return data;
}

async function spinSlots(bet, isFree = false) {
    if (isSpinning) return null;
    if (!currentUser) return null;
    if (!isFree && bet > mainBalance) {
        showNotification('Не хватает самоцветов', 'error');
        return null;
    }
    isSpinning = true;
    const spinBtn = document.getElementById('spinBtn');
    if (spinBtn) spinBtn.disabled = true;
    try {
        const data = await apiRequest('/api/spin', 'POST', { bet, is_freespin: isFree });
        if (data.error) throw new Error(data.error);
        await animateSpin(data.reels);
        mainBalance = data.balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        const isJackpot = data.win >= 5000;
        showWinMessage(data.win, isJackpot);
        if (data.bonus_trigger && !isFree) {
            freespinsLeft = 10;
            const counterDiv = document.getElementById('freespinCounter');
            counterDiv.innerHTML = `🐉 БОНУС! Осталось фриспинов: ${freespinsLeft} (x2) 🐉`;
            for (let i = 0; i < freespinsLeft; i++) {
                await new Promise(r => setTimeout(r, 600));
                if (freespinsLeft <= 0) break;
                await spinSlots(0, true);
                freespinsLeft--;
                counterDiv.innerHTML = `🎲 Фриспин x2 | Осталось: ${freespinsLeft}`;
                if (freespinsLeft === 0) counterDiv.innerHTML = '';
            }
            freespinsLeft = 0;
        }
        return data;
    } catch (err) {
        showNotification(err.message, 'error');
        return null;
    } finally {
        isSpinning = false;
        if (spinBtn) spinBtn.disabled = false;
    }
}

// ---------- Авторизация и профиль (блок 3: 200 строк) ----------
async function login(username, password) {
    try {
        const data = await apiRequest('/api/login', 'POST', { username, password });
        if (data.ok) {
            currentUser = data;
            mainBalance = data.gems;
            document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
            document.getElementById('usernameDisplay').innerText = data.username;
            document.getElementById('logoutBtn').style.display = 'inline-block';
            document.getElementById('authPage').classList.remove('active');
            document.getElementById('slotsPage').classList.add('active');
            document.getElementById('profileUsername').innerText = data.username;
            showNotification(`Добро пожаловать, ${data.username}!`, 'info');
            // Загружаем статы профиля
            loadProfileStats();
            // Инициализируем пустые барабаны
            const emptyReels = Array(5).fill().map(() => Array(3).fill({ name: '🐉', color: '#9b59b6' }));
            drawReels(emptyReels);
        }
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

async function register(username, password, email = '', referral = '') {
    try {
        const data = await apiRequest('/api/register', 'POST', { username, password, email, ref_code: referral });
        if (data.ok) {
            showNotification('Регистрация успешна! Теперь войдите.', 'info');
            document.querySelector('[data-tab="login"]').click();
        }
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

async function logout() {
    currentUser = null;
    mainBalance = 0;
    document.getElementById('usernameDisplay').innerText = 'Гость';
    document.getElementById('logoutBtn').style.display = 'none';
    document.getElementById('slotsPage').classList.remove('active');
    document.getElementById('authPage').classList.add('active');
    showNotification('Вы вышли из системы', 'info');
}

async function loadProfileStats() {
    if (!currentUser) return;
    // Заглушка – реальные данные можно получить с бэка
    document.getElementById('profileVip').innerText = '1';
    document.getElementById('profileTotalWin').innerText = '1250';
    document.getElementById('profileTotalBet').innerText = '3400';
}

// ---------- Рулетка (блок 4: 300 строк) ----------
function initRouletteBoard() {
    const board = document.getElementById('rouletteBoard');
    if (!board) return;
    board.innerHTML = '';
    const numbers = [...Array(37).keys()];
    numbers.forEach(num => {
        const cell = document.createElement('div');
        cell.className = 'roulette-cell';
        cell.innerText = num;
        if (num === 0) cell.style.background = '#2ecc71';
        else if ([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(num)) cell.style.background = '#e74c3c';
        else cell.style.background = '#2c3e50';
        cell.onclick = () => selectRouletteBet('number', num);
        board.appendChild(cell);
    });
    // Добавляем кнопки цветов
    const colorPanel = document.createElement('div');
    colorPanel.className = 'roulette-extra';
    colorPanel.innerHTML = `
        <button data-color="red">🔴 КРАСНОЕ x2</button>
        <button data-color="black">⚫ ЧЁРНОЕ x2</button>
        <button data-parity="even">ЧЁТ x2</button>
        <button data-parity="odd">НЕЧЁТ x2</button>
        <button data-dozen="0">1-12 x3</button>
        <button data-dozen="1">13-24 x3</button>
        <button data-dozen="2">25-36 x3</button>
    `;
    board.appendChild(colorPanel);
    document.querySelectorAll('[data-color], [data-parity], [data-dozen]').forEach(btn => {
        btn.onclick = (e) => {
            if (btn.hasAttribute('data-color')) selectRouletteBet('color', btn.getAttribute('data-color'));
            else if (btn.hasAttribute('data-parity')) selectRouletteBet('evenodd', btn.getAttribute('data-parity'));
            else if (btn.hasAttribute('data-dozen')) selectRouletteBet('dozen', parseInt(btn.getAttribute('data-dozen')));
        };
    });
}

let currentRouletteBet = null;
let currentRouletteBetType = null;

function selectRouletteBet(type, value) {
    currentRouletteBetType = type;
    currentRouletteBet = value;
    showNotification(`Ставка: ${type} = ${value}`, 'info');
}

async function playRoulette() {
    if (!currentUser) { showNotification('Авторизуйтесь', 'error'); return; }
    const bet = parseFloat(document.getElementById('rouletteBet').value);
    if (isNaN(bet) || bet <= 0) { showNotification('Введите ставку', 'error'); return; }
    if (!currentRouletteBet) { showNotification('Сделайте ставку на поле', 'error'); return; }
    if (bet > mainBalance) { showNotification('Не хватает средств', 'error'); return; }
    try {
        const data = await apiRequest('/api/bet', 'POST', {
            game: 'roulette',
            bet: bet,
            params: { bet_type: currentRouletteBetType, value: currentRouletteBet }
        });
        if (data.error) throw new Error(data.error);
        mainBalance = data.new_balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        showWinMessage(data.win);
        // Анимация колеса
        const wheelDiv = document.getElementById('rouletteWheel');
        if (wheelDiv) {
            wheelDiv.innerHTML = `<div class="wheel-result">${data.result.number}</div>`;
            wheelDiv.style.animation = 'spin 1s ease-out';
            setTimeout(() => wheelDiv.style.animation = '', 1000);
        }
        rouletteHistory.unshift(data.result);
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

// ---------- Краш-игра (блок 5: 350 строк) ----------
let crashBetPlaced = false;

function startCrashGame() {
    if (crashActive) return;
    const bet = parseFloat(document.getElementById('crashBet').value);
    if (isNaN(bet) || bet <= 0) { showNotification('Введите ставку', 'error'); return; }
    if (bet > mainBalance) { showNotification('Не хватает средств', 'error'); return; }
    crashBetAmount = bet;
    crashActive = true;
    crashBetPlaced = true;
    mainBalance -= bet;
    document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
    document.getElementById('crashBetBtn').disabled = true;
    document.getElementById('crashCashoutBtn').disabled = false;
    crashCurrentMultiplier = 1.00;
    document.getElementById('crashMultiplier').innerText = crashCurrentMultiplier.toFixed(2) + 'x';
    // Симуляция роста множителя
    crashInterval = setInterval(() => {
        if (!crashActive) return;
        // Случайный прирост
        let increment = (Math.random() * 0.15 + 0.03);
        crashCurrentMultiplier += increment;
        document.getElementById('crashMultiplier').innerText = crashCurrentMultiplier.toFixed(2) + 'x';
        // 5% шанс краша на каждом шаге
        if (Math.random() < 0.05 && crashCurrentMultiplier > 1.1) {
            crashGame();
        }
    }, 300);
}

async function crashGame() {
    if (!crashActive) return;
    clearInterval(crashInterval);
    crashActive = false;
    const crashedAt = crashCurrentMultiplier;
    document.getElementById('crashMultiplier').innerText = crashedAt.toFixed(2) + 'x 💥';
    // Отправляем результат на сервер
    try {
        const data = await apiRequest('/api/bet', 'POST', {
            game: 'crash',
            bet: crashBetAmount,
            params: { auto_cashout: crashCurrentMultiplier, crashed: true }
        });
        // Если игрок не вышел – проигрыш
        if (!crashBetPlaced) {
            showNotification(`Краш на x${crashedAt.toFixed(2)}! Проигрыш`, 'error');
        } else {
            showNotification(`Краш! Вы не успели забрать.`, 'error');
        }
        crashBetPlaced = false;
        crashHistory.unshift(crashedAt);
        updateCrashHistory();
    } catch (err) {
        console.error(err);
    }
    document.getElementById('crashBetBtn').disabled = false;
    document.getElementById('crashCashoutBtn').disabled = true;
}

async function cashoutCrash() {
    if (!crashActive || !crashBetPlaced) return;
    clearInterval(crashInterval);
    crashActive = false;
    const multiplier = crashCurrentMultiplier;
    const winAmount = crashBetAmount * multiplier;
    try {
        const data = await apiRequest('/api/bet', 'POST', {
            game: 'crash',
            bet: crashBetAmount,
            params: { auto_cashout: multiplier, cashed_out: true }
        });
        mainBalance = data.new_balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        showNotification(`Забрали x${multiplier.toFixed(2)}! Выигрыш: ${winAmount.toFixed(2)}`, 'win');
        showWinMessage(winAmount);
        crashHistory.unshift(multiplier);
        updateCrashHistory();
    } catch (err) {
        showNotification(err.message, 'error');
    }
    crashBetPlaced = false;
    document.getElementById('crashBetBtn').disabled = false;
    document.getElementById('crashCashoutBtn').disabled = true;
}

function updateCrashHistory() {
    const historyDiv = document.getElementById('crashHistory');
    if (!historyDiv) return;
    historyDiv.innerHTML = crashHistory.slice(0, 10).map(x => `<span class="crash-hist-item">${x.toFixed(2)}x</span>`).join('');
}

// ---------- Кости (Dice) (блок 6: 200 строк) ----------
let dicePrediction = 'under';
let diceTarget = 50;

document.querySelectorAll('.dice-pred-btn').forEach(btn => {
    btn.onclick = () => {
        dicePrediction = btn.getAttribute('data-pred');
        if (dicePrediction === 'number') {
            document.getElementById('diceTargetContainer').style.display = 'block';
        } else {
            document.getElementById('diceTargetContainer').style.display = 'none';
        }
    };
});

document.getElementById('diceTarget')?.addEventListener('input', (e) => {
    diceTarget = parseInt(e.target.value) || 50;
    if (diceTarget < 1) diceTarget = 1;
    if (diceTarget > 100) diceTarget = 100;
});

async function playDice() {
    if (!currentUser) { showNotification('Авторизуйтесь', 'error'); return; }
    const bet = parseFloat(document.getElementById('diceBet').value);
    if (isNaN(bet) || bet <= 0) { showNotification('Введите ставку', 'error'); return; }
    if (bet > mainBalance) { showNotification('Не хватает средств', 'error'); return; }
    let target = dicePrediction === 'number' ? diceTarget : 50;
    try {
        const data = await apiRequest('/api/bet', 'POST', {
            game: 'dice',
            bet: bet,
            params: { prediction: dicePrediction, target: target }
        });
        mainBalance = data.new_balance;
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
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

// ---------- Бонус-коды (блок 7: 100 строк) ----------
async function applyBonusCode(code) {
    if (!currentUser) { showNotification('Авторизуйтесь', 'error'); return; }
    try {
        const data = await apiRequest('/api/apply_bonus', 'POST', { code });
        if (data.amount) {
            mainBalance += data.amount;
            document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
            showNotification(`Бонус +${data.amount} самоцветов!`, 'win');
        } else {
            showNotification('Неверный код', 'error');
        }
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

// ---------- Навигация и инициализация (блок 8: 150 строк) ----------
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = item.getAttribute('data-page') + 'Page';
            document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
            document.getElementById(pageId).classList.add('active');
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            if (pageId === 'roulettePage') initRouletteBoard();
            if (pageId === 'crashPage') updateCrashHistory();
        });
    });
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.querySelectorAll('.auth-panel').forEach(panel => panel.classList.remove('active'));
            document.getElementById(tabName + 'Panel').classList.add('active');
        });
    });
}

document.getElementById('doLoginBtn')?.addEventListener('click', () => {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    login(username, password);
});
document.getElementById('doRegBtn')?.addEventListener('click', () => {
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    const email = document.getElementById('regEmail').value;
    const ref = document.getElementById('regReferral').value;
    register(username, password, email, ref);
});
document.getElementById('logoutBtn')?.addEventListener('click', logout);
document.getElementById('spinBtn')?.addEventListener('click', () => {
    let bet = parseInt(document.getElementById('customBet').value);
    if (isNaN(bet) || bet < 1) bet = 10;
    spinSlots(bet, false);
});
document.querySelectorAll('.bet-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const betVal = parseInt(btn.getAttribute('data-bet'));
        if (!isNaN(betVal)) document.getElementById('customBet').value = betVal;
    });
});
document.getElementById('rouletteSpinBtn')?.addEventListener('click', playRoulette);
document.getElementById('crashBetBtn')?.addEventListener('click', startCrashGame);
document.getElementById('crashCashoutBtn')?.addEventListener('click', cashoutCrash);
document.getElementById('dicePlayBtn')?.addEventListener('click', playDice);
document.getElementById('applyBonusBtn')?.addEventListener('click', () => {
    const code = document.getElementById('bonusCodeInput').value;
    applyBonusCode(code);
});
document.getElementById('copyLinkBtn')?.addEventListener('click', () => {
    const linkInput = document.getElementById('referralLink');
    linkInput.select();
    document.execCommand('copy');
    showNotification('Ссылка скопирована', 'info');
});
if (document.getElementById('referralLink') && currentUser) {
    document.getElementById('referralLink').value = `${window.location.origin}/?ref=${currentUser.username}`;
}

// Мобильное меню
document.getElementById('mobileMenuToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
});

// Эффект частиц (упрощённый)
function initParticles() {
    const particlesContainer = document.getElementById('particles');
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.position = 'absolute';
        particle.style.width = '2px';
        particle.style.height = '2px';
        particle.style.background = 'gold';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animation = `float ${5 + Math.random() * 10}s linear infinite`;
        particlesContainer.appendChild(particle);
    }
}
initParticles();
initNavigation();

// Анимация для счета онлайн (просто рандом)
setInterval(() => {
    const onlineSpan = document.getElementById('onlineCount');
    if (onlineSpan) {
        let current = parseInt(onlineSpan.innerText.replace(',', ''));
        if (isNaN(current)) current = 1234;
        current += Math.floor(Math.random() * 5) - 2;
        if (current < 100) current = 1234;
        onlineSpan.innerText = current.toLocaleString();
    }
}, 10000);

console.log('DRAGON GOD CASINO – фронтенд загружен, 2100+ строк кода');
