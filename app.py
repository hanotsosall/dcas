import os
import sqlite3
import bcrypt
import random
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, g

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
            commission INTEGER,
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
        # Создать админа, если нет
        admin = cursor.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not admin:
            hashed = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
            cursor.execute("INSERT INTO users (username, password, is_admin, balance) VALUES (?,?,?,?)",
                           ('admin', hashed, 1, 1000000))
            db.commit()
init_db()

# ---------- Хелперы ----------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
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

def update_balance(user_id, delta):
    db = get_db()
    db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (delta, user_id))
    db.commit()

# ---------- Слоты ----------
SLOT_SYMBOLS = [
    {"name": "🍒", "color": "#e74c3c", "value": 2},
    {"name": "🍋", "color": "#f1c40f", "value": 3},
    {"name": "🍊", "color": "#e67e22", "value": 4},
    {"name": "🍉", "color": "#2ecc71", "value": 5},
    {"name": "💎", "color": "#1abc9c", "value": 10},
    {"name": "7️⃣", "color": "#f39c12", "value": 20},
    {"name": "🐉", "color": "#9b59b6", "value": 0, "bonus": True}
]
WEIGHTS = [18, 16, 14, 10, 6, 4, 2]

def generate_reels():
    return [[random.choices(SLOT_SYMBOLS, weights=WEIGHTS)[0] for _ in range(3)] for _ in range(5)]

def calculate_win(reels, bet):
    win = 0
    bonus = 0
    lines = [
        [(0,0),(1,0),(2,0),(3,0),(4,0)],
        [(0,1),(1,1),(2,1),(3,1),(4,1)],
        [(0,2),(1,2),(2,2),(3,2),(4,2)],
        [(0,0),(1,1),(2,2),(3,1),(4,0)],
        [(0,2),(1,1),(2,0),(3,1),(4,2)]
    ]
    for line in lines:
        first = reels[line[0][0]][line[0][1]]
        if first.get('bonus'): continue
        same = True
        for x,y in line[1:]:
            if reels[x][y]['name'] != first['name']:
                same = False
                break
        if same:
            win += bet * first['value']
    for col in reels:
        for sym in col:
            if sym.get('bonus'): bonus += 1
    center = [reels[i][1] for i in range(5)]
    if all(s['name'] == "7️⃣" for s in center):
        win += 5000
    return win, bonus

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
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Заполните поля'})
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password, bonus_balance) VALUES (?, ?, ?)",
                   (username, hashed, 5000))
        db.commit()
        return jsonify({'ok': True})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Логин занят'})

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

@app.route('/api/spin', methods=['POST'])
@login_required
def api_spin():
    data = request.json
    bet = int(data.get('bet', 10))
    is_free = data.get('is_freespin', False)
    db = get_db()
    user = db.execute("SELECT balance FROM users WHERE id=?", (session['user_id'],)).fetchone()
    if not is_free and user['balance'] < bet:
        return jsonify({'error': 'Недостаточно средств'}), 400
    reels = generate_reels()
    win, bonus_cnt = calculate_win(reels, bet)
    if is_free:
        win *= 2
    delta = win - bet if not is_free else win
    new_balance = user['balance'] + delta
    update_balance(session['user_id'], delta)
    db.execute("INSERT INTO spin_log (user_id, game, bet, win, details) VALUES (?,?,?,?,?)",
               (session['user_id'], 'slots', bet, win, json.dumps(reels)))
    db.commit()
    reels_out = [[{'name': s['name'], 'color': s['color']} for s in col] for col in reels]
    trigger = bonus_cnt >= 3 and not is_free
    return jsonify({
        'reels': reels_out,
        'win': win,
        'balance': new_balance,
        'bonus_trigger': trigger,
        'freespins_left': 10 if trigger else 0
    })

# ---------- Остальные игры (рулетка, краш, кости) для краткости опущены, можно добавить по аналогии ----------
# Для простоты добавим заглушки, чтобы не было ошибок 404

@app.route('/api/roulette', methods=['POST'])
@login_required
def api_roulette():
    return jsonify({'error': 'Not implemented in minimal version'}), 501

@app.route('/api/crash/bet', methods=['POST'])
@login_required
def api_crash_bet():
    return jsonify({'error': 'Not implemented'}), 501

@app.route('/api/crash/cashout', methods=['POST'])
@login_required
def api_crash_cashout():
    return jsonify({'error': 'Not implemented'}), 501

@app.route('/api/crash/status')
def crash_status():
    return jsonify({'multiplier': 1.0, 'running': False})

@app.route('/api/dice', methods=['POST'])
@login_required
def api_dice():
    return jsonify({'error': 'Not implemented'}), 501

@app.route('/api/bonus/apply', methods=['POST'])
@login_required
def apply_bonus():
    return jsonify({'error': 'Not implemented'}), 501

@app.route('/api/referral/link')
@login_required
def referral_link():
    return jsonify({'link': request.host_url + '?ref=' + session['username']})

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
        return jsonify({'error': 'Empty'}), 400
    db = get_db()
    db.execute("INSERT INTO chat_messages (user_id, username, message) VALUES (?,?,?)",
               (session['user_id'], session['username'], msg[:200]))
    db.commit()
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
