import random
from database import get_user, update_balance, log_transaction

def roll_dice(user_id, bet, prediction, target=50):
    user = get_user(user_id)
    if not user or user['balance'] < bet:
        return None, 0, user['balance'] if user else 0
    roll = random.randint(1, 100)
    win = 0
    if prediction == 'under':
        if roll < target:
            win = bet * 1.98
    elif prediction == 'over':
        if roll > target:
            win = bet * 1.98
    elif prediction == 'number':
        if roll == target:
            win = bet * 50
    delta = win - bet
    new_balance = user['balance'] + delta
    update_balance(user_id, delta)
    log_transaction(user_id, delta, 'dice', 'dice')
    result = {'roll': roll, 'prediction': prediction, 'target': target, 'win': win}
    return result, win, new_balance
