# app.py
import json
import asyncio
import websockets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import jwt
import smtplib
from fastapi.middleware.cors import CORSMiddleware
from typing import List

# Database setup
DATABASE_URL = "postgresql://example_owner:bpXemxKVZ9h0@ep-shy-recipe-a5cpzfqv.us-east-2.aws.neon.tech/example?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI app setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Update these as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    coin_id = Column(String)
    target_price = Column(Float)
    status = Column(String, default="created")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Security
SECRET_KEY = "balaji"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password):
    # Here you should use a proper hashing function
    return password  # Replace with actual hash logic

def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password  # Replace with actual verification logic

def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class AlertCreate(BaseModel):
    coin_id: str
    target_price: float

class AlertResponse(BaseModel):
    id: int
    coin_id: str
    target_price: float
    status: str
    created_at: datetime

# Endpoints
@app.post("/register")
async def register_user(user: UserCreate):
    db = SessionLocal()
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"username": new_user.username}

@app.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/alerts/create/", response_model=AlertResponse)
def create_alert(alert: AlertCreate, token: str = Depends(oauth2_scheme)):
    db = SessionLocal()
    username = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    db_alert = Alert(user_id=user.id, coin_id=alert.coin_id, target_price=alert.target_price)
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@app.delete("/alerts/delete/{alert_id}")
def delete_alert(alert_id: int, token: str = Depends(oauth2_scheme)):
    db = SessionLocal()
    username = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    db_alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(db_alert)
    db.commit()
    return {"detail": "Alert deleted"}

@app.get("/alerts/", response_model=List[AlertResponse])
def fetch_alerts(status: str = None, skip: int = 0, limit: int = 10, token: str = Depends(oauth2_scheme)):
    db = SessionLocal()
    username = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    query = db.query(Alert).filter(Alert.user_id == user.id)
    if status:
        query = query.filter(Alert.status == status)
    alerts = query.offset(skip).limit(limit).all()
    
    return alerts

@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    asyncio.create_task(get_price_updates())

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")

async def get_price_updates():
    url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    print("Connecting to WebSocket...")
    async with websockets.connect(url) as websocket:
        print("Connected to WebSocket")
        while True:
            data = await websocket.recv()
            price = json.loads(data)["p"]
            print(f"Price received: {price}")
            check_alerts(float(price))

def check_alerts(price):
    db = SessionLocal()
    alerts = db.query(Alert).filter(Alert.target_price <= price, Alert.status == "created").all()
    for alert in alerts:
        send_email(alert)
        alert.status = "triggered"
    db.commit()

def send_email(alert):
    db = SessionLocal()
    user = db.query(User).filter(User.id == alert.user_id).first()
    email = user.email
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "your_email@gmail.com"  # Replace with your email
    password = "your_password"  # Replace with your email password
    message = f"Subject: Price Alert Triggered\n\nThe price of {alert.coin_id} has reached {alert.target_price}."
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, email, message)

# To run the application:
# uvicorn app:app --reload
