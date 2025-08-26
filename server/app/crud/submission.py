from datetime import datetime, timezone
from typing import Optional, List, Tuple
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, select, func
from fastapi import HTTPException, status

from app.models.submission import Submission, SubmissionStatus
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.user import User, UserRole
from app.models.grade import Grade
from app.schemas.submission import SubmissionCreate, SubmissionUpdate
from app.schemas.grade import GradeCreate


async def get_submission(db: AsyncSession, submission_id: int) -> Optional[Submission]:
    """
    Получить сдачу задания по ID с загрузкой связанных объектов.
    
    Args:
        db: Сессия базы данных
        submission_id: ID сдачи задания
        
    Returns:
        Объект сдачи задания или None, если не найден
    """
    result = await db.execute(
        select(Submission).options(
            joinedload(Submission.student),
            joinedload(Submission.assignment).joinedload(Assignment.course),
            joinedload(Submission.grades)
        ).where(Submission.id == submission_id)
    )
    return result.unique().scalar_one_or_none()


async def get_submissions(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    student_id: Optional[int] = None,
    assignment_id: Optional[int] = None,
    course_id: Optional[int] = None
) -> Tuple[List[Submission], int]:
    """
    Получить список сдач заданий с фильтрацией и пагинацией.
    
    Args:
        db: Сессия базы данных
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
        student_id: Фильтр по студенту
        assignment_id: Фильтр по заданию
        course_id: Фильтр по курсу
        
    Returns:
        Кортеж (список сдач, общее количество)
    """
    # Базовый запрос
    query = select(Submission).options(
        joinedload(Submission.student),
        joinedload(Submission.assignment).joinedload(Assignment.course),
        joinedload(Submission.grades)
    )
    count_query = select(func.count(Submission.id))
    
    # Применяем фильтры
    if student_id:
        query = query.where(Submission.student_id == student_id)
        count_query = count_query.where(Submission.student_id == student_id)
    
    if assignment_id:
        query = query.where(Submission.assignment_id == assignment_id)
        count_query = count_query.where(Submission.assignment_id == assignment_id)
    
    if course_id:
        query = query.join(Assignment).where(Assignment.course_id == course_id)
        count_query = count_query.join(Assignment).where(Assignment.course_id == course_id)
    
    # Получаем общее количество
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Получаем сдачи с пагинацией
    submissions_result = await db.execute(query.offset(skip).limit(limit))
    submissions = submissions_result.unique().scalars().all()
    
    return list(submissions), total


async def create_submission(
    db: AsyncSession, 
    submission: SubmissionCreate, 
    current_user: User
) -> Submission:
    """
    Создать новую сдачу задания.
    
    Args:
        db: Сессия базы данных
        submission: Данные для создания сдачи
        current_user: Текущий пользователь
        
    Returns:
        Созданная сдача задания
        
    Raises:
        HTTPException: Если пользователь не студент или не записан на курс
    """
    # Проверяем, что пользователь - студент (или admin для тестирования)
    if current_user.role not in [UserRole.student, UserRole.admin]:
        logging.warning(f"User {current_user.id} tried to create submission but is not a student")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только студенты могут сдавать задания"
        )
    
    # Получаем задание с курсом
    assignment_result = await db.execute(
        select(Assignment).options(
            joinedload(Assignment.course)
        ).where(Assignment.id == submission.assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено"
        )
    
    # Проверяем, что студент записан на курс (здесь нужна модель Enrollment)
    # Пока пропускаем эту проверку, так как модель Enrollment не создана
    
    # Устанавливаем время сдачи, если не указано
    # Приводим к UTC и сохраняем в БД как наивное (TIMESTAMP WITHOUT TIME ZONE)
    submitted_at_input = submission.submitted_at or datetime.now(timezone.utc)
    if submitted_at_input.tzinfo is None or submitted_at_input.tzinfo.utcoffset(submitted_at_input) is None:
        submitted_at_aware = submitted_at_input.replace(tzinfo=timezone.utc)
    else:
        submitted_at_aware = submitted_at_input.astimezone(timezone.utc)
    submitted_at_store = submitted_at_aware.replace(tzinfo=None)

    # Нормализуем дедлайн задания к UTC (для сравнения)
    due_date_input = assignment.due_date
    if due_date_input.tzinfo is None or due_date_input.tzinfo.utcoffset(due_date_input) is None:
        due_date_aware = due_date_input.replace(tzinfo=timezone.utc)
    else:
        due_date_aware = due_date_input.astimezone(timezone.utc)

    # Определяем статус на основе времени сдачи
    status_value = SubmissionStatus.submitted
    if submitted_at_aware > due_date_aware:
        status_value = SubmissionStatus.late
        logging.info(f"Submission for assignment {assignment.id} is late")
    
    # Создаем сдачу
    db_submission = Submission(
        content=submission.content,
        submitted_at=submitted_at_store,
        status=status_value,
        student_id=current_user.id,
        assignment_id=submission.assignment_id
    )
    
    db.add(db_submission)
    await db.commit()
    await db.refresh(db_submission)
    
    logging.info(
        f"Submission created: ID={db_submission.id}, "
        f"student={current_user.id}, assignment={submission.assignment_id}, "
        f"status={status_value}"
    )
    
    # Возвращаем полностью загруженную сущность с отношениями
    return await get_submission(db, db_submission.id)


async def update_submission(
    db: AsyncSession, 
    submission_id: int, 
    submission_update: SubmissionUpdate,
    current_user: User
) -> Optional[Submission]:
    """
    Обновить сдачу задания.
    
    Args:
        db: Сессия базы данных
        submission_id: ID сдачи для обновления
        submission_update: Данные для обновления
        current_user: Текущий пользователь
        
    Returns:
        Обновленная сдача или None, если не найдена
        
    Raises:
        HTTPException: Если нет прав на обновление
    """
    db_submission = await get_submission(db, submission_id)
    if not db_submission:
        return None
    
    # Проверяем права: студент может редактировать только свои сдачи,
    # преподаватель и админ - любые
    if (current_user.role == UserRole.student and 
        db_submission.student_id != current_user.id):
        logging.warning(
            f"User {current_user.id} tried to update submission {submission_id} "
            f"but doesn't have permission"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для редактирования этой сдачи"
        )
    
    # Обновляем поля
    update_data = submission_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_submission, field, value)
    
    # Если обновляется время сдачи, пересчитываем статус
    if 'submitted_at' in update_data and db_submission.status != SubmissionStatus.graded:
        # Нормализуем значения времени к UTC для корректного сравнения
        new_submitted_at = db_submission.submitted_at
        if new_submitted_at.tzinfo is None or new_submitted_at.tzinfo.utcoffset(new_submitted_at) is None:
            new_submitted_at = new_submitted_at.replace(tzinfo=timezone.utc)

        upd_due_date = db_submission.assignment.due_date
        if upd_due_date.tzinfo is None or upd_due_date.tzinfo.utcoffset(upd_due_date) is None:
            upd_due_date = upd_due_date.replace(tzinfo=timezone.utc)
        else:
            upd_due_date = upd_due_date.astimezone(timezone.utc)

        if new_submitted_at > upd_due_date:
            db_submission.status = SubmissionStatus.late
        else:
            db_submission.status = SubmissionStatus.submitted
    
    await db.commit()
    await db.refresh(db_submission)
    
    logging.info(f"Submission {submission_id} updated by user {current_user.id}")
    
    # Возвращаем полностью загруженную сущность с отношениями
    return await get_submission(db, submission_id)


async def delete_submission(
    db: AsyncSession, 
    submission_id: int, 
    current_user: User
) -> bool:
    """
    Удалить сдачу задания.
    
    Args:
        db: Сессия базы данных
        submission_id: ID сдачи для удаления
        current_user: Текущий пользователь
        
    Returns:
        True, если сдача удалена, False, если не найдена
        
    Raises:
        HTTPException: Если нет прав на удаление
    """
    db_submission = await get_submission(db, submission_id)
    if not db_submission:
        return False
    
    # Проверяем права: студент может удалять только свои сдачи,
    # преподаватель и админ - любые
    if (current_user.role == UserRole.student and 
        db_submission.student_id != current_user.id):
        logging.warning(
            f"User {current_user.id} tried to delete submission {submission_id} "
            f"but doesn't have permission"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для удаления этой сдачи"
        )
    
    await db.delete(db_submission)
    await db.commit()
    
    logging.info(f"Submission {submission_id} deleted by user {current_user.id}")
    
    return True


async def create_grade(
    db: AsyncSession,
    submission_id: int,
    grade_data: GradeCreate,
    current_user: User
) -> Grade:
    """
    Создать оценку за сдачу задания.
    
    Args:
        db: Сессия базы данных
        submission_id: ID сдачи задания
        grade_data: Данные оценки
        current_user: Текущий пользователь (преподаватель)
        
    Returns:
        Созданная оценка
        
    Raises:
        HTTPException: Если нет прав или сдача не найдена
    """
    # Проверяем права: только преподаватели и админы могут ставить оценки
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        logging.warning(f"User {current_user.id} tried to create grade but is not teacher/admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только преподаватели и администраторы могут ставить оценки"
        )
    
    # Проверяем существование сдачи
    submission = await get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сдача задания не найдена"
        )
    
    # Проверяем, что оценка еще не выставлена
    existing_grade_result = await db.execute(
        select(Grade).where(Grade.submission_id == submission_id)
    )
    existing_grade = existing_grade_result.scalar_one_or_none()
    if existing_grade:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Оценка за эту сдачу уже выставлена"
        )
    
    # Создаем оценку
    db_grade = Grade(
        score=grade_data.score,
        feedback=grade_data.feedback,
        graded_by=current_user.id,
        submission_id=submission_id
    )
    
    # Обновляем статус сдачи
    submission.status = SubmissionStatus.graded
    
    db.add(db_grade)
    await db.commit()
    await db.refresh(db_grade)
    
    logging.info(
        f"Grade created: ID={db_grade.id}, score={grade_data.score}, "
        f"submission={submission_id}, grader={current_user.id}"
    )
    
    return db_grade