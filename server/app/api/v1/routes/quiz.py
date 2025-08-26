from __future__ import annotations

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, Quiz, 
    QuestionCreate, QuestionUpdate, Question,
    QuizAttemptCreate, QuizAttempt, AnswerCreate
)
from app.crud import quiz as quiz_crud


router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.get("/", response_model=List[Quiz], summary="List all quizzes")
async def list_all_quizzes(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    # admin/demo listing across all courses
    # simple select all
    items = await quiz_crud.list_quizzes_by_course(db, course_id=-1)  # placeholder not used; will replace below
    # Replace with raw select all to avoid creating a generic util now
    from sqlalchemy import select
    from app.models.quiz import Quiz as QuizModel
    result = await db.execute(select(QuizModel))
    return result.scalars().all()


@router.get("/courses/{course_id}/quizzes", response_model=List[Quiz], summary="List quizzes by course")
async def get_quizzes_by_course(course_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await quiz_crud.list_quizzes_by_course(db, course_id)


@router.post("/", response_model=Quiz, status_code=status.HTTP_201_CREATED, summary="Create quiz")
async def create_quiz(payload: QuizCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await quiz_crud.create_quiz(db, payload, created_by=current_user.id)


@router.get("/{quiz_id}", response_model=Quiz, summary="Get quiz by id")
async def get_quiz(quiz_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    q = await quiz_crud.get_quiz(db, quiz_id)
    if not q:
        raise HTTPException(status_code=404, detail="Квиз не найден")
    return q


@router.put("/{quiz_id}", response_model=Quiz, summary="Update quiz")
async def update_quiz(quiz_id: int, payload: QuizUpdate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    q = await quiz_crud.update_quiz(db, quiz_id, payload.dict(exclude_unset=True))
    if not q:
        raise HTTPException(status_code=404, detail="Квиз не найден")
    return q


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete quiz")
async def delete_quiz(quiz_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    ok = await quiz_crud.delete_quiz(db, quiz_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Квиз не найден")
    return


# ---- Questions ----

@router.get("/{quiz_id}/questions", response_model=List[Question], summary="List quiz questions")
async def list_questions(quiz_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await quiz_crud.list_questions(db, quiz_id)


@router.post("/{quiz_id}/questions/", response_model=Question, status_code=status.HTTP_201_CREATED, summary="Add question")
async def add_question(quiz_id: int, payload: QuestionCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    if payload.quiz_id != quiz_id:
        raise HTTPException(status_code=400, detail="quiz_id mismatch")
    return await quiz_crud.create_question(db, payload)


@router.put("/questions/{question_id}", response_model=Question, summary="Update question")
async def update_question(question_id: int, payload: QuestionUpdate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    q = await quiz_crud.update_question(db, question_id, payload)
    if not q:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    return q


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete question")
async def delete_question(question_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    ok = await quiz_crud.delete_question(db, question_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    return


# ---- Attempts ----

@router.post("/{quiz_id}/attempts/", response_model=QuizAttempt, status_code=status.HTTP_201_CREATED, summary="Start attempt")
async def start_attempt(quiz_id: int, payload: QuizAttemptCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    if payload.quiz_id != quiz_id:
        raise HTTPException(status_code=400, detail="quiz_id mismatch")
    return await quiz_crud.create_attempt(db, payload, student_id=current_user.id)


@router.post("/{attempt_id}/submit/", summary="Submit attempt")
async def submit_attempt(attempt_id: int, answers: List[AnswerCreate], db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    attempt = await quiz_crud.submit_attempt(db, attempt_id, answers)
    if not attempt:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    # simple response summarizing
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.quiz import QuizAttempt as AttemptModel
    result = await db.execute(select(AttemptModel).filter(AttemptModel.id == attempt.id))
    att = result.scalar_one()
    return {"attempt_id": att.id, "score": att.score}


@router.get("/attempts/{attempt_id}/results", response_model=QuizAttempt, summary="Attempt results")
async def get_attempt_results(attempt_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    attempt = await quiz_crud.get_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    return attempt


