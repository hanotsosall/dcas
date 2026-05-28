import random
def play_olympus(bet, user_id):
    # 5x5 поле с символами: ⚡, 💎, 🏺, 🦅, 🐉
    symbols = ['⚡','💎','🏺','🦅','🐉']
    grid = [[random.choice(symbols) for _ in range(5)] for _ in range(5)]
    # Гравитация: симуляция падения
    win = 0
    # Подсчёт выигрышей (минимум 3 в линию)
    for row in grid:
        counts = {}
        for s in row:
            counts[s] = counts.get(s,0)+1
        for s,c in counts.items():
            if c>=3:
                win += bet * (c*2)
    return grid, win
