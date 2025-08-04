import os
import json
from typing import List, Optional, Any
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, status, Query, APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import Column, Integer, String, ForeignKey, select, func
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError

# --- 1. Настройки и Конфигурация ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db:5432/eduanalytics_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://cache")
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@eduanalytics.ru")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# --- 2. Настройка Базы Данных ---
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --- 3. Модели Базы Данных ---
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    students = relationship("Student", back_populates="group")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="students")
    grades = relationship("Grade", back_populates="student")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    teacher = relationship("User", back_populates="subjects")
    grades = relationship("Grade", back_populates="subject")

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    grade = Column(Integer, nullable=False)
    date = Column(String, default=datetime.now(timezone.utc).isoformat)
    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String(20), nullable=False, default="teacher")
    subjects = relationship("Subject", back_populates="teacher")

# --- 4. Схемы Данных (Pydantic) ---
class StudentCreate(BaseModel):
    full_name: str = Field(..., max_length=100)
    group_id: int

class StudentResponse(BaseModel):
    id: int
    full_name: str
    group_id: int
    group_name: str

class GroupCreate(BaseModel):
    name: str = Field(..., max_length=50)

class GroupResponse(BaseModel):
    id: int
    name: str
    student_count: int

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "teacher"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class GradeCreate(BaseModel):
    student_id: int
    subject_id: int
    grade: int = Field(..., ge=1, le=5)

class GradeResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    grade: int
    date: str
    student_name: str
    subject_name: str

# --- 5. Утилиты и Зависимости ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- Интеграция Sentry для мониторинга ошибок ---
import sentry_sdk

# Получаем настройки Sentry из переменных окружения
SENTRY_DSN = os.getenv("SENTRY_DSN", "https://58714683213474f3dc910effbffda5e3@o4509786424541184.ingest.de.sentry.io/4509786456588368")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENVIRONMENT,
    traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

# --- 6. Основное приложение FastAPI ---
app = FastAPI(
    title="EduAnalytics AI API",
    description="API для управления учебным процессом и аналитики успеваемости",
    version="1.0.0"
)

# Роутеры для разных частей API
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(tags=["auth"])
students_router = APIRouter(prefix="/students", tags=["students"])
groups_router = APIRouter(prefix="/groups", tags=["groups"])
users_router = APIRouter(prefix="/users", tags=["users"])
grades_router = APIRouter(prefix="/grades", tags=["grades"])
sentry_router = APIRouter(prefix="/sentry", tags=["sentry"])

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Проверяем и создаем администратора
        admin = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        if not admin.scalars().first():
            print("--- Создание администратора ---")
            hashed_password = get_password_hash(ADMIN_PASSWORD)
            admin_user = User(
                email=ADMIN_EMAIL,
                full_name="Администратор Системы",
                hashed_password=hashed_password,
                role="admin"
            )
            session.add(admin_user)
            await session.commit()
            print("--- Администратор успешно создан ---")
        
        # Проверяем и создаем группы
        groups = await session.execute(select(Group))
        if not groups.scalars().first():
            print("--- Создание тестовых групп ---")
            group_5a = Group(name="5A")
            group_6b = Group(name="6B")
            session.add_all([group_5a, group_6b])
            await session.commit()
            print("--- Группы успешно созданы ---")
        
        # Проверяем и создаем предметы
        subjects = await session.execute(select(Subject))
        if not subjects.scalars().first():
            print("--- Создание тестовых предметов ---")
            math = Subject(name="Математика")
            physics = Subject(name="Физика")
            session.add_all([math, physics])
            await session.commit()
            print("--- Предметы успешно созданы ---")
        
        # Проверяем и создаем студентов
        students = await session.execute(select(Student))
        if not students.scalars().first():
            print("--- Создание тестовых студентов ---")
            group_5a = await session.execute(select(Group).where(Group.name == "5A"))
            group_5a = group_5a.scalars().first()
            
            group_6b = await session.execute(select(Group).where(Group.name == "6B"))
            group_6b = group_6b.scalars().first()
            
            students_to_add = [
                Student(full_name="Алихан Нургалиев", group=group_5a),
                Student(full_name="Айгерим Сатыбалдина", group=group_5a),
                Student(full_name="Мадияр Сериков", group=group_5a),
                Student(full_name="Жансая Аскарова", group=group_6b),
                Student(full_name="Тимур Давлетов", group=group_6b),
            ]
            session.add_all(students_to_add)
            await session.commit()
            print("--- Студенты успешно созданы ---")

@app.on_event("startup")
async def on_startup():
    await init_db()

# --- Настройка CORS ---
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Зависимости ---
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def get_redis():
    try:
        r = await redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        yield r
        await r.close()
    except redis.ConnectionError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к Redis: {e}")

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: 
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None: 
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user

async def check_admin_permission(
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения операции"
        )

# --- 7. Эндпоинты API ---

# Аутентификация
@auth_router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Студенты
@students_router.get("/", response_model=List[StudentResponse])
async def get_students(
    group_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    cache_key = f"students:group_{group_id}:skip_{skip}:limit_{limit}"
    if cached_data := await redis_client.get(cache_key):
        return json.loads(cached_data)
    
    query = select(Student).options(joinedload(Student.group)).order_by(Student.full_name.asc())
    
    if group_id is not None:
        group_exists = await db.execute(select(Group).where(Group.id == group_id))
        if not group_exists.scalars().first():
            raise HTTPException(status_code=404, detail="Группа не найдена")
        query = query.where(Student.group_id == group_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    students = result.scalars().all()
    
    response_data = [
        {
            "id": s.id,
            "full_name": s.full_name,
            "group_id": s.group_id,
            "group_name": s.group.name if s.group else "N/A"
        } for s in students
    ]
    
    await redis_client.set(cache_key, json.dumps(response_data), ex=900)
    return response_data

@students_router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student: StudentCreate, 
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    # Проверка существования группы
    group_result = await db.execute(select(Group).where(Group.id == student.group_id))
    group = group_result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Создание студента
    new_student = Student(full_name=student.full_name, group_id=student.group_id)
    
    try:
        db.add(new_student)
        await db.commit()
        await db.refresh(new_student)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ошибка при создании студента")
    
    # Очистка кэша студентов
    keys = await redis_client.keys("students:*")
    if keys:
        await redis_client.delete(*keys)
    
    return {
        "id": new_student.id,
        "full_name": new_student.full_name,
        "group_id": new_student.group_id,
        "group_name": group.name
    }

# Группы
@groups_router.get("/", response_model=List[GroupResponse])
async def get_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
):
    cache_key = f"groups:skip_{skip}:limit_{limit}"
    if cached_data := await redis_client.get(cache_key):
        return json.loads(cached_data)

    # Оптимизированный запрос, который считает студентов одним махом
    subquery = select(Student.group_id, func.count(Student.id).label("student_count")) \
        .group_by(Student.group_id).subquery()

    query = select(Group, func.coalesce(subquery.c.student_count, 0).label("student_count")) \
        .outerjoin(subquery, Group.id == subquery.c.group_id) \
        .order_by(Group.name.asc()) \
        .offset(skip).limit(limit)
        
    result = await db.execute(query)
    groups_with_counts = result.all()

    response_data = [
        {
            "id": group.id,
            "name": group.name,
            "student_count": count
        } for group, count in groups_with_counts
    ]

    await redis_client.set(cache_key, json.dumps(response_data), ex=1800)
    return response_data

@groups_router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate, 
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: User = Depends(check_admin_permission)
):
    new_group = Group(name=group.name)
    
    try:
        db.add(new_group)
        await db.commit()
        await db.refresh(new_group)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Группа с таким именем уже существует")
    
    # Очистка кэша групп
    keys = await redis_client.keys("groups:*")
    if keys:
        await redis_client.delete(*keys)
    
    return {
        "id": new_group.id,
        "name": new_group.name,
        "student_count": 0
    }

# Пользователи
@users_router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    query = select(User).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role
        } for u in users
    ]

@users_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    # Проверка существования пользователя
    existing_user = await db.execute(select(User).where(User.email == user.email))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    # Создание пользователя
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role
    }

# Оценки
@grades_router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def create_grade(
    grade: GradeCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Проверка существования студента
    student_result = await db.execute(select(Student).where(Student.id == grade.student_id))
    student = student_result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    # Проверка существования предмета
    subject_result = await db.execute(select(Subject).where(Subject.id == grade.subject_id))
    subject = subject_result.scalars().first()
    if not subject:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    # Создание оценки
    new_grade = Grade(
        student_id=grade.student_id,
        subject_id=grade.subject_id,
        grade=grade.grade
    )
    
    try:
        db.add(new_grade)
        await db.commit()
        await db.refresh(new_grade)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при создании оценки")
    
    return {
        "id": new_grade.id,
        "student_id": new_grade.student_id,
        "subject_id": new_grade.subject_id,
        "grade": new_grade.grade,
        "date": new_grade.date,
        "student_name": student.full_name,
        "subject_name": subject.name
    }

# Системный статус
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# Тестовый эндпоинт для Sentry
@sentry_router.get("/test")
async def test_sentry():
    try:
        # Генерируем ошибку для тестирования Sentry
        1 / 0
    except Exception as e:
        # Отправляем ошибку в Sentry
        sentry_sdk.capture_exception(e)
        # Возвращаем сообщение пользователю
        return {"message": "Тестовая ошибка отправлена в Sentry!"}

# --- Регистрация роутеров ---
api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(groups_router)
api_router.include_router(users_router)
api_router.include_router(grades_router)
api_router.include_router(sentry_router)
app.include_router(api_router)

# ПРАВИЛЬНЫЙ КОД
@app.get("/")
async def read_root():
    return {
        "message": "Добро пожаловать в EduAnalytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }