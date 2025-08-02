# /server/main.py

import os
import json
from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, status, Query
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import (Column, Integer, String, ForeignKey, select)
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from sqlalchemy.ext.declarative import declarative_base

# --- 1. Настройки и Конфигурация ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/eduanalytics_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://cache")
SECRET_KEY = "your-very-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- 2. Настройка Базы Данных ---
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --- 3. Модели Базы Данных ---
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    students = relationship("Student", back_populates="group")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="students")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")

# --- 4. Схемы Данных (Pydantic) ---
class StudentCreate(BaseModel):
    name: str
    group_id: int

# --- 5. Утилиты и Зависимости ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- 6. Основное приложение FastAPI ---
app = FastAPI(title="EduAnalytics AI API")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        # Проверяем и создаем администратора
        result = await session.execute(select(User).where(User.email == "admin@eduanalytics.ru"))
        if not result.scalars().first():
            print("--- Создание тестового администратора ---")
            hashed_password = get_password_hash("admin123")
            admin_user = User(email="admin@eduanalytics.ru", hashed_password=hashed_password, role="admin")
            session.add(admin_user)
            await session.commit()
            print("--- Администратор успешно создан ---")
        
        # Проверяем и создаем группы и студентов
        result = await session.execute(select(Group))
        if not result.scalars().first():
            print("--- Создание тестовых данных (группы и студенты) ---")
            group_5a = Group(name="5A")
            group_6b = Group(name="6B")
            session.add_all([group_5a, group_6b])
            await session.commit()
            students_to_add = [
                Student(name="Алихан Нургалиев", group=group_5a),
                Student(name="Айгерим Сатыбалдина", group=group_5a),
                Student(name="Мадияр Сериков", group=group_5a),
                Student(name="Жансая Аскарова", group=group_6b),
                Student(name="Тимур Давлетов", group=group_6b),
            ]
            session.add_all(students_to_add)
            await session.commit()
            print("--- Тестовые данные успешно созданы ---")

@app.on_event("startup")
async def on_startup():
    await init_db()

# --- ИСПРАВЛЕНИЕ: Добавляем localhost:8000 в разрешенные источники ---
origins = [
    "http://localhost:3000",
    "http://localhost:4028",
    "http://localhost:8000", # Для работы Swagger UI
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def get_redis():
    try:
        r = await redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        yield r
        await r.close()
    except redis.ConnectionError as e:
        raise HTTPException(status_code=500, detail=f"Redis connection error: {e}")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None: raise credentials_exception
    return user

# --- 7. Эндпоинты API ---
@app.get("/")
async def read_root():
    return {"message": "EduAnalytics AI Backend is running!"}

@app.post("/api/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"})
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/students")
async def get_students(
    group_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    cache_key = f"students:group_{group_id}:skip_{skip}:limit_{limit}"
    if cached_data := await redis_client.get(cache_key):
        return JSONResponse(content=json.loads(cached_data))
    query = select(Student).order_by(Student.name.asc()).options(joinedload(Student.group))
    if group_id is not None:
        group_res = await db.execute(select(Group).where(Group.id == group_id))
        if not group_res.scalars().first():
            raise HTTPException(status_code=404, detail="Group not found")
        query = query.where(Student.group_id == group_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    students_orm = result.scalars().all()
    response_data = []
    for s in students_orm:
        response_data.append({
            "id": s.id, "name": s.name, "group_id": s.group_id,
            "group_name": s.group.name if s.group else "N/A"
        })
    await redis_client.set(cache_key, json.dumps(response_data), ex=900)
    return JSONResponse(content=response_data)

@app.post("/api/students")
async def create_student(
    student: StudentCreate, 
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Group).where(Group.id == student.group_id))
    db_group = result.scalars().first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    db_student = Student(name=student.name, group_id=student.group_id)
    db.add(db_student)
    await db.commit()
    await db.refresh(db_student)

    keys = await redis_client.keys("students:*")
    if keys:
        await redis_client.delete(*keys)

    response_data = {
        "id": db_student.id,
        "name": db_student.name,
        "group_id": db_student.group_id,
        "group_name": db_group.name
    }
    
    return JSONResponse(content=response_data, status_code=status.HTTP_201_CREATED)