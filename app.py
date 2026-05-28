import os
import sqlite3
import bcrypt
import random
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, g, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dragon_god_key_2025')
app.permanent_session_lifetime = timedelta(days=7)

# ---------- Подключение к БД ----------
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
        # Таблица пользователей
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            balance INTEGER DEFAULT 1000,
            bonus_balance INTEGER DEFAULT 0,
            vip_level INTEGER DEFAULT 0,
            total_bet INTEGER DEFAULT 0,
            total_win INTEGER DEFAULT 0,
            referrer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            is_admin BOOLEAN DEFAULT 0
        )''')
        # Таблица транзакций
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            game TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        # Таблица игровых сессий (для краша)
        cursor.execute('''CREATE TABLE IF NOT EXISTS crash_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            multiplier REAL,
            crashed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        # Таблица бонус-кодов
        cursor.execute('''CREATE TABLE IF NOT EXISTS bonus_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            amount INTEGER,
            used_by INTEGER,
            expires_at TIMESTAMP
        )''')
        # Таблица рефералов
        cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            commission INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        # Таблица чата
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()
        # Создаём админа по умолчанию, если нет
        admin = cursor.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not admin:
            hashed = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            cursor.execute("INSERT INTO users (username, password, is_admin, balance) VALUES (?, ?, ?, ?)",
                           ('admin', hashed, 1, 1000000))
            db.commit()
init_db()

# ---------- Декоратор авторизации ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        db = get_db()
        user = db.execute("SELECT is_admin FROM users WHERE id=?", (session['user_id'],)).fetchone()
        if not user or not user['is_admin']:
            return jsonify({'error': 'Forbidden'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ---------- Маршруты ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

# ---------- API авторизации ----------
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
        "INSERT INTO users (username, password, email, referrer_id) VALUES (?, ?, ?, ?)",
        (username, hashed, email, referrer_id)
    )
    db.commit()
    user_id = cursor.lastrowid
    # Начисление бонуса рефереру
    if referrer_id:
        db.execute("UPDATE users SET balance = balance + 100 WHERE id=?", (referrer_id,))
        db.execute("INSERT INTO referrals (referrer_id, referred_id, commission) VALUES (?, ?, ?)",
                   (referrer_id, user_id, 100))
        db.commit()
    # Автоматический вход
    session.permanent = True
    session['user_id'] = user_id
    session['username'] = username
    return jsonify({'ok': True, 'user': {'id': user_id, 'username': username, 'balance': 1000}})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    db = get_db()
    user = db.execute("SELECT id, username, password, balance, is_admin FROM users WHERE username=?", (username,)).fetchone()
    if not user or not bcrypt.checkpw(password.encode(), user['password'].encode()):
        return jsonify({'error': 'Неверные данные'}), 401
    session.permanent = True
    session['user_id'] = user['id']
    session['username'] = user['username']
    db.execute("UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id=?", (user['id'],))
    db.commit()
    return jsonify({'ok': True, 'user': {'id': user['id'], 'username': user['username'], 'balance': user['balance'], 'is_admin': user['is_admin']}})

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
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(user))

# ---------- API для игр (будет подключено из модулей) ----------
# Здесь импортируем функции игр, чтобы избежать циклических импортов
from games.slots import spin_slots
from games.roulette import spin_roulette
from games.crash import start_crash_bet, cashout_crash, get_crash_status
from games.dice import roll_dice

@app.route('/api/spin', methods=['POST'])
@login_required
def api_spin():
    data = request.json
    bet = int(data.get('bet', 10))
    is_free = data.get('is_freespin', False)
    result, win, new_balance, bonus_trigger = spin_slots(session['user_id'], bet, is_free)
    if result is None:
        return jsonify({'error': 'Недостаточно средств'}), 400
    return jsonify({
        'reels': result['reels'],
        'win': win,
        'balance': new_balance,
        'bonus_trigger': bonus_trigger,
        'freespins_left': 10 if bonus_trigger else 0
    })

@app.route('/api/roulette', methods=['POST'])
@login_required
def api_roulette():
    data = request.json
    bet = int(data.get('bet', 10))
    bet_type = data.get('bet_type')
    value = data.get('value')
    result, win, new_balance = spin_roulette(session['user_id'], bet, bet_type, value)
    if result is None:
        return jsonify({'error': 'Недостаточно средств'}), 400
    return jsonify({'result': result, 'win': win, 'balance': new_balance})

@app.route('/api/crash/bet', methods=['POST'])
@login_required
def api_crash_bet():
    data = request.json
    bet = int(data.get('bet', 10))
    result, new_balance, session_id = start_crash_bet(session['user_id'], bet)
    if result is None:
        return jsonify({'error': 'Недостаточно средств'}), 400
    return jsonify({'ok': True, 'balance': new_balance, 'session_id': session_id})

@app.route('/api/crash/cashout', methods=['POST'])
@login_required
def api_crash_cashout():
    data = request.json
    session_id = data.get('session_id')
    result, win, new_balance = cashout_crash(session['user_id'], session_id)
    if result is None:
        return jsonify({'error': 'Сессия не найдена'}), 400
    return jsonify({'win': win, 'balance': new_balance})

@app.route('/api/crash/status')
def crash_status():
    # Возвращает текущий множитель краша для всех
    return jsonify(get_crash_status())

@app.route('/api/dice', methods=['POST'])
@login_required
def api_dice():
    data = request.json
    bet = int(data.get('bet', 10))
    prediction = data.get('prediction')
    target = int(data.get('target', 50))
    result, win, new_balance = roll_dice(session['user_id'], bet, prediction, target)
    if result is None:
        return jsonify({'error': 'Недостаточно средств'}), 400
    return jsonify({'result': result, 'win': win, 'balance': new_balance})

# ---------- Бонус-коды ----------
@app.route('/api/bonus/apply', methods=['POST'])
@login_required
def apply_bonus():
    data = request.json
    code = data.get('code', '').upper()
    db = get_db()
    bonus = db.execute("SELECT amount, expires_at FROM bonus_codes WHERE code=? AND used_by IS NULL", (code,)).fetchone()
    if not bonus:
        return jsonify({'error': 'Неверный код'}), 400
    if datetime.now() > datetime.fromisoformat(bonus['expires_at']):
        return jsonify({'error': 'Код истёк'}), 400
    db.execute("UPDATE bonus_codes SET used_by=? WHERE code=?", (session['user_id'], code))
    db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (bonus['amount'], session['user_id']))
    db.commit()
    return jsonify({'ok': True, 'amount': bonus['amount']})

# ---------- Реферальная ссылка ----------
@app.route('/api/referral/link')
@login_required
def referral_link():
    username = session['username']
    return jsonify({'link': f"{request.host_url}?ref={username}"})

# ---------- Чат ----------
@app.route('/api/chat/messages', methods=['GET'])
def get_messages():
    db = get_db()
    messages = db.execute("SELECT username, message, created_at FROM chat_messages ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify([dict(m) for m in messages][::-1])

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
    users = db.execute("SELECT id, username, balance, total_bet, total_win, is_admin, last_seen FROM users ORDER BY id DESC").fetchall()
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
    db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user['id']))
    db.commit()
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
