from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from fastapi import HTTPException, status
import logging

from app.models.assignment import Assignment
from app.models.course import Course
from app.models.user import User, UserRole
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate

# Настройка логирования
logger = logging.getLogger(__name__)


def get_assignment_by_id(db: Session, assignment_id: int) -> Optional[Assignment]:
    """Получить задание по ID с загрузкой связанных данных."""
    return db.query(Assignment).options(
        selectinload(Assignment.course).selectinload(Course.owner)
    ).filter(Assignment.id == assignment_id).first()


def get_assignments(
    db: Session,
    course_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[List[Assignment], int]:
    """Получить список заданий с пагинацией и фильтрацией по курсу."""
    query = db.query(Assignment).options(
        selectinload(Assignment.course).selectinload(Course.owner)
    )
    
    if course_id:
        query = query.filter(Assignment.course_id == course_id)
    
    total = query.count()
    assignments = query.offset(skip).limit(limit).all()
    
    return assignments, total


def create_assignment(db: Session, assignment: AssignmentCreate, current_user: User) -> Assignment:
    """Создать новое задание с проверками прав и валидацией дедлайна."""
    # Проверка прав пользователя
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        logger.warning(f"Пользователь {current_user.id} пытался создать задание без прав")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только преподаватели и администраторы могут создавать задания"
        )
    
    # Проверка существования курса
    course = db.query(Course).filter(Course.id == assignment.course_id).first()
    if not course:
        logger.error(f"Попытка создать задание для несуществующего курса {assignment.course_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Курс не найден"
        )
    
    # Проверка прав на курс: только владелец курса или админ может создавать задания
    if current_user.role != UserRole.admin and course.owner_id != current_user.id:
        logger.warning(f"Пользователь {current_user.id} пытался создать задание для чужого курса {assignment.course_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете создавать задания только для своих курсов"
        )
    
    # Валидация дедлайна: должен быть в пределах курса
    if assignment.due_date < course.start_date or assignment.due_date > course.end_date:
        logger.warning(f"Попытка создать задание с дедлайном вне периода курса")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Дедлайн задания должен быть в пределах курса ({course.start_date} - {course.end_date})"
        )
    
    # Создание задания
    db_assignment = Assignment(**assignment.model_dump())
    
    try:
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        
        # Загрузка связанных данных
        db_assignment = get_assignment_by_id(db, db_assignment.id)
        
        logger.info(f"Задание '{db_assignment.title}' создано пользователем {current_user.id} для курса {assignment.course_id}")
        return db_assignment
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка создания задания: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании задания"
        )


def update_assignment(
    db: Session,
    assignment_id: int,
    assignment_update: AssignmentUpdate,
    current_user: User
) -> Optional[Assignment]:
    """Обновить задание с проверкой прав и валидацией."""
    db_assignment = get_assignment_by_id(db, assignment_id)
    if not db_assignment:
        return None
    
    # Проверка прав: только владелец курса или админ может обновлять задания
    if current_user.role != UserRole.admin and db_assignment.course.owner_id != current_user.id:
        logger.warning(f"Пользователь {current_user.id} пытался обновить чужое задание {assignment_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете обновлять только задания своих курсов"
        )
    
    # Валидация дедлайна при обновлении
    if assignment_update.due_date:
        course = db_assignment.course
        if assignment_update.due_date < course.start_date or assignment_update.due_date > course.end_date:
            logger.warning(f"Попытка обновить задание с дедлайном вне периода курса")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Дедлайн задания должен быть в пределах курса ({course.start_date} - {course.end_date})"
            )
    
    # Обновление полей
    update_data = assignment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assignment, field, value)
    
    try:
        db.commit()
        db.refresh(db_assignment)
        
        logger.info(f"Задание {assignment_id} обновлено пользователем {current_user.id}")
        return get_assignment_by_id(db, assignment_id)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка обновления задания: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении задания"
        )


def delete_assignment(db: Session, assignment_id: int, current_user: User) -> bool:
    """Удалить задание с проверкой прав."""
    db_assignment = get_assignment_by_id(db, assignment_id)
    if not db_assignment:
        return False
    
    # Проверка прав: только владелец курса или админ может удалять задания
    if current_user.role != UserRole.admin and db_assignment.course.owner_id != current_user.id:
        logger.warning(f"Пользователь {current_user.id} пытался удалить чужое задание {assignment_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалять только задания своих курсов"
        )
    
    try:
        db.delete(db_assignment)
        db.commit()
        
        logger.info(f"Задание {assignment_id} удалено пользователем {current_user.id}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления задания {assignment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении задания"
        )