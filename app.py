import os
import sqlite3
import bcrypt
import random
import json
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, g, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dragon_god_key_2025')
app.permanent_session_lifetime = timedelta(days=7)

# ---------- БД ----------
DATABASE = 'casino.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            balance INTEGER DEFAULT 0,
            bonus_balance INTEGER DEFAULT 0,
            vip_level INTEGER DEFAULT 0,
            total_bet INTEGER DEFAULT 0,
            total_win INTEGER DEFAULT 0,
            referrer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            is_admin BOOLEAN DEFAULT 0
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            game TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS spin_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game TEXT,
            bet INTEGER,
            win INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS bonus_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            amount INTEGER,
            used_by INTEGER,
            expires_at TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            commission INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()
        # Создать админа если нет
        admin = cursor.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not admin:
            hashed = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            cursor.execute("INSERT INTO users (username, password, is_admin, balance) VALUES (?, ?, ?, ?)",
                           ('admin', hashed, 1, 1000000))
            db.commit()
init_db()

# ---------- Декораторы ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        db = get_db()
        user = db.execute("SELECT is_admin FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if not user or not user['is_admin']:
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated

# ---------- Вспомогательные функции ----------
def generate_bonus_code(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def update_balance(user_id, delta, is_bonus=False):
    db = get_db()
    if is_bonus:
        db.execute("UPDATE users SET bonus_balance = bonus_balance + ? WHERE id=?", (delta, user_id))
    else:
        db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (delta, user_id))
    db.commit()

def log_transaction(user_id, amount, type, game=None):
    db = get_db()
    db.execute("INSERT INTO transactions (user_id, amount, type, game) VALUES (?,?,?,?)",
               (user_id, amount, type, game))
    db.commit()

# ---------- Маршруты ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '')
    ref = data.get('ref_code', '')
    if not username or not password:
        return jsonify({'error': 'Заполните все поля'})
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if existing:
        return jsonify({'error': 'Имя уже занято'})
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    referrer_id = None
    if ref:
        ref_user = db.execute("SELECT id FROM users WHERE username=?", (ref,)).fetchone()
        if ref_user:
            referrer_id = ref_user['id']
    cursor = db.execute(
        "INSERT INTO users (username, password, email, referrer_id, bonus_balance) VALUES (?,?,?,?,?)",
        (username, hashed, email, referrer_id, 5000)
    )
    db.commit()
    user_id = cursor.lastrowid
    if referrer_id:
        db.execute("UPDATE users SET balance = balance + 100 WHERE id=?", (referrer_id,))
        db.execute("INSERT INTO referrals (referrer_id, referred_id, commission) VALUES (?,?,?)",
                   (referrer_id, user_id, 100))
        db.commit()
    # Автовход
    session.permanent = True
    session['user_id'] = user_id
    session['username'] = username
    return jsonify({'ok': True, 'user': {'id': user_id, 'username': username, 'balance': 0, 'bonus_balance': 5000}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    db = get_db()
    user = db.execute("SELECT id, username, password, balance, bonus_balance, is_admin FROM users WHERE username=?", (username,)).fetchone()
    if not user or not bcrypt.checkpw(password.encode(), user['password'].encode()):
        return jsonify({'error': 'Неверные данные'}), 401
    session.permanent = True
    session['user_id'] = user['id']
    session['username'] = user['username']
    db.execute("UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id=?", (user['id'],))
    db.commit()
    return jsonify({'ok': True, 'user': {
        'id': user['id'], 'username': user['username'],
        'balance': user['balance'], 'bonus_balance': user['bonus_balance'],
        'is_admin': user['is_admin']
    }})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/user')
def get_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged'}), 401
    db = get_db()
    user = db.execute("SELECT id, username, balance, bonus_balance, vip_level, total_bet, total_win, is_admin FROM users WHERE id=?", (session['user_id'],)).fetchone()
    return jsonify(dict(user))

# ---------- Слоты ----------
@app.route('/api/spin', methods=['POST'])
@login_required
def api_spin():
    from games.slots import spin_slots
    data = request.json
    bet = int(data.get('bet', 10))
    is_free = data.get('is_freespin', False)
    result, win, new_balance, new_bonus, bonus_trigger = spin_slots(session['user_id'], bet, is_free)
    if result is None:
        return jsonify({'error': 'Недостаточно средств'}), 400
    return jsonify({
        'reels': result['reels'],
        'win': win,
        'balance': new_balance,
        'bonus_balance': new_bonus,
        'bonus_trigger': bonus_trigger,
        'freespins_left': 10 if bonus_trigger else 0
    })

# ---------- Рулетка ----------
@app.route('/api/roulette', methods=['POST'])
@login_required
def api_roulette():
    from games.roulette import spin_roulette
    data = request.json
    bet = int(data.get('bet', 10))
    bet_type = data.get('bet_type')
    value = data.get('value')
    result, win, new_balance, new_bonus = spin_roulette(session['user_id'], bet, bet_type, value)
    if result is None:
        return jsonify({'error': 'Недостаточно средств'}), 400
    return jsonify({'result': result, 'win': win, 'balance': new_balance, 'bonus_balance': new_bonus})

# ---------- Краш ----------
# (упрощённая версия без фонового потока, для стабильности)
crash_multiplier = 1.0
crash_running = True
crash_bets = {}  # session_id -> {user_id, bet, cashed_out}

@app.route('/api/crash/status')
def crash_status():
    return jsonify({'multiplier': crash_multiplier, 'running': crash_running})

@app.route('/api/crash/bet', methods=['POST'])
@login_required
def api_crash_bet():
    global crash_multiplier, crash_running
    data = request.json
    bet = int(data.get('bet', 10))
    db = get_db()
    user = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (session['user_id'],)).fetchone()
    total = user['balance'] + user['bonus_balance']
    if total < bet:
        return jsonify({'error': 'Не хватает'}), 400
    # Списываем сначала бонусный баланс
    from_bonus = min(user['bonus_balance'], bet)
    from_main = bet - from_bonus
    if from_bonus:
        db.execute("UPDATE users SET bonus_balance = bonus_balance - ? WHERE id=?", (from_bonus, session['user_id']))
    if from_main:
        db.execute("UPDATE users SET balance = balance - ? WHERE id=?", (from_main, session['user_id']))
    db.commit()
    import uuid
    sid = str(uuid.uuid4())
    crash_bets[sid] = {'user_id': session['user_id'], 'bet': bet, 'cashed_out': False, 'from_bonus': from_bonus, 'from_main': from_main}
    return jsonify({'session_id': sid, 'balance': user['balance'] - from_main, 'bonus_balance': user['bonus_balance'] - from_bonus})

@app.route('/api/crash/cashout', methods=['POST'])
@login_required
def api_crash_cashout():
    global crash_multiplier
    data = request.json
    sid = data.get('session_id')
    bet_info = crash_bets.get(sid)
    if not bet_info or bet_info['cashed_out'] or bet_info['user_id'] != session['user_id']:
        return jsonify({'error': 'Неверная сессия'}), 400
    bet_info['cashed_out'] = True
    win_amount = int(bet_info['bet'] * crash_multiplier)
    # Возвращаем выигрыш на основной баланс
    db = get_db()
    db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (win_amount, session['user_id']))
    db.commit()
    return jsonify({'win': win_amount})

# ---------- Кости ----------
@app.route('/api/dice', methods=['POST'])
@login_required
def api_dice():
    from games.dice import roll_dice
    data = request.json
    bet = int(data.get('bet', 10))
    prediction = data.get('prediction')
    target = int(data.get('target', 50))
    result, win, new_balance, new_bonus = roll_dice(session['user_id'], bet, prediction, target)
    if result is None:
        return jsonify({'error': 'Недостаточно средств'}), 400
    return jsonify({'result': result, 'win': win, 'balance': new_balance, 'bonus_balance': new_bonus})

# ---------- Бонус-коды ----------
@app.route('/api/bonus/apply', methods=['POST'])
@login_required
def apply_bonus():
    data = request.json
    code = data.get('code', '').upper()
    db = get_db()
    bonus = db.execute("SELECT id, amount, expires_at FROM bonus_codes WHERE code=? AND used_by IS NULL", (code,)).fetchone()
    if not bonus:
        return jsonify({'error': 'Неверный код'}), 400
    if datetime.now() > datetime.fromisoformat(bonus['expires_at']):
        return jsonify({'error': 'Код истёк'}), 400
    db.execute("UPDATE bonus_codes SET used_by=? WHERE id=?", (session['user_id'], bonus['id']))
    db.execute("UPDATE users SET bonus_balance = bonus_balance + ? WHERE id=?", (bonus['amount'], session['user_id']))
    db.commit()
    return jsonify({'ok': True, 'amount': bonus['amount']})

# ---------- Рефералка ----------
@app.route('/api/referral/link')
@login_required
def referral_link():
    username = session['username']
    base_url = request.host_url.rstrip('/')
    return jsonify({'link': f"{base_url}/?ref={username}"})

@app.route('/api/referral/stats')
@login_required
def referral_stats():
    db = get_db()
    count = db.execute("SELECT COUNT(*) as cnt FROM users WHERE referrer_id=?", (session['user_id'],)).fetchone()['cnt']
    earnings = db.execute("SELECT SUM(commission) as sum FROM referrals WHERE referrer_id=?", (session['user_id'],)).fetchone()['sum'] or 0
    return jsonify({'count': count, 'earnings': earnings})

# ---------- Чат ----------
@app.route('/api/chat/messages', methods=['GET'])
def get_messages():
    db = get_db()
    msgs = db.execute("SELECT username, message, created_at FROM chat_messages ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify([dict(m) for m in msgs][::-1])

@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'error': 'Пустое сообщение'}), 400
    db = get_db()
    db.execute("INSERT INTO chat_messages (user_id, username, message) VALUES (?, ?, ?)",
               (session['user_id'], session['username'], msg[:200]))
    db.commit()
    return jsonify({'ok': True})

# ---------- Админка ----------
@app.route('/api/admin/users')
@admin_required
def admin_users():
    db = get_db()
    users = db.execute("SELECT id, username, balance, bonus_balance, total_bet, total_win, is_admin, last_seen FROM users ORDER BY id DESC").fetchall()
    return jsonify([dict(u) for u in users])

@app.route('/api/admin/bonus', methods=['POST'])
@admin_required
def admin_add_bonus():
    data = request.json
    username = data.get('username')
    amount = int(data.get('amount', 0))
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    db.execute("UPDATE users SET bonus_balance = bonus_balance + ? WHERE id=?", (amount, user['id']))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/admin/generate_code', methods=['POST'])
@admin_required
def admin_generate_code():
    data = request.json
    amount = int(data.get('amount', 100))
    code = generate_bonus_code()
    expires = datetime.now() + timedelta(days=7)
    db = get_db()
    db.execute("INSERT INTO bonus_codes (code, amount, expires_at) VALUES (?, ?, ?)",
               (code, amount, expires.isoformat()))
    db.commit()
    return jsonify({'code': code})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
