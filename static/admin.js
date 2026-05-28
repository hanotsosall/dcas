async function checkAdmin() {
    try {
        const res = await fetch('/api/user');
        const user = await res.json();
        if (!user.is_admin) {
            alert('Доступ запрещён. Вы не администратор.');
            window.location.href = '/';
        }
    } catch(e) { window.location.href = '/'; }
}

async function loadAdminStats() {
    try {
        const res = await fetch('/api/admin/users');
        const users = await res.json();
        document.getElementById('totalUsers').innerText = users.length;
        let totalBalance = 0, totalBets = 0, totalWins = 0;
        const tbody = document.getElementById('usersTableBody');
        tbody.innerHTML = '';
        users.forEach(u => {
            totalBalance += u.balance;
            totalBets += u.total_bet || 0;
            totalWins += u.total_win || 0;
            const row = tbody.insertRow();
            row.insertCell(0).innerText = u.id;
            row.insertCell(1).innerText = u.username;
            row.insertCell(2).innerText = u.balance;
            row.insertCell(3).innerText = u.vip_level || 0;
            row.insertCell(4).innerText = u.total_bet || 0;
            row.insertCell(5).innerText = u.total_win || 0;
            row.insertCell(6).innerText = u.is_admin ? '✅' : '❌';
            const actionCell = row.insertCell(7);
            const delBtn = document.createElement('button');
            delBtn.innerText = '❌';
            delBtn.style.background = '#e74c3c';
            delBtn.style.border = 'none';
            delBtn.style.borderRadius = '20px';
            delBtn.style.padding = '5px 10px';
            delBtn.style.cursor = 'pointer';
            delBtn.onclick = () => deleteUser(u.id);
            actionCell.appendChild(delBtn);
        });
        document.getElementById('totalBalance').innerText = totalBalance;
        document.getElementById('totalBets').innerText = totalBets;
        document.getElementById('totalWins').innerText = totalWins;
    } catch(e) { console.error(e); }
}

async function deleteUser(userId) {
    if (!confirm('Удалить пользователя?')) return;
    try {
        const res = await fetch(`/api/admin/user/${userId}`, { method: 'DELETE' });
        if (res.ok) loadAdminStats();
        else alert('Ошибка');
    } catch(e) {}
}

async function giveBonus() {
    const username = document.getElementById('bonusUsername').value;
    const amount = parseInt(document.getElementById('bonusAmount').value);
    if (!username || isNaN(amount)) return alert('Заполните поля');
    try {
        const res = await fetch('/api/admin/bonus', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, amount })
        });
        const data = await res.json();
        if (data.error) alert(data.error);
        else { alert('Бонус выдан'); loadAdminStats(); }
    } catch(e) {}
}

async function generateBonusCode() {
    const amount = parseInt(document.getElementById('bonusAmount').value);
    if (isNaN(amount)) return alert('Введите сумму');
    const res = await fetch('/api/admin/generate_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount })
    });
    const data = await res.json();
    if (data.code) {
        document.getElementById('generatedCode').innerHTML = `🎫 Новый бонус-код: <strong>${data.code}</strong> на ${amount} самоцветов`;
    }
}

document.getElementById('refreshBtn')?.addEventListener('click', loadAdminStats);
document.getElementById('giveBonusBtn')?.addEventListener('click', giveBonus);
document.getElementById('generateBonusCodeBtn')?.addEventListener('click', generateBonusCode);

checkAdmin();
loadAdminStats();
