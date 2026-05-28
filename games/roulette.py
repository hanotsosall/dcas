import random
from database import get_user, update_balance, log_transaction

EUROPEAN_NUMBERS = list(range(0, 37))
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def get_color(num):
    if num == 0: return "green"
    return "red" if num in RED else "black"

def spin_roulette(user_id, bet, bet_type, value):
    user = get_user(user_id)
    if not user or user['balance'] < bet:
        return None, 0, user['balance'] if user else 0
    result_num = random.choice(EUROPEAN_NUMBERS)
    result_color = get_color(result_num)
    win = 0
    if bet_type == 'number':
        if result_num == value:
            win = bet * 35
    elif bet_type == 'color':
        if result_color == value:
            win = bet * 2
    elif bet_type == 'evenodd':
        if result_num == 0:
            win = 0
        elif value == 'even' and result_num % 2 == 0:
            win = bet * 2
        elif value == 'odd' and result_num % 2 == 1:
            win = bet * 2
    elif bet_type == 'dozen':
        dozen = (result_num - 1) // 12 if result_num > 0 else -1
        if dozen == value:
            win = bet * 3
    elif bet_type == 'column':
        col = (result_num - 1) % 3 if result_num > 0 else -1
        if col == value:
            win = bet * 3
    delta = win - bet
    new_balance = user['balance'] + delta
    update_balance(user_id, delta)
    log_transaction(user_id, delta, 'roulette', 'roulette')
    result = {'number': result_num, 'color': result_color, 'bet_type': bet_type, 'win': win}
    return result, win, new_balance
