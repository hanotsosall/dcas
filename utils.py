import random
import string
from datetime import datetime, timedelta

def generate_bonus_code(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def format_currency(amount):
    return f"{amount:,.0f}"

def calculate_vip_level(total_bet):
    if total_bet < 10000:
        return 0
    elif total_bet < 50000:
        return 1
    elif total_bet < 200000:
        return 2
    elif total_bet < 1000000:
        return 3
    else:
        return 4

def anonymize_username(username):
    if len(username) <= 4:
        return username[0] + '***'
    return username[:2] + '***' + username[-1]

class AnimationPresets:
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

    @staticmethod
    def generate_reel():
        return random.choices(AnimationPresets.SLOT_SYMBOLS, weights=AnimationPresets.WEIGHTS)[0]
