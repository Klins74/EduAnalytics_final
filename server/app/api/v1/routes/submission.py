from typing import Optional
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user, require_role as _require_role, audit_event
from app.models.user import User, UserRole
from app.schemas.submission import (
    SubmissionCreate, 
    SubmissionUpdate, 
    SubmissionRead, 
    SubmissionList
)
from app.schemas.grade import GradeCreate, GradeResponse
from app.crud import submission as crud_submission
from app.services.cache import analytics_cache


router = APIRouter()


@router.get(
    "/",
    response_model=SubmissionList,
    summary="Получить список сдач заданий",
    description="Получить список всех сдач заданий с возможностью фильтрации по студенту, заданию или курсу. Поддерживает пагинацию.",
    responses={
        200: {"description": "Список сдач заданий успешно получен"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"}
    },
    tags=["Submissions"]
)
async def get_submissions(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    assignment_id: Optional[int] = None,
    course_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(_require_role(UserRole.teacher, UserRole.admin, UserRole.student))
):
    """
    Получить список сдач заданий.
    
    - **skip**: количество записей для пропуска (для пагинации)
    - **limit**: максимальное количество записей (максимум 100)
    - **student_id**: фильтр по ID студента
    - **assignment_id**: фильтр по ID задания
    - **course_id**: фильтр по ID курса
    
    Студенты видят только свои сдачи, преподаватели и админы - все.
    """
    # Ограничиваем лимит
    limit = min(limit, 100)
    
    # Студенты могут видеть только свои сдачи
    if current_user.role == UserRole.student:
        student_id = current_user.id
    
    submissions, total = await crud_submission.get_submissions(
        db=db,
        skip=skip,
        limit=limit,
        student_id=student_id,
        assignment_id=assignment_id,
        course_id=course_id
    )
    
    logging.info(
        f"User {current_user.id} retrieved {len(submissions)} submissions "
        f"(total: {total}, skip: {skip}, limit: {limit})"
    )
    
    return SubmissionList(
        submissions=submissions,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{submission_id}",
    response_model=SubmissionRead,
    summary="Получить сдачу задания по ID",
    description="Получить детальную информацию о конкретной сдаче задания, включая связанные объекты (задание, студент, оценки).",
    responses={
        200: {"description": "Сдача задания найдена"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Сдача задания не найдена"}
    },
    tags=["Submissions"]
)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(_require_role(UserRole.teacher, UserRole.admin, UserRole.student))
):
    """
    Получить сдачу задания по ID.
    
    Студенты могут просматривать только свои сдачи,
    преподаватели и администраторы - любые.
    """
    submission = await crud_submission.get_submission(db=db, submission_id=submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сдача задания не найдена"
        )
    
    # Проверяем права доступа
    if (current_user.role == UserRole.student and 
        submission.student_id != current_user.id):
        logging.warning(
            f"User {current_user.id} tried to access submission {submission_id} "
            f"but doesn't have permission"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для просмотра этой сдачи"
        )
    
    logging.info(f"User {current_user.id} retrieved submission {submission_id}")
    return submission


@router.post(
    "/",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую сдачу задания",
    description="Создать новую сдачу задания. Только студенты могут сдавать задания. Автоматически определяется статус (вовремя/просрочено) на основе времени сдачи и дедлайна.",
    responses={
        201: {"description": "Сдача задания успешно создана"},
        400: {"description": "Некорректные данные"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав (только студенты)"},
        404: {"description": "Задание не найдено"}
    },
    tags=["Submissions"]
)
async def create_submission(
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новую сдачу задания.
    
    - **content**: содержимое сдачи (текст решения, ссылка на репозиторий и т.д.)
    - **assignment_id**: ID задания, для которого создается сдача
    - **submitted_at**: время сдачи (опционально, по умолчанию - текущее время)
    
    Статус сдачи определяется автоматически:
    - "submitted" - если сдано вовремя
    - "late" - если сдано после дедлайна
    """
    try:
        db_submission = await crud_submission.create_submission(
            db=db, 
            submission=submission, 
            current_user=current_user
        )
        logging.info(f"Submission created successfully: ID={db_submission.id}")
        # Invalidate analytics caches related to the assignment/course and student
        if hasattr(db_submission, 'assignment_id'):
            # Try to clear course caches via assignment's course id if resolvable in CRUD (not here)
            pass
        await analytics_cache.invalidate_student(current_user.id)
        return db_submission
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании сдачи задания"
        )


@router.put(
    "/{submission_id}",
    response_model=SubmissionRead,
    summary="Обновить сдачу задания",
    description="Обновить существующую сдачу задания. Студенты могут редактировать только свои сдачи, преподаватели и админы - любые.",
    responses={
        200: {"description": "Сдача задания успешно обновлена"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Сдача задания не найдена"}
    },
    tags=["Submissions"]
)
async def update_submission(
    submission_id: int,
    submission_update: SubmissionUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить сдачу задания.
    
    Можно обновить содержимое сдачи и время сдачи.
    При изменении времени сдачи статус пересчитывается автоматически.
    """
    try:
        updated_submission = await crud_submission.update_submission(
            db=db,
            submission_id=submission_id,
            submission_update=submission_update,
            current_user=current_user
        )
        
        if not updated_submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сдача задания не найдена"
            )
        
        logging.info(f"Submission {submission_id} updated successfully")
        await analytics_cache.invalidate_student(current_user.id)
        return updated_submission
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении сдачи задания"
        )


@router.delete(
    "/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить сдачу задания",
    description="Удалить сдачу задания. Студенты могут удалять только свои сдачи, преподаватели и админы - любые.",
    responses={
        204: {"description": "Сдача задания успешно удалена"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Сдача задания не найдена"}
    },
    tags=["Submissions"]
)
async def delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить сдачу задания.
    
    При удалении сдачи также удаляются все связанные оценки.
    """
    try:
        # Fetch to invalidate correct student
        existing = await crud_submission.get_submission(db=db, submission_id=submission_id)
        deleted = await crud_submission.delete_submission(
            db=db,
            submission_id=submission_id,
            current_user=current_user
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сдача задания не найдена"
            )
        
        logging.info(f"Submission {submission_id} deleted successfully")
        if existing:
            await analytics_cache.invalidate_student(existing.student_id)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении сдачи задания"
        )


@router.post(
    "/{submission_id}/grade",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Поставить оценку за сдачу",
    description="Поставить оценку за сдачу задания. Только преподаватели и администраторы могут ставить оценки. После выставления оценки статус сдачи меняется на 'graded'.",
    responses={
        201: {"description": "Оценка успешно выставлена"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав (только преподаватели и админы)"},
        404: {"description": "Сдача задания не найдена"},
        409: {"description": "Оценка уже выставлена"}
    },
    tags=["Submissions"]
)
async def create_grade(
    submission_id: int,
    grade_data: GradeCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(_require_role(UserRole.teacher, UserRole.admin))
):
    """
    Поставить оценку за сдачу задания.
    
    - **score**: оценка от 0 до 100
    - **feedback**: комментарий преподавателя (опционально)
    
    После выставления оценки:
    1. Статус сдачи меняется на "graded"
    2. Создается запись в таблице оценок
    3. Отправляется уведомление студенту (через n8n-флоу)
    """
    try:
        grade = await crud_submission.create_grade(
            db=db,
            submission_id=submission_id,
            grade_data=grade_data,
            current_user=current_user
        )
        
        logging.info(
            f"Grade created successfully: ID={grade.id}, "
            f"score={grade.score}, submission={submission_id}"
        )
        
        # TODO: Интеграция с n8n для отправки уведомления
        # await send_grade_notification(submission_id, grade.score)
        
        return grade
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating grade for submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выставлении оценки"
        )


@router.post(
    "/{submission_id}/upload",
    summary="Загрузить файл для сдачи",
    description="Загрузить файл (документ, изображение, архив) для сдачи задания. Поддерживаемые форматы: PDF, DOC, DOCX, TXT, JPG, PNG, ZIP, RAR.",
    responses={
        200: {"description": "Файл успешно загружен"},
        400: {"description": "Некорректный файл"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Сдача задания не найдена"},
        413: {"description": "Файл слишком большой"}
    },
    tags=["Submissions"]
)
async def upload_file(
    submission_id: int,
    file: UploadFile = File(..., description="Файл для загрузки"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Загрузить файл для сдачи задания.
    
    - **file**: Файл для загрузки (максимум 10MB)
    - **submission_id**: ID сдачи задания
    
    Поддерживаемые форматы:
    - Документы: PDF, DOC, DOCX, TXT
    - Изображения: JPG, PNG
    - Архивы: ZIP, RAR
    
    Файл сохраняется в папку uploads/submissions/{submission_id}/
    """
    # Проверяем размер файла (максимум 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл слишком большой. Максимальный размер: 10MB"
        )
    
    # Проверяем расширение файла
    allowed_extensions = {
        '.pdf', '.doc', '.docx', '.txt',  # Документы
        '.jpg', '.jpeg', '.png',          # Изображения
        '.zip', '.rar'                    # Архивы
    }
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(allowed_extensions)}"
        )
    
    # Проверяем существование сдачи
    submission = await crud_submission.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сдача задания не найдена"
        )
    
    # Проверяем права: студент может загружать файлы только для своих сдач
    if (current_user.role == UserRole.student and 
        submission.student_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для загрузки файла для этой сдачи"
        )
    
    # Создаем папку для файлов сдачи
    upload_dir = f"uploads/submissions/{submission_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    import uuid
    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
    
    try:
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Обновляем сдачу, добавляя информацию о файле
        submission.file_path = file_path
        submission.file_name = file.filename
        submission.file_size = len(content)
        
        await db.commit()
        await db.refresh(submission)
        
        logging.info(
            f"File uploaded successfully: {file.filename} "
            f"for submission {submission_id} by user {current_user.id}"
        )
        
        return {
            "message": "Файл успешно загружен",
            "file_name": file.filename,
            "file_size": len(content),
            "file_path": file_path
        }
        
    except Exception as e:
        logging.error(f"Error uploading file for submission {submission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при загрузке файла"
        )


@router.get(
    "/{submission_id}/download/{file_id}",
    summary="Скачать файл сдачи",
    description="Скачать файл, загруженный для сдачи задания",
    responses={
        200: {"description": "Файл найден"},
        401: {"description": "Не авторизован"},
        403: {"description": "Недостаточно прав"},
        404: {"description": "Файл не найден"}
    },
    tags=["Submissions"]
)
async def download_file(
    submission_id: int,
    file_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Скачать файл сдачи задания.
    
    - **submission_id**: ID сдачи задания
    - **file_id**: ID файла (UUID)
    """
    # Проверяем существование сдачи
    submission = await crud_submission.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сдача задания не найдена"
        )
    
    # Проверяем права доступа
    if (current_user.role == UserRole.student and 
        submission.student_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для скачивания файла этой сдачи"
        )
    
    # Проверяем, что файл существует
    if not submission.file_path or not os.path.exists(submission.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден"
        )
    
    # Возвращаем файл для скачивания
    return FileResponse(
        submission.file_path,
        filename=submission.file_name or f"submission_{submission_id}.file",
        media_type="application/octet-stream"
    )