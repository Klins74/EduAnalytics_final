from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.schemas.student import StudentRead, StudentCreate, StudentUpdate
from app.crud import student as crud_student
from app.db.session import get_async_session

router = APIRouter(prefix="/students", tags=["Students"])

@router.get(
    "/",
    response_model=List[StudentRead],
    summary="Получить список студентов",
    description="Возвращает список всех студентов. Поддерживает фильтрацию по group_id через query-параметр."
)
async def get_all_students(group_id: Optional[int] = None, session: AsyncSession = Depends(get_async_session)):
    """
    Получение всех студентов с возможной фильтрацией по группе.
    - Если group_id не указан, возвращаются все студенты
    - Использует асинхронную сессию SQLAlchemy
    """
    # Фильтрация по группе, если параметр передан
    return await crud_student.get_all_students(session, group_id=group_id)

@router.get(
    "/{student_id}",
    response_model=StudentRead,
    summary="Получить студента по ID",
    description="Возвращает студента по его уникальному идентификатору. Если студент не найден — 404."
)
async def get_student_by_id(student_id: int, session: AsyncSession = Depends(get_async_session)):
    """
    Получение студента по ID.
    - Проверяет существование студента
    - Возвращает 404, если не найден
    """
    student = await crud_student.get_student_by_id(session, student_id)
    if not student:
        # Если студент не найден, выбрасываем исключение
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@router.get(
    "/by_email/{email}",
    response_model=StudentRead,
    summary="Получить студента по email",
    description="Возвращает студента по email. Если студент не найден — 404."
)
async def get_student_by_email(email: str, session: AsyncSession = Depends(get_async_session)):
    """
    Получение студента по email.
    - Проверяет существование студента
    - Возвращает 404, если не найден
    """
    student = await crud_student.get_student_by_email(session, email)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@router.post(
    "/",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать нового студента",
    description="Создаёт нового студента на основе переданных данных. Можно указать group_id для привязки к группе."
)
async def create_student(student_in: StudentCreate, session: AsyncSession = Depends(get_async_session)):
    """
    Создание нового студента.
    - Проверяет валидность входных данных
    - Позволяет указать group_id для привязки к группе
    - Возвращает созданного студента
    """
    try:
        return await crud_student.create_student(session, student_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put(
    "/{student_id}",
    response_model=StudentRead,
    summary="Обновить студента",
    description="Обновляет данные студента по ID. Если студент не найден — 404."
)
async def update_student(student_id: int, student_in: StudentUpdate, session: AsyncSession = Depends(get_async_session)):
    """
    Обновление студента по ID.
    - Обновляет только переданные поля
    - Возвращает 404, если студент не найден
    """
    student = await crud_student.update_student(session, student_id, student_in)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить студента",
    description="Удаляет студента по ID. Если студент не найден — 404. Возвращает пустой ответ при успехе."
)
async def delete_student(student_id: int, session: AsyncSession = Depends(get_async_session)):
    """
    Удаление студента по ID.
    - Удаляет студента, если найден
    - Возвращает 404, если студент не найден
    """
    result = await crud_student.delete_student(session, student_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return None