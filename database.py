from sqlalchemy.orm import Session
from .app import User, Transaction, SpinLog, BonusCode
from datetime import datetime, timedelta

def get_top_users(db: Session, limit: int = 10) -> list:
    return db.query(User).order_by(User.total_win.desc()).limit(limit).all()

def add_transaction(db: Session, user_id: int, amount: float, type: str, game: str = None):
    tx = Transaction(user_id=user_id, amount=amount, type=type, game=game)
    db.add(tx)
    db.commit()

def generate_bonus_code(db: Session, amount: float, expires_days: int = 7) -> str:
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    expires = datetime.utcnow() + timedelta(days=expires_days)
    bc = BonusCode(code=code, amount=amount, expires_at=expires)
    db.add(bc)
    db.commit()
    return code

def apply_bonus_code(db: Session, code: str, user_id: int) -> float:
    bc = db.query(BonusCode).filter(BonusCode.code == code, BonusCode.used_by == None, BonusCode.expires_at > datetime.utcnow()).first()
    if not bc:
        return 0.0
    bc.used_by = user_id
    user = db.query(User).filter(User.id == user_id).first()
    user.balance += bc.amount
    db.commit()
    return bc.amount
