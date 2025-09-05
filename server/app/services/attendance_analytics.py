"""
Attendance and Page View Analytics Service.

Tracks student attendance and page views to provide comprehensive engagement
analytics similar to Canvas Analytics.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_, func, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.course import Course

logger = logging.getLogger(__name__)


class AttendanceStatus(Enum):
    """Attendance status enumeration."""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"
    UNKNOWN = "unknown"


class PageViewType(Enum):
    """Page view type enumeration."""
    COURSE_HOME = "course_home"
    ASSIGNMENT = "assignment"
    DISCUSSION = "discussion"
    QUIZ = "quiz"
    MODULE = "module"
    PAGE = "page"
    FILE = "file"
    GRADEBOOK = "gradebook"
    SYLLABUS = "syllabus"
    ANNOUNCEMENTS = "announcements"
    OTHER = "other"


@dataclass
class AttendanceRecord:
    """Attendance record data structure."""
    id: Optional[int]
    user_id: int
    course_id: int
    session_date: date
    status: AttendanceStatus
    minutes_present: Optional[int]
    notes: Optional[str]
    recorded_by: int
    recorded_at: datetime


@dataclass
class PageViewRecord:
    """Page view record data structure."""
    id: Optional[int]
    user_id: int
    course_id: int
    page_type: PageViewType
    page_id: Optional[str]
    page_title: Optional[str]
    page_url: str
    session_id: str
    view_time: datetime
    time_on_page: Optional[int]  # seconds
    referrer: Optional[str]
    user_agent: Optional[str]
    ip_address: Optional[str]


class AttendanceAnalyticsService:
    """Service for tracking and analyzing student attendance."""
    
    async def initialize(self):
        """Initialize attendance analytics tables."""
        try:
            async with AsyncSessionLocal() as db:
                await self._create_attendance_tables(db)
                logger.info("Attendance analytics service initialized")
        except Exception as e:
            logger.error(f"Error initializing attendance analytics: {e}")
            raise
    
    async def _create_attendance_tables(self, db: AsyncSession):
        """Create attendance tracking tables."""
        create_tables_sql = """
        -- Attendance records table
        CREATE TABLE IF NOT EXISTS attendance_records (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            session_date DATE NOT NULL,
            status VARCHAR(20) NOT NULL,
            minutes_present INTEGER,
            notes TEXT,
            recorded_by INTEGER NOT NULL,
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, course_id, session_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_attendance_user_course ON attendance_records(user_id, course_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_session_date ON attendance_records(session_date);
        CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance_records(status);
        CREATE INDEX IF NOT EXISTS idx_attendance_course_date ON attendance_records(course_id, session_date);
        
        -- Page views table
        CREATE TABLE IF NOT EXISTS page_views (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            course_id INTEGER,
            page_type VARCHAR(50) NOT NULL,
            page_id VARCHAR(255),
            page_title VARCHAR(500),
            page_url TEXT NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            view_time TIMESTAMP WITH TIME ZONE NOT NULL,
            time_on_page INTEGER, -- seconds
            referrer TEXT,
            user_agent TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_pageviews_user_course ON page_views(user_id, course_id);
        CREATE INDEX IF NOT EXISTS idx_pageviews_view_time ON page_views(view_time);
        CREATE INDEX IF NOT EXISTS idx_pageviews_page_type ON page_views(page_type);
        CREATE INDEX IF NOT EXISTS idx_pageviews_session ON page_views(session_id);
        CREATE INDEX IF NOT EXISTS idx_pageviews_course_time ON page_views(course_id, view_time);
        
        -- User sessions table for tracking online activity
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            course_id INTEGER,
            start_time TIMESTAMP WITH TIME ZONE NOT NULL,
            last_activity TIMESTAMP WITH TIME ZONE NOT NULL,
            end_time TIMESTAMP WITH TIME ZONE,
            total_duration INTEGER, -- seconds
            page_views_count INTEGER DEFAULT 0,
            ip_address VARCHAR(45),
            user_agent TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_course ON user_sessions(course_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON user_sessions(start_time);
        CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active);
        
        -- Attendance summary table (materialized view-like)
        CREATE TABLE IF NOT EXISTS attendance_summary (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            total_sessions INTEGER DEFAULT 0,
            present_sessions INTEGER DEFAULT 0,
            absent_sessions INTEGER DEFAULT 0,
            late_sessions INTEGER DEFAULT 0,
            excused_sessions INTEGER DEFAULT 0,
            attendance_rate DECIMAL(5,2) DEFAULT 0.00,
            total_minutes_present INTEGER DEFAULT 0,
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE(user_id, course_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_attendance_summary_user_course ON attendance_summary(user_id, course_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_summary_rate ON attendance_summary(attendance_rate);
        """
        
        await db.execute(text(create_tables_sql))
        await db.commit()
    
    async def record_attendance(self, user_id: int, course_id: int, session_date: date,
                              status: AttendanceStatus, minutes_present: Optional[int] = None,
                              notes: Optional[str] = None, recorded_by: int = None) -> AttendanceRecord:
        """Record attendance for a student."""
        try:
            async with AsyncSessionLocal() as db:
                # Upsert attendance record
                upsert_sql = """
                INSERT INTO attendance_records (
                    user_id, course_id, session_date, status, minutes_present, notes, recorded_by
                ) VALUES (
                    :user_id, :course_id, :session_date, :status, :minutes_present, :notes, :recorded_by
                ) ON CONFLICT (user_id, course_id, session_date) DO UPDATE SET
                    status = EXCLUDED.status,
                    minutes_present = EXCLUDED.minutes_present,
                    notes = EXCLUDED.notes,
                    recorded_by = EXCLUDED.recorded_by,
                    recorded_at = NOW(),
                    updated_at = NOW()
                RETURNING *
                """
                
                result = await db.execute(text(upsert_sql), {
                    "user_id": user_id,
                    "course_id": course_id,
                    "session_date": session_date,
                    "status": status.value,
                    "minutes_present": minutes_present,
                    "notes": notes,
                    "recorded_by": recorded_by or user_id
                })
                
                record_data = result.fetchone()
                await db.commit()
                
                # Update attendance summary
                await self._update_attendance_summary(db, user_id, course_id)
                
                logger.info(f"Recorded attendance: user={user_id}, course={course_id}, status={status.value}")
                
                return AttendanceRecord(
                    id=record_data.id,
                    user_id=record_data.user_id,
                    course_id=record_data.course_id,
                    session_date=record_data.session_date,
                    status=AttendanceStatus(record_data.status),
                    minutes_present=record_data.minutes_present,
                    notes=record_data.notes,
                    recorded_by=record_data.recorded_by,
                    recorded_at=record_data.recorded_at
                )
                
        except Exception as e:
            logger.error(f"Error recording attendance: {e}")
            raise
    
    async def _update_attendance_summary(self, db: AsyncSession, user_id: int, course_id: int):
        """Update attendance summary for a user-course combination."""
        try:
            summary_sql = """
            INSERT INTO attendance_summary (
                user_id, course_id, total_sessions, present_sessions, absent_sessions,
                late_sessions, excused_sessions, attendance_rate, total_minutes_present
            )
            SELECT 
                :user_id,
                :course_id,
                COUNT(*) as total_sessions,
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present_sessions,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_sessions,
                COUNT(CASE WHEN status = 'late' THEN 1 END) as late_sessions,
                COUNT(CASE WHEN status = 'excused' THEN 1 END) as excused_sessions,
                ROUND(
                    (COUNT(CASE WHEN status IN ('present', 'late') THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2
                ) as attendance_rate,
                COALESCE(SUM(minutes_present), 0) as total_minutes_present
            FROM attendance_records
            WHERE user_id = :user_id AND course_id = :course_id
            ON CONFLICT (user_id, course_id) DO UPDATE SET
                total_sessions = EXCLUDED.total_sessions,
                present_sessions = EXCLUDED.present_sessions,
                absent_sessions = EXCLUDED.absent_sessions,
                late_sessions = EXCLUDED.late_sessions,
                excused_sessions = EXCLUDED.excused_sessions,
                attendance_rate = EXCLUDED.attendance_rate,
                total_minutes_present = EXCLUDED.total_minutes_present,
                last_updated = NOW()
            """
            
            await db.execute(text(summary_sql), {
                "user_id": user_id,
                "course_id": course_id
            })
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating attendance summary: {e}")
    
    async def get_attendance_report(self, course_id: int, start_date: Optional[date] = None,
                                  end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get comprehensive attendance report for a course."""
        try:
            async with AsyncSessionLocal() as db:
                # Set default date range if not provided
                if not end_date:
                    end_date = date.today()
                if not start_date:
                    start_date = end_date - timedelta(days=30)
                
                # Get attendance statistics
                stats_sql = """
                SELECT 
                    COUNT(DISTINCT ar.user_id) as total_students,
                    COUNT(DISTINCT ar.session_date) as total_sessions,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN ar.status = 'present' THEN 1 END) as present_count,
                    COUNT(CASE WHEN ar.status = 'absent' THEN 1 END) as absent_count,
                    COUNT(CASE WHEN ar.status = 'late' THEN 1 END) as late_count,
                    COUNT(CASE WHEN ar.status = 'excused' THEN 1 END) as excused_count,
                    ROUND(AVG(
                        CASE WHEN ar.status IN ('present', 'late') THEN 100.0 ELSE 0.0 END
                    ), 2) as average_attendance_rate
                FROM attendance_records ar
                WHERE ar.course_id = :course_id
                AND ar.session_date BETWEEN :start_date AND :end_date
                """
                
                stats_result = await db.execute(text(stats_sql), {
                    "course_id": course_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                stats = dict(stats_result.fetchone()._mapping)
                
                # Get student attendance summaries
                students_sql = """
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
                    COALESCE(asu.total_minutes_present, 0) as total_minutes_present
                FROM users u
                JOIN enrollments e ON u.id = e.user_id
                LEFT JOIN attendance_summary asu ON u.id = asu.user_id AND asu.course_id = :course_id
                WHERE e.course_id = :course_id AND e.status = 'active'
                ORDER BY u.name
                """
                
                students_result = await db.execute(text(students_sql), {"course_id": course_id})
                students = [dict(row._mapping) for row in students_result.fetchall()]
                
                # Get daily attendance patterns
                daily_sql = """
                SELECT 
                    session_date,
                    COUNT(*) as total_students,
                    COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                    COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent,
                    COUNT(CASE WHEN status = 'late' THEN 1 END) as late,
                    COUNT(CASE WHEN status = 'excused' THEN 1 END) as excused,
                    ROUND(
                        (COUNT(CASE WHEN status IN ('present', 'late') THEN 1 END)::DECIMAL / COUNT(*)) * 100, 2
                    ) as attendance_rate
                FROM attendance_records
                WHERE course_id = :course_id
                AND session_date BETWEEN :start_date AND :end_date
                GROUP BY session_date
                ORDER BY session_date DESC
                """
                
                daily_result = await db.execute(text(daily_sql), {
                    "course_id": course_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                daily_patterns = [
                    {
                        "session_date": row.session_date.isoformat(),
                        "total_students": row.total_students,
                        "present": row.present,
                        "absent": row.absent,
                        "late": row.late,
                        "excused": row.excused,
                        "attendance_rate": float(row.attendance_rate)
                    }
                    for row in daily_result.fetchall()
                ]
                
                return {
                    "course_id": course_id,
                    "date_range": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "statistics": {
                        "total_students": stats["total_students"] or 0,
                        "total_sessions": stats["total_sessions"] or 0,
                        "total_records": stats["total_records"] or 0,
                        "present_count": stats["present_count"] or 0,
                        "absent_count": stats["absent_count"] or 0,
                        "late_count": stats["late_count"] or 0,
                        "excused_count": stats["excused_count"] or 0,
                        "average_attendance_rate": float(stats["average_attendance_rate"] or 0)
                    },
                    "students": students,
                    "daily_patterns": daily_patterns
                }
                
        except Exception as e:
            logger.error(f"Error getting attendance report: {e}")
            raise


class PageViewAnalyticsService:
    """Service for tracking and analyzing page views."""
    
    async def record_page_view(self, user_id: int, course_id: Optional[int],
                             page_type: PageViewType, page_url: str,
                             session_id: str, page_id: Optional[str] = None,
                             page_title: Optional[str] = None,
                             time_on_page: Optional[int] = None,
                             referrer: Optional[str] = None,
                             user_agent: Optional[str] = None,
                             ip_address: Optional[str] = None) -> PageViewRecord:
        """Record a page view."""
        try:
            async with AsyncSessionLocal() as db:
                insert_sql = """
                INSERT INTO page_views (
                    user_id, course_id, page_type, page_id, page_title, page_url,
                    session_id, view_time, time_on_page, referrer, user_agent, ip_address
                ) VALUES (
                    :user_id, :course_id, :page_type, :page_id, :page_title, :page_url,
                    :session_id, :view_time, :time_on_page, :referrer, :user_agent, :ip_address
                ) RETURNING *
                """
                
                result = await db.execute(text(insert_sql), {
                    "user_id": user_id,
                    "course_id": course_id,
                    "page_type": page_type.value,
                    "page_id": page_id,
                    "page_title": page_title,
                    "page_url": page_url,
                    "session_id": session_id,
                    "view_time": datetime.utcnow(),
                    "time_on_page": time_on_page,
                    "referrer": referrer,
                    "user_agent": user_agent,
                    "ip_address": ip_address
                })
                
                record_data = result.fetchone()
                await db.commit()
                
                # Update session activity
                await self._update_session_activity(db, session_id, user_id, course_id)
                
                logger.debug(f"Recorded page view: user={user_id}, page_type={page_type.value}, url={page_url}")
                
                return PageViewRecord(
                    id=record_data.id,
                    user_id=record_data.user_id,
                    course_id=record_data.course_id,
                    page_type=PageViewType(record_data.page_type),
                    page_id=record_data.page_id,
                    page_title=record_data.page_title,
                    page_url=record_data.page_url,
                    session_id=record_data.session_id,
                    view_time=record_data.view_time,
                    time_on_page=record_data.time_on_page,
                    referrer=record_data.referrer,
                    user_agent=record_data.user_agent,
                    ip_address=record_data.ip_address
                )
                
        except Exception as e:
            logger.error(f"Error recording page view: {e}")
            raise
    
    async def _update_session_activity(self, db: AsyncSession, session_id: str,
                                     user_id: int, course_id: Optional[int]):
        """Update or create user session activity."""
        try:
            upsert_sql = """
            INSERT INTO user_sessions (
                user_id, session_id, course_id, start_time, last_activity, page_views_count
            ) VALUES (
                :user_id, :session_id, :course_id, NOW(), NOW(), 1
            ) ON CONFLICT (session_id) DO UPDATE SET
                last_activity = NOW(),
                page_views_count = user_sessions.page_views_count + 1,
                updated_at = NOW()
            """
            
            await db.execute(text(upsert_sql), {
                "user_id": user_id,
                "session_id": session_id,
                "course_id": course_id
            })
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    async def get_page_view_analytics(self, course_id: int, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive page view analytics for a course."""
        try:
            async with AsyncSessionLocal() as db:
                since_date = datetime.utcnow() - timedelta(days=days)
                
                # Get overall statistics
                stats_sql = """
                SELECT 
                    COUNT(*) as total_page_views,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    COUNT(DISTINCT page_url) as unique_pages,
                    ROUND(AVG(time_on_page), 2) as avg_time_on_page
                FROM page_views
                WHERE course_id = :course_id
                AND view_time >= :since_date
                """
                
                stats_result = await db.execute(text(stats_sql), {
                    "course_id": course_id,
                    "since_date": since_date
                })
                stats = dict(stats_result.fetchone()._mapping)
                
                # Get page type breakdown
                page_types_sql = """
                SELECT 
                    page_type,
                    COUNT(*) as view_count,
                    COUNT(DISTINCT user_id) as unique_users,
                    ROUND(AVG(time_on_page), 2) as avg_time_on_page
                FROM page_views
                WHERE course_id = :course_id
                AND view_time >= :since_date
                GROUP BY page_type
                ORDER BY view_count DESC
                """
                
                page_types_result = await db.execute(text(page_types_sql), {
                    "course_id": course_id,
                    "since_date": since_date
                })
                page_types = [dict(row._mapping) for row in page_types_result.fetchall()]
                
                # Get most viewed pages
                top_pages_sql = """
                SELECT 
                    page_title,
                    page_url,
                    page_type,
                    COUNT(*) as view_count,
                    COUNT(DISTINCT user_id) as unique_users,
                    ROUND(AVG(time_on_page), 2) as avg_time_on_page
                FROM page_views
                WHERE course_id = :course_id
                AND view_time >= :since_date
                AND page_title IS NOT NULL
                GROUP BY page_title, page_url, page_type
                ORDER BY view_count DESC
                LIMIT 20
                """
                
                top_pages_result = await db.execute(text(top_pages_sql), {
                    "course_id": course_id,
                    "since_date": since_date
                })
                top_pages = [dict(row._mapping) for row in top_pages_result.fetchall()]
                
                # Get hourly activity pattern
                hourly_sql = """
                SELECT 
                    EXTRACT(hour FROM view_time) as hour,
                    COUNT(*) as view_count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM page_views
                WHERE course_id = :course_id
                AND view_time >= :since_date
                GROUP BY EXTRACT(hour FROM view_time)
                ORDER BY hour
                """
                
                hourly_result = await db.execute(text(hourly_sql), {
                    "course_id": course_id,
                    "since_date": since_date
                })
                hourly_activity = [
                    {
                        "hour": int(row.hour),
                        "view_count": row.view_count,
                        "unique_users": row.unique_users
                    }
                    for row in hourly_result.fetchall()
                ]
                
                # Get user engagement
                user_engagement_sql = """
                SELECT 
                    u.id as user_id,
                    u.name,
                    COUNT(pv.id) as total_page_views,
                    COUNT(DISTINCT pv.session_id) as sessions,
                    ROUND(AVG(pv.time_on_page), 2) as avg_time_on_page,
                    MAX(pv.view_time) as last_activity
                FROM users u
                JOIN enrollments e ON u.id = e.user_id
                LEFT JOIN page_views pv ON u.id = pv.user_id AND pv.course_id = :course_id AND pv.view_time >= :since_date
                WHERE e.course_id = :course_id AND e.status = 'active'
                GROUP BY u.id, u.name
                ORDER BY total_page_views DESC
                LIMIT 50
                """
                
                user_result = await db.execute(text(user_engagement_sql), {
                    "course_id": course_id,
                    "since_date": since_date
                })
                user_engagement = [
                    {
                        "user_id": row.user_id,
                        "name": row.name,
                        "total_page_views": row.total_page_views or 0,
                        "sessions": row.sessions or 0,
                        "avg_time_on_page": float(row.avg_time_on_page or 0),
                        "last_activity": row.last_activity.isoformat() if row.last_activity else None
                    }
                    for row in user_result.fetchall()
                ]
                
                return {
                    "course_id": course_id,
                    "period_days": days,
                    "since_date": since_date.isoformat(),
                    "statistics": {
                        "total_page_views": stats["total_page_views"] or 0,
                        "unique_users": stats["unique_users"] or 0,
                        "unique_sessions": stats["unique_sessions"] or 0,
                        "unique_pages": stats["unique_pages"] or 0,
                        "avg_time_on_page": float(stats["avg_time_on_page"] or 0)
                    },
                    "page_types": page_types,
                    "top_pages": top_pages,
                    "hourly_activity": hourly_activity,
                    "user_engagement": user_engagement
                }
                
        except Exception as e:
            logger.error(f"Error getting page view analytics: {e}")
            raise
    
    async def get_student_engagement_score(self, user_id: int, course_id: int, days: int = 7) -> Dict[str, Any]:
        """Calculate student engagement score based on page views and attendance."""
        try:
            async with AsyncSessionLocal() as db:
                since_date = datetime.utcnow() - timedelta(days=days)
                
                # Get page view metrics
                pageview_sql = """
                SELECT 
                    COUNT(*) as total_page_views,
                    COUNT(DISTINCT session_id) as sessions,
                    COUNT(DISTINCT DATE(view_time)) as active_days,
                    COALESCE(AVG(time_on_page), 0) as avg_time_on_page,
                    COUNT(DISTINCT page_type) as page_types_visited
                FROM page_views
                WHERE user_id = :user_id AND course_id = :course_id
                AND view_time >= :since_date
                """
                
                pv_result = await db.execute(text(pageview_sql), {
                    "user_id": user_id,
                    "course_id": course_id,
                    "since_date": since_date
                })
                pv_metrics = dict(pv_result.fetchone()._mapping)
                
                # Get attendance metrics
                attendance_sql = """
                SELECT 
                    attendance_rate,
                    total_sessions,
                    present_sessions
                FROM attendance_summary
                WHERE user_id = :user_id AND course_id = :course_id
                """
                
                att_result = await db.execute(text(attendance_sql), {
                    "user_id": user_id,
                    "course_id": course_id
                })
                att_metrics = dict(att_result.fetchone()._mapping) if att_result.rowcount > 0 else {}
                
                # Calculate engagement score (0-100)
                page_view_score = min(100, (pv_metrics["total_page_views"] or 0) * 2)  # 2 points per page view, max 100
                activity_score = min(100, (pv_metrics["active_days"] or 0) * 15)  # 15 points per active day, max 100
                attendance_score = float(att_metrics.get("attendance_rate", 0))
                time_score = min(100, (pv_metrics["avg_time_on_page"] or 0) / 60 * 10)  # 10 points per minute, max 100
                
                # Weighted average
                engagement_score = (
                    page_view_score * 0.3 +
                    activity_score * 0.3 +
                    attendance_score * 0.3 +
                    time_score * 0.1
                )
                
                # Determine engagement level
                if engagement_score >= 80:
                    engagement_level = "High"
                elif engagement_score >= 60:
                    engagement_level = "Medium"
                elif engagement_score >= 40:
                    engagement_level = "Low"
                else:
                    engagement_level = "Very Low"
                
                return {
                    "user_id": user_id,
                    "course_id": course_id,
                    "period_days": days,
                    "engagement_score": round(engagement_score, 2),
                    "engagement_level": engagement_level,
                    "metrics": {
                        "page_views": {
                            "total_views": pv_metrics["total_page_views"] or 0,
                            "sessions": pv_metrics["sessions"] or 0,
                            "active_days": pv_metrics["active_days"] or 0,
                            "avg_time_on_page": float(pv_metrics["avg_time_on_page"] or 0),
                            "page_types_visited": pv_metrics["page_types_visited"] or 0
                        },
                        "attendance": {
                            "attendance_rate": float(att_metrics.get("attendance_rate", 0)),
                            "total_sessions": att_metrics.get("total_sessions", 0),
                            "present_sessions": att_metrics.get("present_sessions", 0)
                        }
                    },
                    "score_breakdown": {
                        "page_view_score": round(page_view_score, 2),
                        "activity_score": round(activity_score, 2),
                        "attendance_score": round(attendance_score, 2),
                        "time_score": round(time_score, 2)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            raise


# Global service instances
attendance_service = AttendanceAnalyticsService()
pageview_service = PageViewAnalyticsService()
