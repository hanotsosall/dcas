import random
from typing import Tuple, Dict, Any

EUROPEAN_NUMBERS = list(range(0, 37))  # 0-36
RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def get_color(num):
    if num == 0:
        return "green"
    elif num in RED_NUMBERS:
        return "red"
    else:
        return "black"

def play_roulette(bet: float, params: dict) -> Tuple[Dict[str, Any], float]:
    """
    params: {
        "bet_type": "number" | "color" | "evenodd" | "dozen" | "column",
        "value": ...  # номер/цвет/...
    }
    """
    bet_type = params.get("bet_type", "number")
    value = params.get("value")
    
    result_number = random.choice(EUROPEAN_NUMBERS)
    result_color = get_color(result_number)
    win = 0.0
    
    if bet_type == "number":
        if result_number == value:
            win = bet * 35
    elif bet_type == "color":
        if result_color == value:
            win = bet * 2
    elif bet_type == "evenodd":
        if result_number == 0:
            win = 0
        elif value == "even" and result_number % 2 == 0:
            win = bet * 2
        elif value == "odd" and result_number % 2 == 1:
            win = bet * 2
    elif bet_type == "dozen":
        # 1-12, 13-24, 25-36
        dozen = (result_number - 1) // 12 if result_number > 0 else -1
        if dozen == value:
            win = bet * 3
    elif bet_type == "column":
        col = (result_number - 1) % 3 if result_number > 0 else -1
        if col == value:
            win = bet * 3
    
    result = {
        "game": "roulette",
        "number": result_number,
        "color": result_color,
        "bet_type": bet_type,
        "win": win
    }
    return result, win
