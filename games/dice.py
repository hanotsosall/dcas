import random
from database import get_db

def roll_dice(user_id, bet, prediction, target=50):
    db = get_db()
    user = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    total = user['balance'] + user['bonus_balance']
    if total < bet:
        return None, 0, user['balance'], user['bonus_balance']
    from_bonus = min(user['bonus_balance'], bet)
    from_main = bet - from_bonus
    db.execute("UPDATE users SET balance = balance - ?, bonus_balance = bonus_balance - ? WHERE id=?", (from_main, from_bonus, user_id))
    roll = random.randint(1,100)
    win = 0
    if prediction == 'under' and roll < target:
        win = int(bet * 1.98)
    elif prediction == 'over' and roll > target:
        win = int(bet * 1.98)
    elif prediction == 'number' and roll == target:
        win = bet * 50
    if win > 0:
        db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (win, user_id))
    db.commit()
    new = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    return {'roll': roll}, win, new['balance'], new['bonus_balance']
