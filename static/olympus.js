// ========================
// OLYMPUS GAME – падающие символы
// ========================

const olympCanvas = document.getElementById('olympusCanvas');
const oCtx = olympCanvas?.getContext('2d');
if (olympCanvas) olympCanvas.width = 500, olympCanvas.height = 500;
const CELL_SIZE = 100;

function drawOlympusGrid(grid) {
    if (!oCtx) return;
    oCtx.clearRect(0, 0, 500, 500);
    for (let row = 0; row < 5; row++) {
        for (let col = 0; col < 5; col++) {
            const sym = grid[row][col];
            oCtx.fillStyle = '#2a1a0a';
            oCtx.fillRect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE - 2, CELL_SIZE - 2);
            oCtx.fillStyle = '#ffdd99';
            oCtx.font = '48px "Segoe UI Emoji", "Apple Color Emoji"';
            oCtx.fillText(sym, col * CELL_SIZE + 25, row * CELL_SIZE + 70);
        }
    }
}

async function playOlympus() {
    if (!currentUser) { showNotification('Авторизуйтесь', 'error'); return; }
    let betBtn = document.querySelector('.olympus-bet-btn.active');
    let bet = betBtn ? parseInt(betBtn.getAttribute('data-bet')) : 10;
    if (isNaN(bet)) bet = 10;
    try {
        const res = await fetch('/api/olympus', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bet })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        // Анимация падения (простая: сразу рисуем результат)
        drawOlympusGrid(data.result.grid);
        showNotification(`✨ Выигрыш: ${data.win} самоцветов ✨`, 'win');
        mainBalance = data.balance;
        bonusBalance = data.bonus_balance;
        document.getElementById('mainBalance').innerText = formatNumber(mainBalance);
        document.getElementById('bonusBalance').innerText = formatNumber(bonusBalance);
        if (data.win > 0) {
            const winDiv = document.getElementById('olympusWin');
            winDiv.innerHTML = `🎉 +${data.win} 🎉`;
            setTimeout(() => winDiv.innerHTML = '', 2000);
        }
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

// Инициализация кнопок Olympus
if (document.getElementById('olympusPlayBtn')) {
    document.getElementById('olympusPlayBtn').onclick = playOlympus;
    document.querySelectorAll('.olympus-bet-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.olympus-bet-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        };
    });
    // активируем первую по умолчанию
    document.querySelector('.olympus-bet-btn')?.classList.add('active');
}
