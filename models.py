from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    id: int
    username: str
    balance: int
    bonus_balance: int = 0
    vip_level: int = 0
    total_bet: int = 0
    total_win: int = 0
    is_admin: bool = False
    created_at: datetime = None

@dataclass
class SpinResult:
    reels: List[List[dict]]
    win: int
    new_balance: int
    bonus_trigger: bool = False

@dataclass
class CrashBet:
    user_id: int
    bet: int
    start_multiplier: float = 1.0
    cashed_out_at: Optional[float] = None
    session_id: str = ""
