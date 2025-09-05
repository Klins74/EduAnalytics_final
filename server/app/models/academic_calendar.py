"""
Academic Calendar and Time Dimension models for analytics.

Provides comprehensive time-based dimensions for educational analytics
including academic years, terms, weeks, and SCD (Slowly Changing Dimensions).
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date

from app.db.base_class import Base


class AcademicYear(Base):
    """Academic year dimension table."""
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True, index=True)
    year_code = Column(String(10), unique=True, nullable=False, index=True)  # e.g., "2023-24"
    year_name = Column(String(50), nullable=False)  # e.g., "Academic Year 2023-2024"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    terms = relationship("AcademicTerm", back_populates="academic_year")
    weeks = relationship("AcademicWeek", back_populates="academic_year")

    def __repr__(self):
        return f"<AcademicYear(year_code='{self.year_code}', name='{self.year_name}')>"


class AcademicTerm(Base):
    """Academic term/semester dimension table."""
    __tablename__ = "academic_terms"

    id = Column(Integer, primary_key=True, index=True)
    term_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "2023-24-FALL"
    term_name = Column(String(50), nullable=False)  # e.g., "Fall 2023"
    term_type = Column(String(20), nullable=False)  # fall, spring, summer, winter
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Term-specific dates
    registration_start = Column(Date)
    registration_end = Column(Date)
    classes_start = Column(Date)
    classes_end = Column(Date)
    finals_start = Column(Date)
    finals_end = Column(Date)
    grades_due = Column(Date)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    academic_year = relationship("AcademicYear", back_populates="terms")
    weeks = relationship("AcademicWeek", back_populates="term")
    courses = relationship("Course", back_populates="term")

    def __repr__(self):
        return f"<AcademicTerm(term_code='{self.term_code}', name='{self.term_name}')>"


class AcademicWeek(Base):
    """Academic week dimension table for detailed time analysis."""
    __tablename__ = "academic_weeks"

    id = Column(Integer, primary_key=True, index=True)
    week_code = Column(String(30), unique=True, nullable=False, index=True)  # e.g., "2023-24-FALL-W01"
    week_number = Column(Integer, nullable=False)  # Week number within term (1-16)
    year_week_number = Column(Integer, nullable=False)  # Week number within academic year
    calendar_week = Column(Integer, nullable=False)  # ISO week number (1-53)
    
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    term_id = Column(Integer, ForeignKey("academic_terms.id"), nullable=False)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Week characteristics
    is_current = Column(Boolean, default=False)
    is_break_week = Column(Boolean, default=False)
    is_exam_week = Column(Boolean, default=False)
    is_registration_week = Column(Boolean, default=False)
    week_type = Column(String(20), default="regular")  # regular, break, exam, registration
    
    # Special events/holidays
    has_holiday = Column(Boolean, default=False)
    holiday_name = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    academic_year = relationship("AcademicYear", back_populates="weeks")
    term = relationship("AcademicTerm", back_populates="weeks")

    def __repr__(self):
        return f"<AcademicWeek(week_code='{self.week_code}', week_number={self.week_number})>"


class DateDimension(Base):
    """Date dimension table for comprehensive date analytics."""
    __tablename__ = "date_dimension"

    date_key = Column(Integer, primary_key=True)  # YYYYMMDD format
    full_date = Column(Date, unique=True, nullable=False, index=True)
    
    # Date components
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False, index=True)
    month_name = Column(String(20), nullable=False)
    month_abbrev = Column(String(3), nullable=False)
    week_of_year = Column(Integer, nullable=False)
    week_of_month = Column(Integer, nullable=False)
    day_of_year = Column(Integer, nullable=False)
    day_of_month = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 1=Monday, 7=Sunday
    day_name = Column(String(20), nullable=False)
    day_abbrev = Column(String(3), nullable=False)
    
    # Business/academic flags
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    is_business_day = Column(Boolean, default=True)
    is_academic_day = Column(Boolean, default=True)
    
    # Academic context
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"))
    term_id = Column(Integer, ForeignKey("academic_terms.id"))
    academic_week_id = Column(Integer, ForeignKey("academic_weeks.id"))
    
    # Holiday information
    holiday_name = Column(String(100))
    holiday_type = Column(String(50))  # federal, state, academic, religious
    
    # Fiscal information
    fiscal_year = Column(Integer)
    fiscal_quarter = Column(Integer)
    fiscal_month = Column(Integer)
    
    # Relative date flags
    is_today = Column(Boolean, default=False)
    is_current_week = Column(Boolean, default=False)
    is_current_month = Column(Boolean, default=False)
    is_current_quarter = Column(Boolean, default=False)
    is_current_year = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DateDimension(date_key={self.date_key}, full_date='{self.full_date}')>"


# SCD (Slowly Changing Dimension) Models

class UserSCD(Base):
    """User Slowly Changing Dimension for tracking user attribute changes over time."""
    __tablename__ = "user_scd"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # SCD Type 2 fields
    effective_date = Column(Date, nullable=False, index=True)
    expiry_date = Column(Date, index=True)  # NULL for current record
    is_current = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)
    
    # User attributes that change over time
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    department = Column(String(100))
    major = Column(String(100))
    year_level = Column(String(20))  # freshman, sophomore, junior, senior, graduate
    enrollment_status = Column(String(20))  # active, inactive, graduated, withdrawn
    gpa = Column(String(10))  # Current GPA range
    
    # Change tracking
    change_reason = Column(String(255))
    changed_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserSCD(user_id={self.user_id}, version={self.version}, is_current={self.is_current})>"


class CourseSCD(Base):
    """Course Slowly Changing Dimension for tracking course attribute changes over time."""
    __tablename__ = "course_scd"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    
    # SCD Type 2 fields
    effective_date = Column(Date, nullable=False, index=True)
    expiry_date = Column(Date, index=True)
    is_current = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)
    
    # Course attributes that change over time
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    credits = Column(Integer)
    department = Column(String(100))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    instructor_name = Column(String(255))
    enrollment_count = Column(Integer, default=0)
    capacity = Column(Integer)
    status = Column(String(20))  # active, inactive, cancelled, completed
    
    # Academic context
    term_id = Column(Integer, ForeignKey("academic_terms.id"))
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"))
    
    # Change tracking
    change_reason = Column(String(255))
    changed_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CourseSCD(course_id={self.course_id}, version={self.version}, is_current={self.is_current})>"


class EnrollmentSCD(Base):
    """Enrollment Slowly Changing Dimension for tracking enrollment changes over time."""
    __tablename__ = "enrollment_scd"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    
    # SCD Type 2 fields
    effective_date = Column(Date, nullable=False, index=True)
    expiry_date = Column(Date, index=True)
    is_current = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)
    
    # Enrollment attributes that change over time
    status = Column(String(20), nullable=False)  # enrolled, dropped, completed, withdrawn
    role = Column(String(50))  # student, ta, observer
    grade = Column(String(10))
    grade_points = Column(String(10))
    participation_score = Column(Integer)
    attendance_rate = Column(String(10))  # percentage
    
    # Academic context
    term_id = Column(Integer, ForeignKey("academic_terms.id"))
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"))
    
    # Change tracking
    change_reason = Column(String(255))
    changed_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EnrollmentSCD(enrollment_id={self.enrollment_id}, version={self.version}, is_current={self.is_current})>"


# Indexes for performance
Index('idx_user_scd_user_current', UserSCD.user_id, UserSCD.is_current)
Index('idx_user_scd_effective_date', UserSCD.effective_date)
Index('idx_course_scd_course_current', CourseSCD.course_id, CourseSCD.is_current)
Index('idx_course_scd_effective_date', CourseSCD.effective_date)
Index('idx_enrollment_scd_enrollment_current', EnrollmentSCD.enrollment_id, EnrollmentSCD.is_current)
Index('idx_enrollment_scd_user_course', EnrollmentSCD.user_id, EnrollmentSCD.course_id, EnrollmentSCD.is_current)
Index('idx_date_dimension_academic', DateDimension.academic_year_id, DateDimension.term_id)
Index('idx_academic_weeks_term_week', AcademicWeek.term_id, AcademicWeek.week_number)
