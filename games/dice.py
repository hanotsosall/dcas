import random
from typing import Tuple, Dict, Any

def play_dice(bet: float, params: dict) -> Tuple[Dict[str, Any], float]:
    """
    params: {"prediction": "over"|"under", "target": float (0-100)}
    Или "number" для точного числа
    """
    roll = random.randint(1, 100)
    pred = params.get("prediction")
    target = params.get("target", 50)
    win = 0.0
    
    if pred == "over":
        if roll > target:
            win = bet * 1.98
    elif pred == "under":
        if roll < target:
            win = bet * 1.98
    elif pred == "number":
        if roll == target:
            win = bet * 50
    
    result = {
        "game": "dice",
        "roll": roll,
        "prediction": pred,
        "target": target,
        "win": win
    }
    return result, win
