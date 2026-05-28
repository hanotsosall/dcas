# app.py – ЯДРО КАЗИНО (часть 1)
import os
import asyncio
import json
import random
import hashlib
import time
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import bcrypt
import jwt
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import aioredis
from dotenv import load_dotenv

load_dotenv()

# ---------- Конфигурация ----------
SECRET_KEY = os.getenv("SECRET_KEY", "dragon_god_super_secret_2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./casino.db")

# ---------- SQLAlchemy ----------
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели БД
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=1000.0)
    bonus_balance = Column(Float, default=0.0)
    vip_level = Column(Integer, default=0)
    total_bet = Column(Float, default=0.0)
    total_win = Column(Float, default=0.0)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    last_seen = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    type = Column(String)  # deposit, withdraw, bet, win, bonus
    game = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

class SpinLog(Base):
    __tablename__ = "spin_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game = Column(String)  # slots, roulette, crash, dice
    bet = Column(Float)
    win = Column(Float)
    details = Column(Text)  # JSON результат
    created_at = Column(DateTime, default=func.now())

class BonusCode(Base):
    __tablename__ = "bonus_codes"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    amount = Column(Float)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

Base.metadata.create_all(bind=engine)

# ---------- Redis ----------
redis = None
async def get_redis():
    global redis
    if redis is None:
        redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis

# ---------- Асинхронный lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск: подключаем Redis
    await get_redis()
    print("🔥 DRAGON GOD CASINO запущен на порту 8080")
    yield
    # Остановка
    await redis.close()

app = FastAPI(title="Dragon God Casino", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------- Хелперы ----------
def get_password_hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- API маршруты (REST) ----------
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    ref_code: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class BetRequest(BaseModel):
    game: str
    bet: float
    params: Optional[Dict] = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Имя уже занято")
    hashed = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed, balance=1000.0)
    if user.ref_code:
        referrer = db.query(User).filter(User.username == user.ref_code).first()
        if referrer:
            new_user.referrer_id = referrer.id
            # бонус рефереру
            referrer.balance += 50
            db.add(referrer)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_access_token({"sub": new_user.username, "id": new_user.id})
    return {"access_token": token, "token_type": "bearer", "user": {"id": new_user.id, "username": new_user.username, "balance": new_user.balance}}

@app.post("/api/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные данные")
    token = create_access_token({"sub": db_user.username, "id": db_user.id})
    return {"access_token": token, "token_type": "bearer", "user": {"id": db_user.id, "username": db_user.username, "balance": db_user.balance}}

@app.get("/api/user")
async def get_user(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = auth.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401)
    user_id = payload.get("id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return {"id": user.id, "username": user.username, "balance": user.balance, "bonus": user.bonus_balance, "vip": user.vip_level}

@app.post("/api/bet")
async def place_bet(bet: BetRequest, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = auth.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401)
    user_id = payload.get("id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    if user.balance < bet.bet:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    # Импортируем игры
    from games.slots import play_slots
    from games.roulette import play_roulette
    from games.crash import play_crash
    from games.dice import play_dice
    
    result = None
    win_amount = 0
    if bet.game == "slots":
        result, win_amount = play_slots(bet.bet, bet.params)
    elif bet.game == "roulette":
        result, win_amount = play_roulette(bet.bet, bet.params)
    elif bet.game == "crash":
        result, win_amount = play_crash(bet.bet, bet.params)
    elif bet.game == "dice":
        result, win_amount = play_dice(bet.bet, bet.params)
    else:
        raise HTTPException(status_code=400, detail="Неизвестная игра")
    
    # Обновляем баланс
    net = win_amount - bet.bet
    user.balance += net
    user.total_bet += bet.bet
    user.total_win += win_amount
    # Логируем
    log = SpinLog(user_id=user.id, game=bet.game, bet=bet.bet, win=win_amount, details=json.dumps(result))
    db.add(log)
    db.commit()
    
    return {"result": result, "win": win_amount, "new_balance": user.balance}
