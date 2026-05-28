import sqlite3
from flask import g

DATABASE = 'casino.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

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
