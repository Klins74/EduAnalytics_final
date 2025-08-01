# /server/main.py

import os
import random
from datetime import datetime, timedelta, timezone
from typing import List

# Импорт для Gemini
import google.generativeai as genai

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# --- 1. Настройки и Конфигурация ---
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = "your-very-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Настройка Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- 2. Настройка Базы Данных (SQLAlchemy) ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 3. Модели Базы Данных ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")

# --- 4. Схемы Данных (Pydantic) для API ---
class KPIData(BaseModel): id: str; title: str; value: str; change: str; changeType: str; icon: str; color: str; description: str
class ActivityChartData(BaseModel): date: str; students: int; sessions: int; engagement: int
class RecentActivityData(BaseModel): id: int; type: str; student: str; action: str; course: str; timestamp: datetime; status: str; details: str
class StudentData(BaseModel): id: int; name: str; avatar: str; group: str; totalActivities: int; lastActivity: datetime; engagementStatus: str; aiRiskScore: float; averageScore: float; subjects: List[str]
class ChatRequest(BaseModel): message: str
class ChatResponse(BaseModel): reply: str

# --- 5. Основное приложение FastAPI ---
app = FastAPI(title="EduAnalytics AI API")

# Настройка CORS
origins = ["http://localhost:4028"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 6. Утилиты для Безопасности и работы с БД ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def verify_password(plain_password, hashed_password): return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password): return pwd_context.hash(password)
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None: raise credentials_exception
    return user

# --- 7. Создание таблиц и тестового пользователя при старте ---
Base.metadata.create_all(bind=engine)

def create_initial_user(db: Session):
    if not db.query(User).filter(User.email == "admin@eduanalytics.ru").first():
        hashed_password = get_password_hash("admin123")
        db_user = User(email="admin@eduanalytics.ru", hashed_password=hashed_password, role="admin")
        db.add(db_user)
        db.commit()
        print("--- Тестовый администратор успешно создан ---")

with SessionLocal() as db:
    create_initial_user(db)

# --- 8. Эндпоинты API ---
@app.get("/")
def read_root():
    return {"message": "EduAnalytics AI Backend is running!"}

@app.post("/api/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"})
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email, "role": user.role}, expires_delta=expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/dashboard/kpi", response_model=List[KPIData])
async def get_kpi_data(current_user: User = Depends(get_current_user)):
    return [
        {"id": "students", "title": "Всего студентов", "value": "3,128", "change": "+15%", "changeType": "positive", "icon": "Users", "color": "primary", "description": "Активных студентов в системе"},
        {"id": "activity", "title": "Активность", "value": "91.5%", "change": "+2.1%", "changeType": "positive", "icon": "Activity", "color": "success", "description": "Средняя активность за неделю"},
        {"id": "performance", "title": "Успеваемость", "value": "4.3", "change": "+0.1", "changeType": "positive", "icon": "TrendingUp", "color": "accent", "description": "Средний балл по системе"},
        {"id": "alerts", "title": "Предупреждения", "value": "19", "change": "-4", "changeType": "negative", "icon": "AlertTriangle", "color": "warning", "description": "Требуют внимания"}
    ]

@app.get("/api/dashboard/activity-chart", response_model=List[ActivityChartData])
async def get_activity_chart_data(current_user: User = Depends(get_current_user)):
    return [
        {"date": "01.12", "students": 2340, "sessions": 4200, "engagement": 85},
        {"date": "02.12", "students": 2456, "sessions": 4350, "engagement": 87},
        {"date": "03.12", "students": 2398, "sessions": 4180, "engagement": 82},
        {"date": "04.12", "students": 2567, "sessions": 4520, "engagement": 89},
        {"date": "05.12", "students": 2634, "sessions": 4680, "engagement": 91},
        {"date": "06.12", "students": 2589, "sessions": 4590, "engagement": 88},
        {"date": "07.12", "students": 2847, "sessions": 4920, "engagement": 92}
    ]

@app.get("/api/dashboard/recent-activity", response_model=List[RecentActivityData])
async def get_recent_activity_data(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    return [
        {"id": 1, "type": "login", "student": "Айзере Асқар", "action": "Вход в систему", "course": "Математический анализ", "timestamp": now - timedelta(minutes=5), "status": "success", "details": "Успешная авторизация"},
        {"id": 2, "type": "assignment", "student": "Нұрлан Оспанов", "action": "Сдача задания", "course": "Физика", "timestamp": now - timedelta(minutes=15), "status": "success", "details": "Лабораторная работа №3"},
        {"id": 3, "type": "test", "student": "Алихан Берік", "action": "Прохождение теста", "course": "История", "timestamp": now - timedelta(minutes=30), "status": "warning", "details": "Результат 65%"},
        {"id": 4, "type": "assignment", "student": "Камила Ермекова", "action": "Просрочка", "course": "Биология", "timestamp": now - timedelta(hours=1, minutes=30), "status": "error", "details": "Задание 'Клеточная структура'"},
    ]

@app.get("/api/students", response_model=List[StudentData])
async def get_students_data(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    return [
        {"id": 1, "name": "Мәриәм Сұлтанова", "avatar": "https://i.pravatar.cc/150?img=1", "group": "ИТ-21-1", "totalActivities": 48, "lastActivity": now - timedelta(hours=1), "engagementStatus": "active", "aiRiskScore": 0.2, "averageScore": 4.5, "subjects": ["Математика", "Физика"]},
        {"id": 2, "name": "Қаржаубаева Аружан", "avatar": "https://i.pravatar.cc/150?img=2", "group": "ИТ-21-2", "totalActivities": 32, "lastActivity": now - timedelta(days=1), "engagementStatus": "moderate", "aiRiskScore": 0.5, "averageScore": 3.8, "subjects": ["Химия", "Биология"]},
        {"id": 3, "name": "Қуанышев Асылхан", "avatar": "https://i.pravatar.cc/150?img=3", "group": "ИТ-21-1", "totalActivities": 15, "lastActivity": now - timedelta(days=3), "engagementStatus": "low", "aiRiskScore": 0.8, "averageScore": 3.1, "subjects": ["Тарих", "Дерекқорлар"]},
        {"id": 4, "name": "Имаш Тимур", "avatar": "https://i.pravatar.cc/150?img=4", "group": "ФМ-20-1", "totalActivities": 55, "lastActivity": now - timedelta(minutes=30), "engagementStatus": "active", "aiRiskScore": 0.1, "averageScore": 4.8, "subjects": ["Физика", "Жоғары математика"]}
    ]

@app.post("/api/ai/chat", response_model=ChatResponse)
async def handle_ai_chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    user_message = request.message
    
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API ключ для Gemini не настроен на сервере.")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Ты — AI-ассистент в образовательной платформе EduAnalytics. Ответь на вопрос студента или преподавателя кратко и по делу. Вопрос: '{user_message}'"
        response = await model.generate_content_async(prompt)
        reply = response.text
    except Exception as e:
        print(f"Ошибка вызова Gemini API: {e}")
        raise HTTPException(status_code=500, detail="Произошла ошибка при обращении к AI-сервису.")

    return {"reply": reply}