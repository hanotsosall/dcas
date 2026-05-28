// Дополнительные анимации для всех игр
function addParticles(x, y, color) {
    const particlesContainer = document.getElementById('particles');
    for (let i = 0; i < 20; i++) {
        const p = document.createElement('div');
        p.style.position = 'absolute';
        p.style.left = x + 'px';
        p.style.top = y + 'px';
        p.style.width = '4px';
        p.style.height = '4px';
        p.style.background = color;
        p.style.borderRadius = '50%';
        p.style.pointerEvents = 'none';
        p.style.zIndex = '9999';
        p.style.animation = `particleFly ${Math.random() * 0.8 + 0.5}s ease-out forwards`;
        document.body.appendChild(p);
        setTimeout(() => p.remove(), 800);
    }
}

// Вспышка при джекпоте
function jackpotFlash() {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = 0;
    overlay.style.left = 0;
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(255,215,0,0.6)';
    overlay.style.zIndex = '9998';
    overlay.style.pointerEvents = 'none';
    overlay.style.animation = 'fadeOut 0.5s forwards';
    document.body.appendChild(overlay);
    setTimeout(() => overlay.remove(), 500);
}

// Анимация вращения рулетки
const styleSheet = document.createElement("style");
styleSheet.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(1080deg); }
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-30px); }
    }
    @keyframes particleFly {
        0% { transform: translate(0, 0) scale(1); opacity: 1; }
        100% { transform: translate(${Math.random() * 200 - 100}px, ${Math.random() * 200 - 100}px) scale(0); opacity: 0; }
    }
    @keyframes fadeOut {
        0% { opacity: 1; }
        100% { opacity: 0; }
    }
    .roulette-wheel {
        position: relative;
        width: 200px;
        height: 200px;
        margin: 20px auto;
        background: radial-gradient(circle, #2c3e50, #1a1a2a);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        font-weight: bold;
        border: 3px solid gold;
    }
    .crash-hist-item {
        display: inline-block;
        background: #2a1a0a;
        padding: 5px 12px;
        margin: 5px;
        border-radius: 20px;
        font-family: monospace;
        font-weight: bold;
    }
    .notification {
        animation: slideIn 0.3s ease-out;
    }
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(styleSheet);

// Эффект конфетти для больших выигрышей
function confetti() {
    const colors = ['#ffaa33', '#ff6600', '#ffcc00', '#ffffff'];
    for (let i = 0; i < 100; i++) {
        const conf = document.createElement('div');
        conf.style.position = 'fixed';
        conf.style.width = '8px';
        conf.style.height = '8px';
        conf.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        conf.style.left = Math.random() * window.innerWidth + 'px';
        conf.style.top = '-10px';
        conf.style.zIndex = '10000';
        conf.style.pointerEvents = 'none';
        conf.style.animation = `fall ${Math.random() * 2 + 1}s linear forwards`;
        document.body.appendChild(conf);
        setTimeout(() => conf.remove(), 3000);
    }
}

const confettiStyle = document.createElement('style');
confettiStyle.textContent = `
    @keyframes fall {
        0% { transform: translateY(0) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
`;
document.head.appendChild(confettiStyle);

window.jackpotFlash = jackpotFlash;
window.confetti = confetti;
window.addParticles = addParticles;
