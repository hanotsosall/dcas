import random
import json
from typing import Tuple, Dict, Any

# Символы слота (эмодзи + цвета)
SLOT_SYMBOLS = [
    {"id": 0, "name": "🍒", "value": 2, "color": "#e63946", "bonus": False},
    {"id": 1, "name": "🍋", "value": 3, "color": "#f4d03f", "bonus": False},
    {"id": 2, "name": "🍊", "value": 4, "color": "#f39c12", "bonus": False},
    {"id": 3, "name": "🍉", "value": 5, "color": "#2ecc71", "bonus": False},
    {"id": 4, "name": "💎", "value": 10, "color": "#1abc9c", "bonus": False},
    {"id": 5, "name": "7️⃣", "value": 20, "color": "#e67e22", "bonus": False},
    {"id": 6, "name": "🐉", "value": 0, "color": "#9b59b6", "bonus": True}
]

# Веса для генерации (чем реже, тем меньше вес)
WEIGHTS = [18, 16, 14, 10, 6, 4, 2]  # дракон = 2%

# Линии для подсчёта выигрыша (5 линий: 3 горизонтальные + 2 диагонали)
PAY_LINES = [
    [(0,0), (1,0), (2,0), (3,0), (4,0)],  # верх
    [(0,1), (1,1), (2,1), (3,1), (4,1)],  # центр
    [(0,2), (1,2), (2,2), (3,2), (4,2)],  # низ
    [(0,0), (1,1), (2,2), (3,1), (4,0)],  # диагональ 1
    [(0,2), (1,1), (2,0), (3,1), (4,2)]   # диагональ 2
]

def generate_reels() -> list:
    """Генерирует 5 барабанов x 3 ряда символов"""
    reels = []
    for _ in range(5):
        col = []
        for _ in range(3):
            sym = random.choices(SLOT_SYMBOLS, weights=WEIGHTS)[0]
            col.append(sym.copy())  # копия, чтобы не менять оригинал
        reels.append(col)
    return reels

def calculate_win(reels: list, bet: float) -> Tuple[float, int]:
    """
    Возвращает (выигрыш, количество бонусных символов)
    """
    win = 0.0
    bonus_count = 0
    
    # Подсчёт бонусов
    for col in reels:
        for sym in col:
            if sym["bonus"]:
                bonus_count += 1
    
    # Проверка линий
    for line in PAY_LINES:
        first_sym = reels[line[0][0]][line[0][1]]
        if first_sym["bonus"]:
            continue
        all_match = True
        for (col, row) in line[1:]:
            if reels[col][row]["name"] != first_sym["name"]:
                all_match = False
                break
        if all_match:
            win += bet * first_sym["value"]
    
    # Джекпот за пять 7️⃣ в центре
    center_line = [reels[i][1] for i in range(5)]
    if all(sym["name"] == "7️⃣" for sym in center_line):
        win += 5000.0
    
    # Спец-бонус: 3 дракона дают фриспины (но их обработка на фронте)
    # Здесь просто возвращаем bonus_count
    return win, bonus_count

def play_slots(bet: float, params: dict = None) -> Tuple[Dict[str, Any], float]:
    """
    Основная функция игры. Возвращает (результат, выигрыш)
    """
    reels = generate_reels()
    win, bonus_count = calculate_win(reels, bet)
    
    # Подготовка результата для фронта
    result = {
        "game": "slots",
        "reels": [[{"name": s["name"], "color": s["color"]} for s in col] for col in reels],
        "bonus_trigger": bonus_count >= 3,
        "bonus_count": bonus_count,
        "win_amount": win
    }
    return result, win
