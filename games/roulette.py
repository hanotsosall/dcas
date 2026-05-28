import random
from database import get_db, log_transaction

EUROPEAN = list(range(37))
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def get_color(num):
    if num == 0: return 'green'
    return 'red' if num in RED else 'black'

def spin_roulette(user_id, bet, bet_type, value):
    db = get_db()
    user = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    total = user['balance'] + user['bonus_balance']
    if total < bet:
        return None, 0, user['balance'], user['bonus_balance']
    # Списываем
    from_bonus = min(user['bonus_balance'], bet)
    from_main = bet - from_bonus
    db.execute("UPDATE users SET balance = balance - ?, bonus_balance = bonus_balance - ? WHERE id=?", (from_main, from_bonus, user_id))
    num = random.choice(EUROPEAN)
    col = get_color(num)
    win = 0
    if bet_type == 'number' and num == value:
        win = bet * 35
    elif bet_type == 'color' and col == value:
        win = bet * 2
    elif bet_type == 'evenodd':
        if num != 0 and ((value == 'even' and num%2==0) or (value=='odd' and num%2==1)):
            win = bet * 2
    elif bet_type == 'dozen':
        d = (num-1)//12 if num>0 else -1
        if d == value:
            win = bet * 3
    if win > 0:
        db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (win, user_id))
    db.commit()
    log_transaction(user_id, win if win>0 else -bet, 'roulette', 'roulette')
    new = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    return {'number': num, 'color': col}, win, new['balance'], new['bonus_balance']
