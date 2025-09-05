"""API routes for academic calendar and SCD management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import date, datetime

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.academic_calendar_service import academic_calendar_service, scd_service

router = APIRouter(prefix="/academic-calendar", tags=["Academic Calendar"])


class AcademicYearRequest(BaseModel):
    """Request model for creating academic year."""
    year_code: str
    start_date: date
    end_date: date


class AcademicTermRequest(BaseModel):
    """Request model for creating academic term."""
    term_code: str
    term_name: str
    term_type: str
    academic_year_id: int
    start_date: date
    end_date: date
    registration_start: Optional[date] = None
    registration_end: Optional[date] = None
    classes_start: Optional[date] = None
    classes_end: Optional[date] = None
    finals_start: Optional[date] = None
    finals_end: Optional[date] = None
    grades_due: Optional[date] = None
    is_current: bool = False


class DateDimensionRequest(BaseModel):
    """Request model for populating date dimension."""
    start_year: int
    end_year: int


class UserSCDUpdateRequest(BaseModel):
    """Request model for updating user SCD."""
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    major: Optional[str] = None
    year_level: Optional[str] = None
    enrollment_status: Optional[str] = None
    gpa: Optional[str] = None
    change_reason: str


class CourseSCDUpdateRequest(BaseModel):
    """Request model for updating course SCD."""
    course_id: int
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    department: Optional[str] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    enrollment_count: Optional[int] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    term_id: Optional[int] = None
    academic_year_id: Optional[int] = None
    change_reason: str


@router.post("/academic-years", summary="Create academic year")
async def create_academic_year(
    request: AcademicYearRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Create a new academic year."""
    try:
        academic_year = await academic_calendar_service.create_academic_year(
            request.year_code,
            request.start_date,
            request.end_date
        )
        
        return {
            "success": True,
            "message": "Academic year created successfully",
            "academic_year": {
                "id": academic_year.id,
                "year_code": academic_year.year_code,
                "year_name": academic_year.year_name,
                "start_date": academic_year.start_date.isoformat(),
                "end_date": academic_year.end_date.isoformat(),
                "is_current": academic_year.is_current,
                "is_active": academic_year.is_active
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create academic year: {str(e)}"
        )


@router.post("/academic-terms", summary="Create academic term")
async def create_academic_term(
    request: AcademicTermRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Create a new academic term."""
    try:
        term_data = request.dict()
        term = await academic_calendar_service.create_academic_term(term_data)
        
        return {
            "success": True,
            "message": "Academic term created successfully",
            "term": {
                "id": term.id,
                "term_code": term.term_code,
                "term_name": term.term_name,
                "term_type": term.term_type,
                "academic_year_id": term.academic_year_id,
                "start_date": term.start_date.isoformat(),
                "end_date": term.end_date.isoformat(),
                "is_current": term.is_current,
                "is_active": term.is_active
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create academic term: {str(e)}"
        )


@router.get("/academic-years", summary="Get academic years")
async def get_academic_years(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all academic years."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.academic_calendar import AcademicYear
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            query = select(AcademicYear)
            
            if is_active is not None:
                query = query.where(AcademicYear.is_active == is_active)
            
            query = query.order_by(AcademicYear.start_date.desc())
            
            result = await db.execute(query)
            academic_years = result.scalars().all()
            
            return {
                "success": True,
                "academic_years": [
                    {
                        "id": year.id,
                        "year_code": year.year_code,
                        "year_name": year.year_name,
                        "start_date": year.start_date.isoformat(),
                        "end_date": year.end_date.isoformat(),
                        "is_current": year.is_current,
                        "is_active": year.is_active,
                        "created_at": year.created_at.isoformat()
                    }
                    for year in academic_years
                ]
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get academic years: {str(e)}"
        )


@router.get("/academic-terms", summary="Get academic terms")
async def get_academic_terms(
    academic_year_id: Optional[int] = Query(None, description="Filter by academic year"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all academic terms."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.academic_calendar import AcademicTerm
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            query = select(AcademicTerm)
            
            if academic_year_id:
                query = query.where(AcademicTerm.academic_year_id == academic_year_id)
            
            if is_active is not None:
                query = query.where(AcademicTerm.is_active == is_active)
            
            query = query.order_by(AcademicTerm.start_date.desc())
            
            result = await db.execute(query)
            terms = result.scalars().all()
            
            return {
                "success": True,
                "terms": [
                    {
                        "id": term.id,
                        "term_code": term.term_code,
                        "term_name": term.term_name,
                        "term_type": term.term_type,
                        "academic_year_id": term.academic_year_id,
                        "start_date": term.start_date.isoformat(),
                        "end_date": term.end_date.isoformat(),
                        "registration_start": term.registration_start.isoformat() if term.registration_start else None,
                        "registration_end": term.registration_end.isoformat() if term.registration_end else None,
                        "classes_start": term.classes_start.isoformat() if term.classes_start else None,
                        "classes_end": term.classes_end.isoformat() if term.classes_end else None,
                        "finals_start": term.finals_start.isoformat() if term.finals_start else None,
                        "finals_end": term.finals_end.isoformat() if term.finals_end else None,
                        "grades_due": term.grades_due.isoformat() if term.grades_due else None,
                        "is_current": term.is_current,
                        "is_active": term.is_active
                    }
                    for term in terms
                ]
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get academic terms: {str(e)}"
        )


@router.get("/academic-weeks", summary="Get academic weeks")
async def get_academic_weeks(
    term_id: Optional[int] = Query(None, description="Filter by term"),
    is_current: Optional[bool] = Query(None, description="Filter by current status"),
    week_type: Optional[str] = Query(None, description="Filter by week type"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get academic weeks."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.academic_calendar import AcademicWeek
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            query = select(AcademicWeek)
            
            if term_id:
                query = query.where(AcademicWeek.term_id == term_id)
            
            if is_current is not None:
                query = query.where(AcademicWeek.is_current == is_current)
            
            if week_type:
                query = query.where(AcademicWeek.week_type == week_type)
            
            query = query.order_by(AcademicWeek.start_date.desc()).limit(50)
            
            result = await db.execute(query)
            weeks = result.scalars().all()
            
            return {
                "success": True,
                "weeks": [
                    {
                        "id": week.id,
                        "week_code": week.week_code,
                        "week_number": week.week_number,
                        "year_week_number": week.year_week_number,
                        "calendar_week": week.calendar_week,
                        "term_id": week.term_id,
                        "academic_year_id": week.academic_year_id,
                        "start_date": week.start_date.isoformat(),
                        "end_date": week.end_date.isoformat(),
                        "is_current": week.is_current,
                        "is_break_week": week.is_break_week,
                        "is_exam_week": week.is_exam_week,
                        "is_registration_week": week.is_registration_week,
                        "week_type": week.week_type,
                        "has_holiday": week.has_holiday,
                        "holiday_name": week.holiday_name
                    }
                    for week in weeks
                ]
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get academic weeks: {str(e)}"
        )


@router.post("/date-dimension/populate", summary="Populate date dimension")
async def populate_date_dimension(
    request: DateDimensionRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Populate the date dimension table."""
    try:
        await academic_calendar_service.populate_date_dimension(
            request.start_year,
            request.end_year
        )
        
        return {
            "success": True,
            "message": f"Date dimension populated from {request.start_year} to {request.end_year}",
            "start_year": request.start_year,
            "end_year": request.end_year
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to populate date dimension: {str(e)}"
        )


@router.post("/update-current-flags", summary="Update current flags")
async def update_current_flags(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Update current flags for all calendar dimensions."""
    try:
        await academic_calendar_service.update_current_flags()
        
        return {
            "success": True,
            "message": "Current flags updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update current flags: {str(e)}"
        )


@router.get("/current-context", summary="Get current academic context")
async def get_current_context(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the current academic context (year, term, week)."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.academic_calendar import AcademicYear, AcademicTerm, AcademicWeek
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # Get current academic year
            current_year_result = await db.execute(
                select(AcademicYear).where(AcademicYear.is_current == True)
            )
            current_year = current_year_result.scalar_one_or_none()
            
            # Get current term
            current_term_result = await db.execute(
                select(AcademicTerm).where(AcademicTerm.is_current == True)
            )
            current_term = current_term_result.scalar_one_or_none()
            
            # Get current week
            current_week_result = await db.execute(
                select(AcademicWeek).where(AcademicWeek.is_current == True)
            )
            current_week = current_week_result.scalar_one_or_none()
            
            return {
                "success": True,
                "current_context": {
                    "academic_year": {
                        "id": current_year.id,
                        "year_code": current_year.year_code,
                        "year_name": current_year.year_name,
                        "start_date": current_year.start_date.isoformat(),
                        "end_date": current_year.end_date.isoformat()
                    } if current_year else None,
                    "term": {
                        "id": current_term.id,
                        "term_code": current_term.term_code,
                        "term_name": current_term.term_name,
                        "term_type": current_term.term_type,
                        "start_date": current_term.start_date.isoformat(),
                        "end_date": current_term.end_date.isoformat()
                    } if current_term else None,
                    "week": {
                        "id": current_week.id,
                        "week_code": current_week.week_code,
                        "week_number": current_week.week_number,
                        "week_type": current_week.week_type,
                        "start_date": current_week.start_date.isoformat(),
                        "end_date": current_week.end_date.isoformat(),
                        "is_break_week": current_week.is_break_week,
                        "is_exam_week": current_week.is_exam_week,
                        "has_holiday": current_week.has_holiday,
                        "holiday_name": current_week.holiday_name
                    } if current_week else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current context: {str(e)}"
        )


# SCD Management Endpoints

@router.post("/scd/users/update", summary="Update user SCD")
async def update_user_scd(
    request: UserSCDUpdateRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Update user slowly changing dimensions."""
    try:
        # Prepare attributes dict (exclude None values)
        attributes = {k: v for k, v in request.dict().items() 
                     if v is not None and k not in ['user_id', 'change_reason']}
        
        scd_record = await scd_service.update_user_scd(
            request.user_id,
            attributes,
            request.change_reason,
            current_user.id
        )
        
        return {
            "success": True,
            "message": "User SCD updated successfully",
            "scd_record": {
                "id": scd_record.id,
                "user_id": scd_record.user_id,
                "version": scd_record.version,
                "effective_date": scd_record.effective_date.isoformat(),
                "is_current": scd_record.is_current,
                "change_reason": scd_record.change_reason
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user SCD: {str(e)}"
        )


@router.post("/scd/courses/update", summary="Update course SCD")
async def update_course_scd(
    request: CourseSCDUpdateRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Update course slowly changing dimensions."""
    try:
        # Prepare attributes dict (exclude None values)
        attributes = {k: v for k, v in request.dict().items() 
                     if v is not None and k not in ['course_id', 'change_reason']}
        
        scd_record = await scd_service.update_course_scd(
            request.course_id,
            attributes,
            request.change_reason,
            current_user.id
        )
        
        return {
            "success": True,
            "message": "Course SCD updated successfully",
            "scd_record": {
                "id": scd_record.id,
                "course_id": scd_record.course_id,
                "version": scd_record.version,
                "effective_date": scd_record.effective_date.isoformat(),
                "is_current": scd_record.is_current,
                "change_reason": scd_record.change_reason
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update course SCD: {str(e)}"
        )


@router.get("/scd/users/{user_id}/history", summary="Get user SCD history")
async def get_user_scd_history(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get the complete history of a user's attributes."""
    try:
        history = await scd_service.get_user_history(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "history": [
                {
                    "id": record.id,
                    "version": record.version,
                    "effective_date": record.effective_date.isoformat(),
                    "expiry_date": record.expiry_date.isoformat() if record.expiry_date else None,
                    "is_current": record.is_current,
                    "name": record.name,
                    "email": record.email,
                    "role": record.role,
                    "department": record.department,
                    "major": record.major,
                    "year_level": record.year_level,
                    "enrollment_status": record.enrollment_status,
                    "gpa": record.gpa,
                    "change_reason": record.change_reason,
                    "changed_by": record.changed_by,
                    "created_at": record.created_at.isoformat()
                }
                for record in history
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user SCD history: {str(e)}"
        )


@router.get("/scd/users/{user_id}/at-date", summary="Get user attributes at date")
async def get_user_attributes_at_date(
    user_id: int,
    target_date: date = Query(..., description="Date to get attributes for"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get user attributes as they were on a specific date."""
    try:
        attributes = await scd_service.get_user_attributes_at_date(user_id, target_date)
        
        if not attributes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No user attributes found for user {user_id} at date {target_date}"
            )
        
        return {
            "success": True,
            "user_id": user_id,
            "target_date": target_date.isoformat(),
            "attributes": {
                "id": attributes.id,
                "version": attributes.version,
                "effective_date": attributes.effective_date.isoformat(),
                "expiry_date": attributes.expiry_date.isoformat() if attributes.expiry_date else None,
                "name": attributes.name,
                "email": attributes.email,
                "role": attributes.role,
                "department": attributes.department,
                "major": attributes.major,
                "year_level": attributes.year_level,
                "enrollment_status": attributes.enrollment_status,
                "gpa": attributes.gpa
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user attributes at date: {str(e)}"
        )


@router.get("/status", summary="Get calendar system status")
async def get_calendar_status(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Get academic calendar system status."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.academic_calendar import AcademicYear, AcademicTerm, AcademicWeek, DateDimension, UserSCD, CourseSCD
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as db:
            # Get counts
            year_count = await db.execute(select(func.count(AcademicYear.id)))
            term_count = await db.execute(select(func.count(AcademicTerm.id)))
            week_count = await db.execute(select(func.count(AcademicWeek.id)))
            date_count = await db.execute(select(func.count(DateDimension.date_key)))
            user_scd_count = await db.execute(select(func.count(UserSCD.id)))
            course_scd_count = await db.execute(select(func.count(CourseSCD.id)))
            
            # Get date range
            date_range_result = await db.execute(
                select(func.min(DateDimension.full_date), func.max(DateDimension.full_date))
            )
            date_range = date_range_result.fetchone()
            
            return {
                "success": True,
                "status": "active",
                "statistics": {
                    "academic_years": year_count.scalar(),
                    "academic_terms": term_count.scalar(),
                    "academic_weeks": week_count.scalar(),
                    "date_dimension_records": date_count.scalar(),
                    "user_scd_records": user_scd_count.scalar(),
                    "course_scd_records": course_scd_count.scalar()
                },
                "date_dimension_range": {
                    "start_date": date_range[0].isoformat() if date_range[0] else None,
                    "end_date": date_range[1].isoformat() if date_range[1] else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar status: {str(e)}"
        )
