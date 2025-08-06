from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_async_session
from app.schemas.student import StudentCreate, StudentUpdate, StudentRead
from app.crud.student import get_student_by_id, get_all_students, create_student, update_student, delete_student
from app.core.security import get_current_user, require_role
from app.models.user import UserRole

router = APIRouter()

@router.get("/", response_model=List[StudentRead], summary="Получить всех студентов", status_code=200)
async def read_students(db: AsyncSession = Depends(get_async_session), current_user = Depends(get_current_user)):
    return await get_all_students(db)

@router.get("/{student_id}", response_model=StudentRead, summary="Получить студента по ID", status_code=200)
async def read_student(student_id: int, db: AsyncSession = Depends(get_async_session), current_user = Depends(get_current_user)):
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student

@router.post("/", response_model=StudentRead, summary="Создать студента", status_code=201)
async def create_new_student(student_in: StudentCreate, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.teacher, UserRole.admin))):
    try:
        return await create_student(db, student_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{student_id}", response_model=StudentRead, summary="Обновить студента по ID", status_code=200)
async def update_existing_student(student_id: int, student_in: StudentUpdate, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.teacher, UserRole.admin))):
    student = await update_student(db, student_id, student_in)
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student

@router.delete("/{student_id}", summary="Удалить студента по ID", status_code=204)
async def delete_existing_student(student_id: int, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    success = await delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return None