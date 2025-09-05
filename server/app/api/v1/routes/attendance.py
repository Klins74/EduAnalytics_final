"""API routes for attendance and page view analytics."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import date, datetime
import uuid

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.attendance_analytics import (
    attendance_service, pageview_service, 
    AttendanceStatus, PageViewType
)

router = APIRouter(prefix="/attendance", tags=["Attendance & Page Views"])


class AttendanceRecordRequest(BaseModel):
    """Request model for recording attendance."""
    user_id: int
    course_id: int
    session_date: date
    status: str  # Will be converted to AttendanceStatus
    minutes_present: Optional[int] = None
    notes: Optional[str] = None


class BulkAttendanceRequest(BaseModel):
    """Request model for bulk attendance recording."""
    course_id: int
    session_date: date
    records: List[Dict[str, Any]]  # List of {user_id, status, minutes_present?, notes?}


class PageViewRequest(BaseModel):
    """Request model for recording page view."""
    course_id: Optional[int] = None
    page_type: str  # Will be converted to PageViewType
    page_url: str
    page_id: Optional[str] = None
    page_title: Optional[str] = None
    time_on_page: Optional[int] = None
    referrer: Optional[str] = None


@router.post("/records", summary="Record attendance")
async def record_attendance(
    request: AttendanceRecordRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Record attendance for a student."""
    try:
        # Validate status
        try:
            status = AttendanceStatus(request.status.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid attendance status: {request.status}. Valid values: {[s.value for s in AttendanceStatus]}"
            )
        
        # Record attendance
        record = await attendance_service.record_attendance(
            user_id=request.user_id,
            course_id=request.course_id,
            session_date=request.session_date,
            status=status,
            minutes_present=request.minutes_present,
            notes=request.notes,
            recorded_by=current_user.id
        )
        
        return {
            "success": True,
            "message": "Attendance recorded successfully",
            "record": {
                "id": record.id,
                "user_id": record.user_id,
                "course_id": record.course_id,
                "session_date": record.session_date.isoformat(),
                "status": record.status.value,
                "minutes_present": record.minutes_present,
                "notes": record.notes,
                "recorded_by": record.recorded_by,
                "recorded_at": record.recorded_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record attendance: {str(e)}"
        )


@router.post("/bulk-records", summary="Record bulk attendance")
async def record_bulk_attendance(
    request: BulkAttendanceRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Record attendance for multiple students at once."""
    try:
        successful_records = []
        failed_records = []
        
        for record_data in request.records:
            try:
                # Validate required fields
                if "user_id" not in record_data or "status" not in record_data:
                    failed_records.append({
                        "user_id": record_data.get("user_id"),
                        "error": "Missing required fields: user_id, status"
                    })
                    continue
                
                # Validate status
                try:
                    attendance_status = AttendanceStatus(record_data["status"].lower())
                except ValueError:
                    failed_records.append({
                        "user_id": record_data["user_id"],
                        "error": f"Invalid status: {record_data['status']}"
                    })
                    continue
                
                # Record attendance
                record = await attendance_service.record_attendance(
                    user_id=record_data["user_id"],
                    course_id=request.course_id,
                    session_date=request.session_date,
                    status=attendance_status,
                    minutes_present=record_data.get("minutes_present"),
                    notes=record_data.get("notes"),
                    recorded_by=current_user.id
                )
                
                successful_records.append({
                    "user_id": record.user_id,
                    "status": record.status.value,
                    "recorded_at": record.recorded_at.isoformat()
                })
                
            except Exception as e:
                failed_records.append({
                    "user_id": record_data.get("user_id"),
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"Processed {len(request.records)} attendance records",
            "results": {
                "successful": len(successful_records),
                "failed": len(failed_records),
                "successful_records": successful_records,
                "failed_records": failed_records
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record bulk attendance: {str(e)}"
        )


@router.get("/reports/{course_id}", summary="Get attendance report")
async def get_attendance_report(
    course_id: int,
    start_date: Optional[date] = Query(None, description="Start date for report"),
    end_date: Optional[date] = Query(None, description="End date for report"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get comprehensive attendance report for a course."""
    try:
        report = await attendance_service.get_attendance_report(
            course_id=course_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance report: {str(e)}"
        )


@router.post("/page-views", summary="Record page view")
async def record_page_view(
    request: PageViewRequest,
    req: Request,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Record a page view for analytics."""
    try:
        # Validate page type
        try:
            page_type = PageViewType(request.page_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid page type: {request.page_type}. Valid values: {[t.value for t in PageViewType]}"
            )
        
        # Generate or get session ID from headers/cookies
        session_id = req.headers.get("X-Session-ID") or str(uuid.uuid4())
        
        # Get client info
        user_agent = req.headers.get("User-Agent")
        client_ip = req.client.host if req.client else None
        
        # Record page view
        record = await pageview_service.record_page_view(
            user_id=current_user.id,
            course_id=request.course_id,
            page_type=page_type,
            page_url=request.page_url,
            session_id=session_id,
            page_id=request.page_id,
            page_title=request.page_title,
            time_on_page=request.time_on_page,
            referrer=request.referrer,
            user_agent=user_agent,
            ip_address=client_ip
        )
        
        return {
            "success": True,
            "message": "Page view recorded successfully",
            "session_id": session_id,
            "record": {
                "id": record.id,
                "page_type": record.page_type.value,
                "page_url": record.page_url,
                "view_time": record.view_time.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record page view: {str(e)}"
        )


@router.get("/page-views/analytics/{course_id}", summary="Get page view analytics")
async def get_page_view_analytics(
    course_id: int,
    days: int = Query(7, description="Number of days to analyze", ge=1, le=90),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get comprehensive page view analytics for a course."""
    try:
        analytics = await pageview_service.get_page_view_analytics(
            course_id=course_id,
            days=days
        )
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get page view analytics: {str(e)}"
        )


@router.get("/engagement/{user_id}/{course_id}", summary="Get student engagement score")
async def get_student_engagement_score(
    user_id: int,
    course_id: int,
    days: int = Query(7, description="Number of days to analyze", ge=1, le=90),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get student engagement score based on attendance and page views."""
    try:
        engagement = await pageview_service.get_student_engagement_score(
            user_id=user_id,
            course_id=course_id,
            days=days
        )
        
        return {
            "success": True,
            "engagement": engagement
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student engagement score: {str(e)}"
        )


@router.get("/summary/{course_id}", summary="Get course attendance summary")
async def get_course_attendance_summary(
    course_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get attendance summary for all students in a course."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            summary_sql = """
            SELECT 
                u.id as user_id,
                u.name,
                u.email,
                COALESCE(asu.total_sessions, 0) as total_sessions,
                COALESCE(asu.present_sessions, 0) as present_sessions,
                COALESCE(asu.absent_sessions, 0) as absent_sessions,
                COALESCE(asu.late_sessions, 0) as late_sessions,
                COALESCE(asu.excused_sessions, 0) as excused_sessions,
                COALESCE(asu.attendance_rate, 0.00) as attendance_rate,
                COALESCE(asu.total_minutes_present, 0) as total_minutes_present,
                asu.last_updated
            FROM users u
            JOIN enrollments e ON u.id = e.user_id
            LEFT JOIN attendance_summary asu ON u.id = asu.user_id AND asu.course_id = :course_id
            WHERE e.course_id = :course_id AND e.status = 'active'
            ORDER BY u.name
            """
            
            result = await db.execute(text(summary_sql), {"course_id": course_id})
            summaries = [
                {
                    "user_id": row.user_id,
                    "name": row.name,
                    "email": row.email,
                    "total_sessions": row.total_sessions,
                    "present_sessions": row.present_sessions,
                    "absent_sessions": row.absent_sessions,
                    "late_sessions": row.late_sessions,
                    "excused_sessions": row.excused_sessions,
                    "attendance_rate": float(row.attendance_rate),
                    "total_minutes_present": row.total_minutes_present,
                    "last_updated": row.last_updated.isoformat() if row.last_updated else None
                }
                for row in result.fetchall()
            ]
            
            # Calculate course-wide statistics
            if summaries:
                total_students = len(summaries)
                avg_attendance_rate = sum(s["attendance_rate"] for s in summaries) / total_students
                students_with_perfect_attendance = sum(1 for s in summaries if s["attendance_rate"] >= 100)
                students_at_risk = sum(1 for s in summaries if s["attendance_rate"] < 70)
            else:
                total_students = 0
                avg_attendance_rate = 0
                students_with_perfect_attendance = 0
                students_at_risk = 0
            
            return {
                "success": True,
                "course_id": course_id,
                "statistics": {
                    "total_students": total_students,
                    "average_attendance_rate": round(avg_attendance_rate, 2),
                    "students_with_perfect_attendance": students_with_perfect_attendance,
                    "students_at_risk": students_at_risk
                },
                "student_summaries": summaries
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance summary: {str(e)}"
        )


@router.get("/at-risk/{course_id}", summary="Get at-risk students")
async def get_at_risk_students(
    course_id: int,
    attendance_threshold: float = Query(70.0, description="Attendance rate threshold", ge=0, le=100),
    engagement_threshold: float = Query(40.0, description="Engagement score threshold", ge=0, le=100),
    days: int = Query(14, description="Days to analyze for engagement", ge=1, le=90),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Identify students at risk based on attendance and engagement metrics."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Get students with low attendance
            at_risk_sql = """
            SELECT 
                u.id as user_id,
                u.name,
                u.email,
                COALESCE(asu.attendance_rate, 0.00) as attendance_rate,
                COALESCE(asu.total_sessions, 0) as total_sessions,
                COALESCE(asu.absent_sessions, 0) as absent_sessions,
                asu.last_updated
            FROM users u
            JOIN enrollments e ON u.id = e.user_id
            LEFT JOIN attendance_summary asu ON u.id = asu.user_id AND asu.course_id = :course_id
            WHERE e.course_id = :course_id 
            AND e.status = 'active'
            AND (asu.attendance_rate < :attendance_threshold OR asu.attendance_rate IS NULL)
            ORDER BY COALESCE(asu.attendance_rate, 0) ASC
            """
            
            result = await db.execute(text(at_risk_sql), {
                "course_id": course_id,
                "attendance_threshold": attendance_threshold
            })
            
            at_risk_students = []
            
            for row in result.fetchall():
                # Calculate engagement score for each at-risk student
                try:
                    engagement = await pageview_service.get_student_engagement_score(
                        user_id=row.user_id,
                        course_id=course_id,
                        days=days
                    )
                    engagement_score = engagement["engagement_score"]
                    engagement_level = engagement["engagement_level"]
                except Exception:
                    engagement_score = 0
                    engagement_level = "Unknown"
                
                # Determine risk factors
                risk_factors = []
                if row.attendance_rate < attendance_threshold:
                    risk_factors.append(f"Low attendance ({row.attendance_rate:.1f}%)")
                if engagement_score < engagement_threshold:
                    risk_factors.append(f"Low engagement ({engagement_score:.1f})")
                if row.absent_sessions > 3:
                    risk_factors.append(f"High absences ({row.absent_sessions})")
                
                # Calculate risk level
                if row.attendance_rate < 50 or engagement_score < 20:
                    risk_level = "Critical"
                elif row.attendance_rate < 60 or engagement_score < 30:
                    risk_level = "High"
                else:
                    risk_level = "Medium"
                
                at_risk_students.append({
                    "user_id": row.user_id,
                    "name": row.name,
                    "email": row.email,
                    "attendance_rate": float(row.attendance_rate),
                    "engagement_score": engagement_score,
                    "engagement_level": engagement_level,
                    "risk_level": risk_level,
                    "risk_factors": risk_factors,
                    "total_sessions": row.total_sessions,
                    "absent_sessions": row.absent_sessions,
                    "last_attendance_update": row.last_updated.isoformat() if row.last_updated else None
                })
            
            # Sort by risk level and attendance rate
            risk_order = {"Critical": 0, "High": 1, "Medium": 2}
            at_risk_students.sort(key=lambda x: (risk_order.get(x["risk_level"], 3), x["attendance_rate"]))
            
            return {
                "success": True,
                "course_id": course_id,
                "criteria": {
                    "attendance_threshold": attendance_threshold,
                    "engagement_threshold": engagement_threshold,
                    "analysis_days": days
                },
                "summary": {
                    "total_at_risk": len(at_risk_students),
                    "critical_risk": len([s for s in at_risk_students if s["risk_level"] == "Critical"]),
                    "high_risk": len([s for s in at_risk_students if s["risk_level"] == "High"]),
                    "medium_risk": len([s for s in at_risk_students if s["risk_level"] == "Medium"])
                },
                "at_risk_students": at_risk_students
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get at-risk students: {str(e)}"
        )


@router.post("/initialize", summary="Initialize attendance analytics")
async def initialize_attendance_analytics(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Initialize attendance analytics database tables."""
    try:
        await attendance_service.initialize()
        
        return {
            "success": True,
            "message": "Attendance analytics initialized successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize attendance analytics: {str(e)}"
        )


@router.get("/status", summary="Get attendance analytics status")
async def get_attendance_status(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Get attendance and page view analytics system status."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Check if tables exist and get counts
            status_sql = """
            SELECT 
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'attendance_records') as attendance_table_exists,
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'page_views') as pageviews_table_exists,
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'user_sessions') as sessions_table_exists,
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'attendance_summary') as summary_table_exists
            """
            
            result = await db.execute(text(status_sql))
            table_status = dict(result.fetchone()._mapping)
            
            # Get record counts if tables exist
            counts = {}
            if table_status["attendance_table_exists"]:
                count_result = await db.execute(text("SELECT COUNT(*) as count FROM attendance_records"))
                counts["attendance_records"] = count_result.fetchone().count
            
            if table_status["pageviews_table_exists"]:
                count_result = await db.execute(text("SELECT COUNT(*) as count FROM page_views"))
                counts["page_views"] = count_result.fetchone().count
            
            if table_status["sessions_table_exists"]:
                count_result = await db.execute(text("SELECT COUNT(*) as count FROM user_sessions"))
                counts["user_sessions"] = count_result.fetchone().count
            
            if table_status["summary_table_exists"]:
                count_result = await db.execute(text("SELECT COUNT(*) as count FROM attendance_summary"))
                counts["attendance_summaries"] = count_result.fetchone().count
            
            return {
                "success": True,
                "status": "active" if all(table_status.values()) else "partial",
                "tables": {
                    "attendance_records": bool(table_status["attendance_table_exists"]),
                    "page_views": bool(table_status["pageviews_table_exists"]),
                    "user_sessions": bool(table_status["sessions_table_exists"]),
                    "attendance_summary": bool(table_status["summary_table_exists"])
                },
                "record_counts": counts,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attendance status: {str(e)}"
        )
