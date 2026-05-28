import random
from database import get_db

SYMBOLS_OLY = ['⚡', '💎', '🏺', '🦅', '🐉']
MULTIPLIERS = {'⚡': 3, '💎': 10, '🏺': 5, '🦅': 8, '🐉': 20}

def generate_grid(rows=5, cols=5):
    return [[random.choice(SYMBOLS_OLY) for _ in range(cols)] for _ in range(rows)]

def apply_gravity(grid):
    # Симуляция падения: новые символы падают сверху
    for col in range(len(grid[0])):
        column = [grid[row][col] for row in range(len(grid))]
        # Убираем пустоты (None) и сдвигаем вниз
        non_empty = [x for x in column if x is not None]
        missing = len(column) - len(non_empty)
        new_column = [random.choice(SYMBOLS_OLY) for _ in range(missing)] + non_empty
        for row in range(len(grid)):
            grid[row][col] = new_column[row]
    return grid

def calculate_olympus_win(grid, bet):
    win = 0
    # Проверяем горизонтальные линии (минимум 3 одинаковых подряд)
    for row in grid:
        count = 1
        for i in range(1, len(row)):
            if row[i] == row[i-1]:
                count += 1
            else:
                if count >= 3:
                    win += bet * MULTIPLIERS.get(row[i-1], 1) * (count - 2)
                count = 1
        if count >= 3:
            win += bet * MULTIPLIERS.get(row[-1], 1) * (count - 2)
    # Вертикальные линии
    for col in range(len(grid[0])):
        count = 1
        for row in range(1, len(grid)):
            if grid[row][col] == grid[row-1][col]:
                count += 1
            else:
                if count >= 3:
                    win += bet * MULTIPLIERS.get(grid[row-1][col], 1) * (count - 2)
                count = 1
        if count >= 3:
            win += bet * MULTIPLIERS.get(grid[-1][col], 1) * (count - 2)
    return win

def play_olympus(user_id, bet):
    db = get_db()
    user = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    total = user['balance'] + user['bonus_balance']
    if total < bet:
        return None, 0, user['balance'], user['bonus_balance']
    # Списываем
    from_bonus = min(user['bonus_balance'], bet)
    from_main = bet - from_bonus
    db.execute("UPDATE users SET balance = balance - ?, bonus_balance = bonus_balance - ? WHERE id=?", (from_main, from_bonus, user_id))
    grid = generate_grid()
    # Анимация падения будет на фронте, здесь просто финальный результат после падения
    final_grid = apply_gravity(grid)
    win = calculate_olympus_win(final_grid, bet)
    if win > 0:
        db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (win, user_id))
    db.commit()
    new = db.execute("SELECT balance, bonus_balance FROM users WHERE id=?", (user_id,)).fetchone()
    return {'grid': final_grid, 'win': win}, win, new['balance'], new['bonus_balance']
