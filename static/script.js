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
    for (let i = 0; i <= 12; i++) {
        const fake = Array(5).fill().map(() => Array(3).fill({ name: '💎', color: '#555' }));
        drawReels(fake);
        await new Promise(r => setTimeout(r, 45));
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
// Остальные функции (login, register, roulette, crash, dice) в следующих сообщениях
