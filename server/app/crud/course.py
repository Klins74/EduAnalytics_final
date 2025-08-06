from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from fastapi import HTTPException, status
import logging

from app.models.course import Course
from app.models.user import User, UserRole
from app.schemas.course import CourseCreate, CourseUpdate

# Настройка логирования
logger = logging.getLogger(__name__)


def get_course_by_id(db: Session, course_id: int) -> Optional[Course]:
    """Получить курс по ID с загрузкой связанных данных."""
    return db.query(Course).options(
        selectinload(Course.owner)
    ).filter(Course.id == course_id).first()


def get_courses(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    owner_id: Optional[int] = None
) -> tuple[List[Course], int]:
    """Получить список курсов с пагинацией и фильтрацией."""
    query = db.query(Course).options(selectinload(Course.owner))
    
    if owner_id:
        query = query.filter(Course.owner_id == owner_id)
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    
    return courses, total


def create_course(db: Session, course: CourseCreate, current_user: User) -> Course:
    """Создать новый курс с проверками прав и валидацией."""
    # Проверка прав пользователя
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        logger.warning(f"Пользователь {current_user.id} пытался создать курс без прав")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только преподаватели и администраторы могут создавать курсы"
        )
    
    # Проверка существования владельца курса
    owner = db.query(User).filter(
        and_(
            User.id == course.owner_id,
            User.role.in_([UserRole.teacher, UserRole.admin])
        )
    ).first()
    
    if not owner:
        logger.error(f"Попытка создать курс с несуществующим или неподходящим владельцем {course.owner_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Владелец курса должен быть преподавателем или администратором"
        )
    
    # Создание курса
    db_course = Course(**course.model_dump())
    
    try:
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        
        # Загрузка связанных данных
        db_course = get_course_by_id(db, db_course.id)
        
        logger.info(f"Курс '{db_course.title}' создан пользователем {current_user.id}")
        return db_course
        
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: courses.title" in str(e):
            logger.warning(f"Попытка создать курс с существующим названием: {course.title}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Курс с названием '{course.title}' уже существует"
            )
        else:
            logger.error(f"Ошибка создания курса: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании курса"
            )


def update_course(
    db: Session, 
    course_id: int, 
    course_update: CourseUpdate,
    current_user: User
) -> Optional[Course]:
    """Обновить курс с проверкой прав."""
    db_course = get_course_by_id(db, course_id)
    if not db_course:
        return None
    
    # Проверка прав: только владелец курса или админ может обновлять
    if current_user.role != UserRole.admin and db_course.owner_id != current_user.id:
        logger.warning(f"Пользователь {current_user.id} пытался обновить чужой курс {course_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете обновлять только свои курсы"
        )
    
    # Обновление полей
    update_data = course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)
    
    try:
        db.commit()
        db.refresh(db_course)
        
        logger.info(f"Курс {course_id} обновлен пользователем {current_user.id}")
        return get_course_by_id(db, course_id)
        
    except IntegrityError as e:
        db.rollback()
        if "UNIQUE constraint failed: courses.title" in str(e):
            logger.warning(f"Попытка обновить курс с существующим названием")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Курс с таким названием уже существует"
            )
        else:
            logger.error(f"Ошибка обновления курса: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обновлении курса"
            )


def delete_course(db: Session, course_id: int, current_user: User) -> bool:
    """Удалить курс с проверкой прав."""
    db_course = get_course_by_id(db, course_id)
    if not db_course:
        return False
    
    # Проверка прав: только владелец курса или админ может удалять
    if current_user.role != UserRole.admin and db_course.owner_id != current_user.id:
        logger.warning(f"Пользователь {current_user.id} пытался удалить чужой курс {course_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалять только свои курсы"
        )
    
    try:
        db.delete(db_course)
        db.commit()
        
        logger.info(f"Курс {course_id} удален пользователем {current_user.id}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления курса {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении курса"
        )