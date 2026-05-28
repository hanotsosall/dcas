import random
import time
import uuid
from database import get_user, update_balance, log_transaction

active_crash_sessions = {}  # session_id -> {user_id, bet, cashed_out, start_time}
global_crash_multiplier = 1.0
crash_running = False
crash_timer = None

def get_crash_status():
    return {'multiplier': global_crash_multiplier, 'running': crash_running}

def start_crash_bet(user_id, bet):
    global crash_running
    user = get_user(user_id)
    if not user or user['balance'] < bet:
        return None, user['balance'] if user else 0, None
    session_id = str(uuid.uuid4())
    active_crash_sessions[session_id] = {
        'user_id': user_id,
        'bet': bet,
        'cashed_out': False,
        'start_time': time.time()
    }
    update_balance(user_id, -bet)
    log_transaction(user_id, -bet, 'crash_bet', 'crash')
    return {'session_id': session_id}, user['balance'] - bet, session_id

def cashout_crash(user_id, session_id):
    sess = active_crash_sessions.get(session_id)
    if not sess or sess['user_id'] != user_id or sess['cashed_out']:
        return None, 0, 0
    sess['cashed_out'] = True
    multiplier = global_crash_multiplier
    win = int(sess['bet'] * multiplier)
    update_balance(user_id, win)
    log_transaction(user_id, win, 'crash_win', 'crash')
    user = get_user(user_id)
    return {'multiplier': multiplier}, win, user['balance']

def update_crash_multiplier():
    global global_crash_multiplier, crash_running
    if not crash_running:
        return
    # Симуляция роста с возможным крашем
    global_crash_multiplier += random.uniform(0.05, 0.25)
    # Вероятность краша увеличивается с ростом множителя
    crash_prob = min(0.02 * global_crash_multiplier, 0.4)
    if random.random() < crash_prob:
        crash_running = False
        global_crash_multiplier = 1.0
        # Очистка сессий – все активные ставки проиграны
        active_crash_sessions.clear()
    # Запланировать следующий тик
    import threading
    threading.Timer(0.5, update_crash_multiplier).start()

def start_crash_round():
    global crash_running, global_crash_multiplier
    crash_running = True
    global_crash_multiplier = 1.0
    update_crash_multiplier()

# Автоматический запуск цикла краша при импорте
import threading
threading.Thread(target=start_crash_round, daemon=True).start()
