from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.db.session import get_async_session
from app.models import Grade, Student, User
from app.schemas import GradeCreate, GradeResponse
from app.core.security import get_current_user, require_role
from app.models.user import UserRole

router = APIRouter(tags=["Grades"])

@router.get("/", response_model=list[GradeResponse])
async def get_grades(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Grade))
    return result.scalars().all()

@router.post("/", response_model=GradeResponse, status_code=201)
async def create_grade(
    grade_in: GradeCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    try:
        print("create_grade input:", grade_in)
        grade = Grade(value=grade_in.value, student_id=grade_in.student_id, subject=grade_in.subject)
        db.add(grade)
        await db.commit()
        await db.refresh(grade)
        print("created grade:", grade)
        return grade
    except IntegrityError:
        await db.rollback()
        print("IntegrityError in create_grade")
        raise HTTPException(status_code=400, detail="Ошибка при создании оценки")
    except Exception as e:
        import traceback
        await db.rollback()
        print("Exception in create_grade:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{grade_id}", response_model=GradeResponse)
async def get_grade(grade_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    return grade

@router.put("/{grade_id}", response_model=GradeResponse)
async def update_grade(
    grade_id: int,
    grade_in: GradeCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    for key, value in grade_in.dict().items():
        setattr(grade, key, value)
    try:
        await db.commit()
        await db.refresh(grade)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ошибка при обновлении оценки")
    return grade

@router.delete("/{grade_id}", status_code=204)
async def delete_grade(
    grade_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.admin))
):
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    await db.delete(grade)
    await db.commit()
    return None