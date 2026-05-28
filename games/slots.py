import random
from database import get_db, update_balance, log_transaction

SYMBOLS = [
    {"name": "🍒", "color": "#e74c3c", "value": 5, "bonus": False},
    {"name": "🍋", "color": "#f1c40f", "value": 4, "bonus": False},
    {"name": "🍊", "color": "#e67e22", "value": 6, "bonus": False},
    {"name": "🍉", "color": "#2ecc71", "value": 8, "bonus": False},
    {"name": "💎", "color": "#1abc9c", "value": 15, "bonus": False},
    {"name": "7️⃣", "color": "#f39c12", "value": 25, "bonus": False},
    {"name": "🐉", "color": "#9b59b6", "value": 0, "bonus": True}
]
WEIGHTS = [18, 16, 14, 10, 6, 4, 2]  # дракон редко

def generate_reels():
    return [[random.choices(SYMBOLS, weights=WEIGHTS)[0] for _ in range(3)] for _ in range(5)]

def calculate_win_and_bonus(reels, bet):
    win = 0
    bonus_count = 0
    lines = [
        [(0,0),(1,0),(2,0),(3,0),(4,0)],
        [(0,1),(1,1),(2,1),(3,1),(4,1)],
        [(0,2),(1,2),(2,2),(3,2),(4,2)],
        [(0,0),(1,1),(2,2),(3,1),(4,0)],
        [(0,2),(1,1),(2,0),(3,1),(4,2)]
    ]
    for line in lines:
        first = reels[line[0][0]][line[0][1]]
        if first['bonus']:
            continue
        if all(reels[x][y]['name'] == first['name'] for x,y in line[1:]):
            win += bet * first['value']
    # Джекпот: 5 семёрок в центре
    if all(reels[i][1]['name'] == "7️⃣" for i in range(5)):
        win += 5000
    # Бонусные драконы
    for col in reels:
        for sym in col:
            if sym.get('bonus'):
                bonus_count += 1
    return win, bonus_count

def spin_slots(user_id, bet, is_freespin=False):
    db = get_db()
    user = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    total = user['balance'] + user['bonus_balance']
    if not is_freespin and total < bet:
        return None, 0, user['balance'], user['bonus_balance'], False
    # Списываем ставку (сначала бонусный баланс)
    if not is_freespin:
        from_bonus = min(user['bonus_balance'], bet)
        from_main = bet - from_bonus
        db.execute("UPDATE users SET balance = balance - ?, bonus_balance = bonus_balance - ? WHERE id=?", (from_main, from_bonus, user_id))
    reels = generate_reels()
    win, bonus_count = calculate_win_and_bonus(reels, bet)
    if is_freespin:
        win *= 2
    # Начисляем выигрыш на основной баланс
    if win > 0:
        db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (win, user_id))
    db.commit()
    log_transaction(user_id, win if not is_freespin else win, 'win' if win>0 else 'bet', 'slots')
    new_user = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    trigger_bonus = (bonus_count >= 3) and not is_freespin
    result = {
        'reels': [[{'name': s['name'], 'color': s['color']} for s in col] for col in reels],
        'win': win,
        'bonus_trigger': trigger_bonus
    }
    return result, win, new_user['balance'], new_user['bonus_balance'], trigger_bonus
