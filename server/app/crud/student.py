"""
Модуль для асинхронных CRUD-операций с сущностью Student.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.student import Student
from app.models.group import Group
from app.schemas.student import StudentCreate, StudentUpdate
from typing import List, Optional

async def get_student_by_id(db: AsyncSession, student_id: int) -> Optional[Student]:
    """
    Получить студента по его ID с подгрузкой группы.
    :param db: Асинхронная сессия БД
    :param student_id: ID студента
    :return: Объект Student или None
    """
    result = await db.execute(
        select(Student).options(selectinload(Student.group)).where(Student.id == student_id)
    )
    return result.scalar_one_or_none()

async def get_all_students(db: AsyncSession, group_id: Optional[int] = None) -> List[Student]:
    """
    Получить список всех студентов, опционально фильтруя по группе.
    :param db: Асинхронная сессия БД
    :param group_id: (Необязательно) ID группы для фильтрации
    :return: Список объектов Student
    """
    query = select(Student).options(selectinload(Student.group))
    if group_id:
        query = query.where(Student.group_id == group_id)
    result = await db.execute(query)
    return result.scalars().all()

async def get_student_by_email(db: AsyncSession, email: str) -> Optional[Student]:
    """
    Найти студента по email.
    :param db: Асинхронная сессия БД
    :param email: Email студента
    :return: Объект Student или None
    """
    result = await db.execute(
        select(Student).options(selectinload(Student.group)).where(Student.email == email)
    )
    return result.scalar_one_or_none()

async def create_student(db: AsyncSession, student_in: StudentCreate) -> Student:
    """
    Создать нового студента.
    :param db: Асинхронная сессия БД
    :param student_in: Данные для создания студента
    :return: Созданный объект Student
    """
    # Проверяем, что email уникален
    existing_student = await get_student_by_email(db, student_in.email)
    if existing_student:
        raise ValueError(f"Student with email {student_in.email} already exists")
    
    student = Student(**student_in.model_dump())
    db.add(student)
    await db.commit()
    await db.refresh(student)
    
    # Загружаем студента с группой
    result = await db.execute(
        select(Student).options(selectinload(Student.group)).where(Student.id == student.id)
    )
    return result.scalar_one()

async def update_student(db: AsyncSession, student_id: int, student_in: StudentUpdate) -> Optional[Student]:
    """
    Обновить данные студента по его ID.
    :param db: Асинхронная сессия БД
    :param student_id: ID студента
    :param student_in: Данные для обновления
    :return: Обновлённый объект Student или None
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return None
    update_data = student_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(student, key, value)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student

async def delete_student(db: AsyncSession, student_id: int) -> bool:
    """
    Удалить студента по его ID.
    :param db: Асинхронная сессия БД
    :param student_id: ID студента
    :return: True, если удаление прошло успешно, иначе False
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return False
    await db.delete(student)
    await db.commit()
    return True