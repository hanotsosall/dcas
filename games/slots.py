import random
import json
from database import get_user, update_balance, log_transaction
from utils import AnimationPresets

SLOT_SYMBOLS = AnimationPresets.SLOT_SYMBOLS
WEIGHTS = AnimationPresets.WEIGHTS

PAY_LINES = [
    [(0,0),(1,0),(2,0),(3,0),(4,0)],
    [(0,1),(1,1),(2,1),(3,1),(4,1)],
    [(0,2),(1,2),(2,2),(3,2),(4,2)],
    [(0,0),(1,1),(2,2),(3,1),(4,0)],
    [(0,2),(1,1),(2,0),(3,1),(4,2)]
]

def generate_reels():
    return [[random.choices(SLOT_SYMBOLS, weights=WEIGHTS)[0] for _ in range(3)] for _ in range(5)]

def calculate_win(reels, bet):
    win = 0
    bonus_count = 0
    # Линии: 5 штук
    lines = [
        [(0,0),(1,0),(2,0),(3,0),(4,0)],
        [(0,1),(1,1),(2,1),(3,1),(4,1)],
        [(0,2),(1,2),(2,2),(3,2),(4,2)],
        [(0,0),(1,1),(2,2),(3,1),(4,0)],
        [(0,2),(1,1),(2,0),(3,1),(4,2)]
    ]
    for line in lines:
        first = reels[line[0][0]][line[0][1]]
        if first.get('bonus', False):
            continue
        if all(reels[x][y]['name'] == first['name'] for x,y in line[1:]):
            win += bet * first.get('value', 2)
    # Джекпот за 5 семёрок в центре
    if all(reels[i][1]['name'] == "7️⃣" for i in range(5)):
        win += 5000
    # Бонусные драконы
    for col in reels:
        for sym in col:
            if sym.get('bonus'):
                bonus_count += 1
    return win, bonus_count

def spin_slots(user_id, bet, is_freespin=False):
    user = get_user(user_id)
    if not user:
        return None, 0, 0, False
    if not is_freespin and user['balance'] < bet:
        return None, 0, user['balance'], False
    reels = generate_reels()
    win, bonus_count = calculate_win(reels, bet)
    if is_freespin:
        win *= 2
    delta = win - bet if not is_freespin else win
    new_balance = user['balance'] + delta
    update_balance(user_id, delta)
    log_transaction(user_id, delta, 'bet' if not is_freespin else 'freespin_win', 'slots')
    trigger = bonus_count >= 3 and not is_freespin
    result = {
        'reels': [[{'name': s['name'], 'color': s['color']} for s in col] for col in reels],
        'win': win,
        'bonus_trigger': trigger
    }
    return result, win, new_balance, trigger
