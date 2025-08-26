from typing import Optional, List, Dict, Literal
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
from datetime import datetime, timezone, timedelta

from app.db.session import get_async_session
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.submission import Submission, SubmissionStatus
from app.models.grade import Grade
from app.models.student import Student
from app.models.group import Group

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Analytics"],
    prefix="/analytics"
)


@router.get(
    "/courses/{course_id}/overview",
    summary="Обзор аналитики курса",
    description="Получить общую статистику по курсу: количество студентов, заданий, средняя успеваемость"
)
async def get_course_overview(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить общий обзор курса с ключевыми метриками."""
    
    # Проверяем права доступа
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра аналитики курса"
        )
    
    try:
        # Получаем курс
        course_result = await db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Курс не найден"
            )
        
        # Проверяем, что пользователь - владелец курса или админ
        if current_user.role != UserRole.admin and course.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра аналитики этого курса"
            )
        
        # Подсчитываем количество заданий
        assignments_count_result = await db.execute(
            select(func.count(Assignment.id)).where(Assignment.course_id == course_id)
        )
        assignments_count = assignments_count_result.scalar()
        
        # Подсчитываем количество студентов (временно возвращаем 0, так как связь Group-Course не реализована)
        # TODO: Реализовать связь Group-Course или использовать другой подход
        students_count = 0
        
        # Подсчитываем количество сдач
        submissions_count_result = await db.execute(
            select(func.count(Submission.id))
            .select_from(Submission)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .where(Assignment.course_id == course_id)
        )
        submissions_count = submissions_count_result.scalar()
        
        # Подсчитываем среднюю оценку
        avg_grade_result = await db.execute(
            select(func.avg(Grade.score))
            .select_from(Grade)
            .join(Submission, Grade.submission_id == Submission.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .where(Assignment.course_id == course_id)
        )
        avg_grade = avg_grade_result.scalar() or 0.0
        
        # Подсчитываем процент вовремя сданных заданий
        on_time_submissions_result = await db.execute(
            select(func.count(Submission.id))
            .select_from(Submission)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .where(
                and_(
                    Assignment.course_id == course_id,
                    Submission.status == SubmissionStatus.submitted,
                    Submission.submitted_at <= Assignment.due_date
                )
            )
        )
        on_time_submissions = on_time_submissions_result.scalar()
        
        completion_rate = 0.0
        if assignments_count > 0 and students_count > 0:
            total_possible_submissions = assignments_count * students_count
            completion_rate = (submissions_count / total_possible_submissions) * 100 if total_possible_submissions > 0 else 0.0
        
        on_time_rate = 0.0
        if submissions_count > 0:
            on_time_rate = (on_time_submissions / submissions_count) * 100
        
        return {
            "course_id": course_id,
            "course_title": course.title,
            "overview": {
                "students_count": students_count,
                "assignments_count": assignments_count,
                "submissions_count": submissions_count,
                "average_grade": round(avg_grade, 2),
                "completion_rate": round(completion_rate, 2),
                "on_time_submission_rate": round(on_time_rate, 2)
            },
            "period": {
                "start_date": course.start_date,
                "end_date": course.end_date,
                "duration_days": (course.end_date - course.start_date).days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting course overview for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении аналитики курса"
        )


@router.get(
    "/courses/{course_id}/assignments",
    summary="Аналитика заданий курса",
    description="Получить статистику по заданиям курса: количество сдач, средние оценки, сроки"
)
async def get_course_assignments_analytics(
    course_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить аналитику по заданиям конкретного курса."""
    
    # Проверяем права доступа
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра аналитики"
        )
    
    try:
        # Получаем все задания курса с аналитикой
        assignments_result = await db.execute(
            select(Assignment).where(Assignment.course_id == course_id)
        )
        assignments = assignments_result.scalars().all()
        
        assignments_analytics = []
        
        for assignment in assignments:
            # Подсчитываем количество сдач для задания
            submissions_count_result = await db.execute(
                select(func.count(Submission.id)).where(Submission.assignment_id == assignment.id)
            )
            submissions_count = submissions_count_result.scalar()
            
            # Подсчитываем среднюю оценку
            avg_grade_result = await db.execute(
                select(func.avg(Grade.score))
                .select_from(Grade)
                .join(Submission, Grade.submission_id == Submission.id)
                .where(Submission.assignment_id == assignment.id)
            )
            avg_grade = avg_grade_result.scalar() or 0.0
            
            # Подсчитываем количество вовремя сданных
            on_time_count_result = await db.execute(
                select(func.count(Submission.id))
                .select_from(Submission)
                .where(
                    and_(
                        Submission.assignment_id == assignment.id,
                        Submission.status == SubmissionStatus.submitted,
                        Submission.submitted_at <= assignment.due_date
                    )
                )
            )
            on_time_count = on_time_count_result.scalar()
            
            # Подсчитываем количество опоздавших
            late_count_result = await db.execute(
                select(func.count(Submission.id))
                .select_from(Submission)
                .where(
                    and_(
                        Submission.assignment_id == assignment.id,
                        Submission.status == SubmissionStatus.submitted,
                        Submission.submitted_at > assignment.due_date
                    )
                )
            )
            late_count = late_count_result.scalar()
            
            assignments_analytics.append({
                "assignment_id": assignment.id,
                "title": assignment.title,
                "due_date": assignment.due_date,
                "statistics": {
                    "total_submissions": submissions_count,
                    "average_grade": round(avg_grade, 2),
                    "on_time_submissions": on_time_count,
                    "late_submissions": late_count,
                    "submission_rate": 0.0  # TODO: заменить на реальное количество студентов, когда связь Group-Course будет реализована
                }
            })
        
        return {
            "course_id": course_id,
            "assignments_analytics": assignments_analytics
        }
        
    except Exception as e:
        logger.error(f"Error getting assignments analytics for course {course_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении аналитики заданий"
        )


@router.get(
    "/students/{student_id}/performance",
    summary="Успеваемость студента",
    description="Получить аналитику успеваемости конкретного студента по всем курсам"
)
async def get_student_performance(
    student_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить аналитику успеваемости студента."""
    
    # Проверяем права доступа
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра аналитики студента"
        )
    
    try:
        # Получаем студента
        student_result = await db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Студент не найден"
            )
        
        # Получаем все сдачи студента с оценками
        submissions_result = await db.execute(
            select(Submission, Assignment, Course, Grade)
            .select_from(Submission)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Course, Assignment.course_id == Course.id)
            .outerjoin(Grade, Submission.id == Grade.submission_id)
            .where(Submission.student_id == student_id)
        )
        
        submissions_data = submissions_result.all()
        
        # Группируем по курсам
        courses_performance = {}
        
        for submission, assignment, course, grade in submissions_data:
            if course.id not in courses_performance:
                courses_performance[course.id] = {
                    "course_id": course.id,
                    "course_title": course.title,
                    "assignments_count": 0,
                    "submissions_count": 0,
                    "grades": [],
                    "average_grade": 0.0,
                    "on_time_rate": 0.0
                }
            
            course_data = courses_performance[course.id]
            course_data["assignments_count"] += 1
            course_data["submissions_count"] += 1
            
            if grade:
                course_data["grades"].append(grade.score)
            
            # Проверяем, вовремя ли сдано
            if submission.submitted_at <= assignment.due_date:
                course_data["on_time_rate"] += 1
        
        # Вычисляем средние значения
        for course_data in courses_performance.values():
            if course_data["grades"]:
                course_data["average_grade"] = round(sum(course_data["grades"]) / len(course_data["grades"]), 2)
            
            if course_data["submissions_count"] > 0:
                course_data["on_time_rate"] = round((course_data["on_time_rate"] / course_data["submissions_count"]) * 100, 2)
        
        # Общая статистика
        all_grades = [grade.score for _, _, _, grade in submissions_data if grade]
        overall_average = round(sum(all_grades) / len(all_grades), 2) if all_grades else 0.0
        
        return {
            "student_id": student_id,
            "student_name": student.full_name,
            "overall_performance": {
                "total_submissions": len(submissions_data),
                "total_assignments": sum(course["assignments_count"] for course in courses_performance.values()),
                "overall_average_grade": overall_average,
                "courses_count": len(courses_performance)
            },
            "courses_performance": list(courses_performance.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting student performance for student {student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении аналитики студента"
        )


@router.get(
    "/dashboard/summary",
    summary="Общая сводка системы",
    description="Получить общую статистику по всей системе: курсы, студенты, задания, успеваемость"
)
async def get_system_summary(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.admin))
):
    """Получить общую сводку по системе (только для админов)."""
    
    try:
        # Общее количество курсов
        courses_count_result = await db.execute(select(func.count(Course.id)))
        courses_count = courses_count_result.scalar()
        
        # Общее количество студентов
        students_count_result = await db.execute(select(func.count(Student.id)))
        students_count = students_count_result.scalar()
        
        # Общее количество заданий
        assignments_count_result = await db.execute(select(func.count(Assignment.id)))
        assignments_count = assignments_count_result.scalar()
        
        # Общее количество сдач
        submissions_count_result = await db.execute(select(func.count(Submission.id)))
        submissions_count = submissions_count_result.scalar()
        
        # Общее количество оценок
        grades_count_result = await db.execute(select(func.count(Grade.id)))
        grades_count = grades_count_result.scalar()
        
        # Средняя оценка по системе
        avg_grade_result = await db.execute(select(func.avg(Grade.score)))
        avg_grade = avg_grade_result.scalar() or 0.0
        
        # Активные курсы (не завершенные)
        # Используем наивное время для сравнения с TIMESTAMP WITHOUT TIME ZONE
        current_time = datetime.now().replace(tzinfo=None)
        active_courses_result = await db.execute(
            select(func.count(Course.id))
            .where(Course.end_date > current_time)
        )
        active_courses = active_courses_result.scalar()
        
        return {
            "system_overview": {
                "total_courses": courses_count,
                "active_courses": active_courses,
                "total_students": students_count,
                "total_assignments": assignments_count,
                "total_submissions": submissions_count,
                "total_grades": grades_count,
                "system_average_grade": round(avg_grade, 2)
            },
            "generated_at": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        logger.error(f"Error getting system summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении сводки системы"
        )


@router.get(
    "/teacher/{teacher_id}/overview",
    summary="Обзор преподавателя",
    description="Получить статистику по курсам и студентам конкретного преподавателя"
)
async def get_teacher_overview(
    teacher_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Получить обзор для конкретного преподавателя."""
    
    # Проверяем права доступа
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра аналитики"
        )
    
    # Проверяем, что пользователь - сам преподаватель или админ
    if current_user.role != UserRole.admin and current_user.id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра аналитики другого преподавателя"
        )
    
    try:
        # Получаем курсы преподавателя
        courses_result = await db.execute(
            select(Course).where(Course.owner_id == teacher_id)
        )
        courses = courses_result.scalars().all()
        courses_count = len(courses)
        
        # Подсчитываем общее количество заданий
        total_assignments = 0
        total_submissions = 0
        total_grades = 0
        grades_sum = 0
        
        for course in courses:
            # Задания курса
            assignments_result = await db.execute(
                select(Assignment).where(Assignment.course_id == course.id)
            )
            course_assignments = assignments_result.scalars().all()
            total_assignments += len(course_assignments)
            
            # Сдачи и оценки
            for assignment in course_assignments:
                submissions_result = await db.execute(
                    select(Submission).where(Submission.assignment_id == assignment.id)
                )
                assignment_submissions = submissions_result.scalars().all()
                total_submissions += len(assignment_submissions)
                
                # Получаем оценки для сдач
                for submission in assignment_submissions:
                    grades_result = await db.execute(
                        select(Grade).where(Grade.submission_id == submission.id)
                    )
                    submission_grades = grades_result.scalars().all()
                    if submission_grades:
                        total_grades += len(submission_grades)
                        for grade in submission_grades:
                            grades_sum += grade.score
        
        # Вычисляем среднюю оценку
        average_grade = round(grades_sum / total_grades, 2) if total_grades > 0 else 0.0
        
        # Подсчитываем pending submissions
        pending_submissions_result = await db.execute(
            select(func.count(Submission.id))
            .select_from(Submission)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Course, Assignment.course_id == Course.id)
            .where(
                and_(
                    Course.owner_id == teacher_id,
                    Submission.status == SubmissionStatus.submitted,
                    ~Submission.grades.any()  # Нет оценок
                )
            )
        )
        pending_submissions = pending_submissions_result.scalar() or 0
        
        return {
            "teacher_id": teacher_id,
            "overview": {
                "total_courses": courses_count,
                "total_assignments": total_assignments,
                "total_submissions": total_submissions,
                "total_grades": total_grades,
                "average_grade": average_grade,
                "pending_submissions": pending_submissions
            },
            "courses": [
                {
                    "id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "start_date": course.start_date,
                    "end_date": course.end_date
                }
                for course in courses
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting teacher overview for teacher {teacher_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении обзора преподавателя"
        )


# ------------------------- Advanced Analytics -------------------------

def _bucket_start(date_value: datetime, bucket: Literal["day", "week", "month"]) -> datetime:
    """Normalize datetime to the beginning of the bucket (day/week/month)."""
    naive = date_value.replace(tzinfo=None)
    if bucket == "day":
        return datetime(naive.year, naive.month, naive.day)
    if bucket == "week":
        monday = naive - timedelta(days=naive.weekday())
        return datetime(monday.year, monday.month, monday.day)
    return datetime(naive.year, naive.month, 1)


async def _course_trend_series(
    db: AsyncSession,
    course_id: int,
    days: int,
    bucket: Literal["day", "week", "month"],
) -> List[Dict]:
    window_start = datetime.now().replace(tzinfo=None) - timedelta(days=days)
    result = await db.execute(
        select(Submission, Assignment, Grade)
        .select_from(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .outerjoin(Grade, Grade.submission_id == Submission.id)
        .where(
            and_(
                Assignment.course_id == course_id,
                Submission.submitted_at.isnot(None),
                Submission.submitted_at >= window_start,
            )
        )
    )
    rows = result.all()

    buckets: Dict[datetime, Dict[str, float]] = {}
    submissions_seen: Dict[datetime, set] = {}

    for submission, assignment, grade in rows:
        if not submission.submitted_at:
            continue
        bstart = _bucket_start(submission.submitted_at, bucket)
        if bstart not in buckets:
            buckets[bstart] = {
                "submissions": 0,
                "grades_sum": 0.0,
                "grades_count": 0,
                "on_time_count": 0,
                "late_count": 0,
            }
            submissions_seen[bstart] = set()

        bucket_data = buckets[bstart]
        if submission.id not in submissions_seen[bstart]:
            submissions_seen[bstart].add(submission.id)
            bucket_data["submissions"] += 1
            if assignment and submission.submitted_at and assignment.due_date:
                if submission.submitted_at <= assignment.due_date:
                    bucket_data["on_time_count"] += 1
                else:
                    bucket_data["late_count"] += 1

        if grade is not None and grade.score is not None:
            bucket_data["grades_sum"] += float(grade.score)
            bucket_data["grades_count"] += 1

    series = []
    for key in sorted(buckets.keys()):
        data = buckets[key]
        avg_grade = (data["grades_sum"] / data["grades_count"]) if data["grades_count"] > 0 else 0.0
        on_time_rate = (data["on_time_count"] / data["submissions"]) * 100 if data["submissions"] > 0 else 0.0
        series.append({
            "bucket_start": key.isoformat(),
            "submissions": int(data["submissions"]),
            "average_grade": round(avg_grade, 2),
            "on_time_rate": round(on_time_rate, 2),
            "late_submissions": int(data["late_count"]),
        })

    return series


async def _student_trend_series(
    db: AsyncSession,
    student_id: int,
    days: int,
    bucket: Literal["day", "week", "month"],
) -> List[Dict]:
    window_start = datetime.now().replace(tzinfo=None) - timedelta(days=days)
    result = await db.execute(
        select(Submission, Assignment, Grade)
        .select_from(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .outerjoin(Grade, Grade.submission_id == Submission.id)
        .where(
            and_(
                Submission.student_id == student_id,
                Submission.submitted_at.isnot(None),
                Submission.submitted_at >= window_start,
            )
        )
    )
    rows = result.all()

    buckets: Dict[datetime, Dict[str, float]] = {}
    submissions_seen: Dict[datetime, set] = {}

    for submission, assignment, grade in rows:
        if not submission.submitted_at:
            continue
        bstart = _bucket_start(submission.submitted_at, bucket)
        if bstart not in buckets:
            buckets[bstart] = {
                "submissions": 0,
                "grades_sum": 0.0,
                "grades_count": 0,
                "on_time_count": 0,
                "late_count": 0,
            }
            submissions_seen[bstart] = set()

        bucket_data = buckets[bstart]
        if submission.id not in submissions_seen[bstart]:
            submissions_seen[bstart].add(submission.id)
            bucket_data["submissions"] += 1
            if assignment and submission.submitted_at and assignment.due_date:
                if submission.submitted_at <= assignment.due_date:
                    bucket_data["on_time_count"] += 1
                else:
                    bucket_data["late_count"] += 1

        if grade is not None and grade.score is not None:
            bucket_data["grades_sum"] += float(grade.score)
            bucket_data["grades_count"] += 1

    series = []
    for key in sorted(buckets.keys()):
        data = buckets[key]
        avg_grade = (data["grades_sum"] / data["grades_count"]) if data["grades_count"] > 0 else 0.0
        on_time_rate = (data["on_time_count"] / data["submissions"]) * 100 if data["submissions"] > 0 else 0.0
        series.append({
            "bucket_start": key.isoformat(),
            "submissions": int(data["submissions"]),
            "average_grade": round(avg_grade, 2),
            "on_time_rate": round(on_time_rate, 2),
            "late_submissions": int(data["late_count"]),
        })

    return series


@router.get(
    "/courses/{course_id}/trends",
    summary="Тренды по курсу",
    description="Временные ряды по сдачам, средним оценкам и своевременности"
)
async def get_course_trends(
    course_id: int,
    days: int = Query(30, ge=7, le=365),
    bucket: Literal["day", "week", "month"] = Query("week"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    if current_user.role != UserRole.admin and course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к курсу")

    try:
        series = await _course_trend_series(db, course_id, days, bucket)
        return {
            "course_id": course_id,
            "bucket": bucket,
            "days": days,
            "series": series,
            "generated_at": datetime.now(timezone.utc)
        }
    except Exception as e:
        logger.error(f"Error getting course trends for {course_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении трендов курса")


@router.get(
    "/students/{student_id}/trends",
    summary="Тренды по студенту",
    description="Временные ряды по сдачам, средним оценкам и своевременности для студента"
)
async def get_student_trends(
    student_id: int,
    days: int = Query(30, ge=7, le=365),
    bucket: Literal["day", "week", "month"] = Query("week"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Студент не найден")

    try:
        series = await _student_trend_series(db, student_id, days, bucket)
        return {
            "student_id": student_id,
            "bucket": bucket,
            "days": days,
            "series": series,
            "generated_at": datetime.now(timezone.utc)
        }
    except Exception as e:
        logger.error(f"Error getting student trends for {student_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении трендов студента")


def _simple_forecast(values: List[float], horizon: int) -> List[float]:
    if not values:
        return [0.0] * horizon
    window = min(len(values), 5)
    avg = sum(values[-window:]) / window
    return [round(avg, 2) for _ in range(horizon)]


@router.get(
    "/predict/performance",
    summary="Прогнозирование производительности",
    description="Простой прогноз по числу сдач и средним оценкам для студента или курса"
)
async def predict_performance(
    scope: Literal["student", "course"],
    target_id: int,
    horizon_days: int = Query(14, ge=7, le=60),
    bucket: Literal["day", "week"] = Query("day"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.teacher, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    days_history = 60 if bucket == "day" else 180
    try:
        if scope == "course":
            course_result = await db.execute(select(Course).where(Course.id == target_id))
            course = course_result.scalar_one_or_none()
            if not course:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
            if current_user.role != UserRole.admin and course.owner_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к курсу")
            series = await _course_trend_series(db, target_id, days_history, bucket)
        else:
            student_result = await db.execute(select(Student).where(Student.id == target_id))
            if not student_result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Студент не найден")
            series = await _student_trend_series(db, target_id, days_history, bucket)

        submissions_series = [point["submissions"] for point in series]
        avg_grade_series = [point["average_grade"] for point in series]

        horizon_points = horizon_days if bucket == "day" else max(2, horizon_days // 7)
        forecast_submissions = _simple_forecast(submissions_series, horizon_points)
        forecast_average_grade = _simple_forecast(avg_grade_series, horizon_points)

        return {
            "scope": scope,
            "target_id": target_id,
            "bucket": bucket,
            "history_points": len(series),
            "forecast_horizon": horizon_days,
            "history": series,
            "forecast": [
                {"index": i + 1, "pred_submissions": s, "pred_avg_grade": g}
                for i, (s, g) in enumerate(zip(forecast_submissions, forecast_average_grade))
            ],
            "generated_at": datetime.now(timezone.utc)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting performance ({scope}:{target_id}): {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при прогнозировании")
