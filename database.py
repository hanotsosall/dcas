import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

DATABASE = 'casino.db'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
            return dict(result) if result else None
        elif fetch_all:
            return [dict(row) for row in cursor.fetchall()]
        else:
            conn.commit()
            return cursor.lastrowid

def get_user(user_id):
    return execute_query("SELECT id, username, balance, bonus_balance, vip_level, total_bet, total_win, is_admin FROM users WHERE id=?", (user_id,), fetch_one=True)

def update_balance(user_id, delta, commit=True):
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE id=?", (delta, user_id))
        if commit:
            conn.commit()

def log_transaction(user_id, amount, type, game=None):
    execute_query("INSERT INTO transactions (user_id, amount, type, game) VALUES (?, ?, ?, ?)",
                  (user_id, amount, type, game))
