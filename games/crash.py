import random
import math
from typing import Tuple, Dict, Any

def play_crash(bet: float, params: dict) -> Tuple[Dict[str, Any], float]:
    """
    params: {"auto_cashout": float} — коэффициент, на котором игрок вышел
    Если не указан, то генерируется случайный краш-коэффициент.
    """
    auto_cashout = params.get("auto_cashout", None)
    
    # Генерируем случайный множитель краша (от 1.01 до 1000, но распределение不均匀)
    # Используем экспоненциальное распределение: большинство крашей < 2x
    crash_point = 1.0
    while crash_point < 1.01:
        # Алгоритм, похожий на Bustabit
        r = random.random()
        crash_point = 0.99 / (1 - r) + 0.01
        if crash_point > 1000:
            crash_point = 1000
    
    crash_point = round(crash_point, 2)
    
    if auto_cashout is None:
        # Игрок не вышел — проигрыш
        win = 0.0
        cashed_out = False
        multiplier = crash_point
    else:
        if auto_cashout < crash_point:
            win = bet * auto_cashout
            cashed_out = True
            multiplier = auto_cashout
        else:
            win = 0.0
            cashed_out = False
            multiplier = crash_point
    
    result = {
        "game": "crash",
        "crash_point": crash_point,
        "cashed_out": cashed_out,
        "multiplier": multiplier,
        "win": win
    }
    return result, win
