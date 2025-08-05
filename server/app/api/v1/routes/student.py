from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_async_session
from app.schemas.student import StudentCreate, StudentUpdate, StudentRead
from app.crud.student import get_student_by_id, get_all_students, create_student, update_student, delete_student
from fastapi.security import OAuth2PasswordBearer
from ..routes.users import get_current_user

router = APIRouter()

@router.get("/students", response_model=List[StudentRead], summary="Получить всех студентов", status_code=200)
async def read_students(db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    students = await get_all_students(db)
    return students

@router.get("/students/{student_id}", response_model=StudentRead, summary="Получить студента по ID", status_code=200)
async def read_student(student_id: int, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    student = await get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student

@router.post("/students", response_model=StudentRead, summary="Создать студента", status_code=201)
async def create_new_student(student_in: StudentCreate, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    student = await create_student(db, student_in)
    return student

@router.put("/students/{student_id}", response_model=StudentRead, summary="Обновить студента по ID", status_code=200)
async def update_existing_student(student_id: int, student_in: StudentUpdate, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    student = await update_student(db, student_id, student_in)
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return student

@router.delete("/students/{student_id}", summary="Удалить студента по ID", status_code=204)
async def delete_existing_student(student_id: int, db: AsyncSession = Depends(get_async_session), current_user: dict = Depends(get_current_user)):
    success = await delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Студент не найден")
    return None