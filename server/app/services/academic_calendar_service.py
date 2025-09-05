"""
Academic Calendar and SCD Management Service.

Manages academic calendar setup, date dimensions, and slowly changing dimensions
for comprehensive educational analytics.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.models.academic_calendar import (
    AcademicYear, AcademicTerm, AcademicWeek, DateDimension,
    UserSCD, CourseSCD, EnrollmentSCD
)

logger = logging.getLogger(__name__)


class AcademicCalendarService:
    """Service for managing academic calendar and time dimensions."""
    
    def __init__(self):
        self.holidays = self._get_default_holidays()
    
    def _get_default_holidays(self) -> Dict[str, Dict[str, Any]]:
        """Get default holiday definitions."""
        return {
            "new_years": {"name": "New Year's Day", "month": 1, "day": 1, "type": "federal"},
            "mlk_day": {"name": "Martin Luther King Jr. Day", "month": 1, "day": "third_monday", "type": "federal"},
            "presidents_day": {"name": "Presidents' Day", "month": 2, "day": "third_monday", "type": "federal"},
            "memorial_day": {"name": "Memorial Day", "month": 5, "day": "last_monday", "type": "federal"},
            "independence_day": {"name": "Independence Day", "month": 7, "day": 4, "type": "federal"},
            "labor_day": {"name": "Labor Day", "month": 9, "day": "first_monday", "type": "federal"},
            "columbus_day": {"name": "Columbus Day", "month": 10, "day": "second_monday", "type": "federal"},
            "veterans_day": {"name": "Veterans Day", "month": 11, "day": 11, "type": "federal"},
            "thanksgiving": {"name": "Thanksgiving", "month": 11, "day": "fourth_thursday", "type": "federal"},
            "christmas": {"name": "Christmas Day", "month": 12, "day": 25, "type": "federal"},
            
            # Academic holidays
            "spring_break": {"name": "Spring Break", "type": "academic", "duration": 7},
            "fall_break": {"name": "Fall Break", "type": "academic", "duration": 2},
            "winter_break": {"name": "Winter Break", "type": "academic", "duration": 14}
        }
    
    async def create_academic_year(self, year_code: str, start_date: date, end_date: date) -> AcademicYear:
        """Create a new academic year."""
        try:
            async with AsyncSessionLocal() as db:
                # Check if academic year already exists
                existing = await db.execute(
                    select(AcademicYear).where(AcademicYear.year_code == year_code)
                )
                if existing.scalar_one_or_none():
                    raise ValueError(f"Academic year {year_code} already exists")
                
                # Create academic year
                academic_year = AcademicYear(
                    year_code=year_code,
                    year_name=f"Academic Year {year_code}",
                    start_date=start_date,
                    end_date=end_date,
                    is_current=False,
                    is_active=True
                )
                
                db.add(academic_year)
                await db.commit()
                await db.refresh(academic_year)
                
                logger.info(f"Created academic year: {year_code}")
                return academic_year
                
        except Exception as e:
            logger.error(f"Error creating academic year: {e}")
            raise
    
    async def create_academic_term(self, term_data: Dict[str, Any]) -> AcademicTerm:
        """Create a new academic term."""
        try:
            async with AsyncSessionLocal() as db:
                # Validate academic year exists
                academic_year = await db.execute(
                    select(AcademicYear).where(AcademicYear.id == term_data["academic_year_id"])
                )
                if not academic_year.scalar_one_or_none():
                    raise ValueError(f"Academic year {term_data['academic_year_id']} not found")
                
                # Create academic term
                term = AcademicTerm(
                    term_code=term_data["term_code"],
                    term_name=term_data["term_name"],
                    term_type=term_data["term_type"],
                    academic_year_id=term_data["academic_year_id"],
                    start_date=term_data["start_date"],
                    end_date=term_data["end_date"],
                    registration_start=term_data.get("registration_start"),
                    registration_end=term_data.get("registration_end"),
                    classes_start=term_data.get("classes_start"),
                    classes_end=term_data.get("classes_end"),
                    finals_start=term_data.get("finals_start"),
                    finals_end=term_data.get("finals_end"),
                    grades_due=term_data.get("grades_due"),
                    is_current=term_data.get("is_current", False),
                    is_active=True
                )
                
                db.add(term)
                await db.commit()
                await db.refresh(term)
                
                # Generate weeks for this term
                await self._generate_academic_weeks(db, term)
                
                logger.info(f"Created academic term: {term_data['term_code']}")
                return term
                
        except Exception as e:
            logger.error(f"Error creating academic term: {e}")
            raise
    
    async def _generate_academic_weeks(self, db: AsyncSession, term: AcademicTerm):
        """Generate academic weeks for a term."""
        try:
            current_date = term.start_date
            week_number = 1
            
            while current_date <= term.end_date:
                # Calculate week end (Sunday)
                days_until_sunday = (6 - current_date.weekday()) % 7
                week_end = current_date + timedelta(days=days_until_sunday)
                
                # Don't exceed term end date
                if week_end > term.end_date:
                    week_end = term.end_date
                
                # Generate week code
                week_code = f"{term.term_code}-W{week_number:02d}"
                
                # Determine week characteristics
                is_break_week = self._is_break_week(current_date, term)
                is_exam_week = self._is_exam_week(current_date, term)
                is_registration_week = self._is_registration_week(current_date, term)
                
                week_type = "regular"
                if is_break_week:
                    week_type = "break"
                elif is_exam_week:
                    week_type = "exam"
                elif is_registration_week:
                    week_type = "registration"
                
                # Check for holidays
                has_holiday, holiday_name = self._check_holiday_in_week(current_date, week_end)
                
                # Create academic week
                academic_week = AcademicWeek(
                    week_code=week_code,
                    week_number=week_number,
                    year_week_number=self._calculate_year_week_number(current_date, term),
                    calendar_week=current_date.isocalendar()[1],
                    academic_year_id=term.academic_year_id,
                    term_id=term.id,
                    start_date=current_date,
                    end_date=week_end,
                    is_current=self._is_current_week(current_date, week_end),
                    is_break_week=is_break_week,
                    is_exam_week=is_exam_week,
                    is_registration_week=is_registration_week,
                    week_type=week_type,
                    has_holiday=has_holiday,
                    holiday_name=holiday_name
                )
                
                db.add(academic_week)
                
                # Move to next week
                current_date = week_end + timedelta(days=1)
                week_number += 1
            
            await db.commit()
            logger.info(f"Generated {week_number - 1} weeks for term {term.term_code}")
            
        except Exception as e:
            logger.error(f"Error generating academic weeks: {e}")
            raise
    
    def _is_break_week(self, week_start: date, term: AcademicTerm) -> bool:
        """Determine if a week is a break week."""
        # Simple heuristic - you would customize this based on your calendar
        if term.term_type.lower() == "spring":
            # Spring break is typically in March
            return week_start.month == 3 and week_start.day >= 15
        elif term.term_type.lower() == "fall":
            # Fall break is typically in October
            return week_start.month == 10 and week_start.day >= 15
        return False
    
    def _is_exam_week(self, week_start: date, term: AcademicTerm) -> bool:
        """Determine if a week is an exam week."""
        if term.finals_start and term.finals_end:
            return term.finals_start <= week_start <= term.finals_end
        return False
    
    def _is_registration_week(self, week_start: date, term: AcademicTerm) -> bool:
        """Determine if a week is a registration week."""
        if term.registration_start and term.registration_end:
            return term.registration_start <= week_start <= term.registration_end
        return False
    
    def _calculate_year_week_number(self, week_start: date, term: AcademicTerm) -> int:
        """Calculate week number within academic year."""
        # Get academic year start date
        year_start = term.academic_year.start_date if hasattr(term, 'academic_year') else week_start
        delta = week_start - year_start
        return (delta.days // 7) + 1
    
    def _is_current_week(self, week_start: date, week_end: date) -> bool:
        """Check if this is the current week."""
        today = date.today()
        return week_start <= today <= week_end
    
    def _check_holiday_in_week(self, week_start: date, week_end: date) -> Tuple[bool, Optional[str]]:
        """Check if there's a holiday in the given week."""
        for holiday_key, holiday_info in self.holidays.items():
            if holiday_info["type"] == "academic":
                continue  # Skip academic holidays for now
            
            holiday_date = self._calculate_holiday_date(week_start.year, holiday_info)
            if holiday_date and week_start <= holiday_date <= week_end:
                return True, holiday_info["name"]
        
        return False, None
    
    def _calculate_holiday_date(self, year: int, holiday_info: Dict[str, Any]) -> Optional[date]:
        """Calculate the date of a holiday for a given year."""
        try:
            month = holiday_info["month"]
            day_spec = holiday_info["day"]
            
            if isinstance(day_spec, int):
                return date(year, month, day_spec)
            elif isinstance(day_spec, str):
                if day_spec == "third_monday":
                    return self._get_nth_weekday(year, month, 0, 3)  # Monday = 0
                elif day_spec == "last_monday":
                    return self._get_last_weekday(year, month, 0)
                elif day_spec == "first_monday":
                    return self._get_nth_weekday(year, month, 0, 1)
                elif day_spec == "second_monday":
                    return self._get_nth_weekday(year, month, 0, 2)
                elif day_spec == "fourth_thursday":
                    return self._get_nth_weekday(year, month, 3, 4)  # Thursday = 3
            
            return None
            
        except Exception:
            return None
    
    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int) -> date:
        """Get the nth occurrence of a weekday in a month."""
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate days to add to get to the first occurrence of the target weekday
        days_to_add = (weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=days_to_add)
        
        # Add weeks to get to the nth occurrence
        target_date = first_occurrence + timedelta(weeks=n-1)
        
        # Make sure it's still in the same month
        if target_date.month != month:
            raise ValueError(f"No {n}th occurrence of weekday {weekday} in {year}-{month}")
        
        return target_date
    
    def _get_last_weekday(self, year: int, month: int, weekday: int) -> date:
        """Get the last occurrence of a weekday in a month."""
        # Start from the last day of the month and work backwards
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Calculate how many days to subtract to get to the target weekday
        days_to_subtract = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_to_subtract)
    
    async def populate_date_dimension(self, start_year: int, end_year: int):
        """Populate the date dimension table for the given year range."""
        try:
            async with AsyncSessionLocal() as db:
                start_date = date(start_year, 1, 1)
                end_date = date(end_year, 12, 31)
                
                current_date = start_date
                batch_size = 1000
                batch = []
                
                while current_date <= end_date:
                    date_record = self._create_date_record(current_date)
                    batch.append(date_record)
                    
                    if len(batch) >= batch_size:
                        await self._insert_date_batch(db, batch)
                        batch = []
                    
                    current_date += timedelta(days=1)
                
                # Insert remaining records
                if batch:
                    await self._insert_date_batch(db, batch)
                
                await db.commit()
                logger.info(f"Populated date dimension from {start_year} to {end_year}")
                
        except Exception as e:
            logger.error(f"Error populating date dimension: {e}")
            raise
    
    def _create_date_record(self, target_date: date) -> Dict[str, Any]:
        """Create a date dimension record for the given date."""
        # Calculate date key (YYYYMMDD)
        date_key = int(target_date.strftime("%Y%m%d"))
        
        # Get date components
        year = target_date.year
        month = target_date.month
        day = target_date.day
        
        # Calculate derived fields
        quarter = (month - 1) // 3 + 1
        day_of_year = target_date.timetuple().tm_yday
        week_of_year = target_date.isocalendar()[1]
        day_of_week = target_date.isoweekday()  # 1=Monday, 7=Sunday
        
        # Calculate week of month
        first_day_of_month = target_date.replace(day=1)
        week_of_month = ((day - 1) // 7) + 1
        
        # Get names
        month_name = target_date.strftime("%B")
        month_abbrev = target_date.strftime("%b")
        day_name = target_date.strftime("%A")
        day_abbrev = target_date.strftime("%a")
        
        # Calculate flags
        is_weekend = day_of_week in [6, 7]  # Saturday, Sunday
        is_business_day = not is_weekend
        
        # Check for holidays
        is_holiday = False
        holiday_name = None
        holiday_type = None
        
        for holiday_key, holiday_info in self.holidays.items():
            if holiday_info["type"] == "academic":
                continue
            
            holiday_date = self._calculate_holiday_date(year, holiday_info)
            if holiday_date == target_date:
                is_holiday = True
                holiday_name = holiday_info["name"]
                holiday_type = holiday_info["type"]
                is_business_day = False
                break
        
        # Calculate fiscal year (assuming July 1 start)
        if month >= 7:
            fiscal_year = year + 1
        else:
            fiscal_year = year
        
        fiscal_quarter = ((month - 7) % 12) // 3 + 1
        fiscal_month = ((month - 7) % 12) + 1
        
        # Calculate relative flags
        today = date.today()
        is_today = target_date == today
        is_current_week = abs((target_date - today).days) < 7
        is_current_month = (target_date.year == today.year and target_date.month == today.month)
        is_current_quarter = (target_date.year == today.year and 
                            ((target_date.month - 1) // 3) == ((today.month - 1) // 3))
        is_current_year = target_date.year == today.year
        
        return {
            "date_key": date_key,
            "full_date": target_date,
            "year": year,
            "quarter": quarter,
            "month": month,
            "month_name": month_name,
            "month_abbrev": month_abbrev,
            "week_of_year": week_of_year,
            "week_of_month": week_of_month,
            "day_of_year": day_of_year,
            "day_of_month": day,
            "day_of_week": day_of_week,
            "day_name": day_name,
            "day_abbrev": day_abbrev,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "is_business_day": is_business_day,
            "is_academic_day": is_business_day and not is_holiday,
            "holiday_name": holiday_name,
            "holiday_type": holiday_type,
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "fiscal_month": fiscal_month,
            "is_today": is_today,
            "is_current_week": is_current_week,
            "is_current_month": is_current_month,
            "is_current_quarter": is_current_quarter,
            "is_current_year": is_current_year
        }
    
    async def _insert_date_batch(self, db: AsyncSession, batch: List[Dict[str, Any]]):
        """Insert a batch of date records."""
        # Use upsert to handle duplicates
        stmt = pg_insert(DateDimension).values(batch)
        stmt = stmt.on_conflict_do_nothing(index_elements=['full_date'])
        await db.execute(stmt)
    
    async def update_current_flags(self):
        """Update current flags for academic years, terms, and weeks."""
        try:
            async with AsyncSessionLocal() as db:
                today = date.today()
                
                # Update academic years
                await db.execute(
                    update(AcademicYear)
                    .values(is_current=False)
                )
                
                await db.execute(
                    update(AcademicYear)
                    .where(and_(
                        AcademicYear.start_date <= today,
                        AcademicYear.end_date >= today
                    ))
                    .values(is_current=True)
                )
                
                # Update terms
                await db.execute(
                    update(AcademicTerm)
                    .values(is_current=False)
                )
                
                await db.execute(
                    update(AcademicTerm)
                    .where(and_(
                        AcademicTerm.start_date <= today,
                        AcademicTerm.end_date >= today
                    ))
                    .values(is_current=True)
                )
                
                # Update weeks
                await db.execute(
                    update(AcademicWeek)
                    .values(is_current=False)
                )
                
                await db.execute(
                    update(AcademicWeek)
                    .where(and_(
                        AcademicWeek.start_date <= today,
                        AcademicWeek.end_date >= today
                    ))
                    .values(is_current=True)
                )
                
                # Update date dimension
                await db.execute(
                    update(DateDimension)
                    .values(is_today=False, is_current_week=False, 
                           is_current_month=False, is_current_quarter=False)
                )
                
                # Set today
                await db.execute(
                    update(DateDimension)
                    .where(DateDimension.full_date == today)
                    .values(is_today=True)
                )
                
                # Set current week (within 7 days)
                week_start = today - timedelta(days=7)
                week_end = today + timedelta(days=7)
                await db.execute(
                    update(DateDimension)
                    .where(and_(
                        DateDimension.full_date >= week_start,
                        DateDimension.full_date <= week_end
                    ))
                    .values(is_current_week=True)
                )
                
                # Set current month
                await db.execute(
                    update(DateDimension)
                    .where(and_(
                        DateDimension.year == today.year,
                        DateDimension.month == today.month
                    ))
                    .values(is_current_month=True)
                )
                
                # Set current quarter
                current_quarter = (today.month - 1) // 3 + 1
                await db.execute(
                    update(DateDimension)
                    .where(and_(
                        DateDimension.year == today.year,
                        DateDimension.quarter == current_quarter
                    ))
                    .values(is_current_quarter=True)
                )
                
                await db.commit()
                logger.info("Updated current flags for calendar dimensions")
                
        except Exception as e:
            logger.error(f"Error updating current flags: {e}")
            raise


class SCDService:
    """Service for managing Slowly Changing Dimensions."""
    
    async def update_user_scd(self, user_id: int, new_attributes: Dict[str, Any], 
                            change_reason: str, changed_by: int):
        """Update user SCD with new attributes."""
        try:
            async with AsyncSessionLocal() as db:
                today = date.today()
                
                # Get current record
                current_record = await db.execute(
                    select(UserSCD)
                    .where(and_(UserSCD.user_id == user_id, UserSCD.is_current == True))
                )
                current = current_record.scalar_one_or_none()
                
                if current:
                    # Check if attributes have actually changed
                    if not self._has_user_attributes_changed(current, new_attributes):
                        return current
                    
                    # Expire current record
                    current.expiry_date = today
                    current.is_current = False
                    
                    # Create new version
                    new_version = current.version + 1
                else:
                    new_version = 1
                
                # Create new current record
                new_record = UserSCD(
                    user_id=user_id,
                    effective_date=today,
                    expiry_date=None,
                    is_current=True,
                    version=new_version,
                    name=new_attributes.get("name", ""),
                    email=new_attributes.get("email", ""),
                    role=new_attributes.get("role", ""),
                    department=new_attributes.get("department"),
                    major=new_attributes.get("major"),
                    year_level=new_attributes.get("year_level"),
                    enrollment_status=new_attributes.get("enrollment_status", "active"),
                    gpa=new_attributes.get("gpa"),
                    change_reason=change_reason,
                    changed_by=changed_by
                )
                
                db.add(new_record)
                await db.commit()
                await db.refresh(new_record)
                
                logger.info(f"Updated user SCD for user {user_id}, version {new_version}")
                return new_record
                
        except Exception as e:
            logger.error(f"Error updating user SCD: {e}")
            raise
    
    def _has_user_attributes_changed(self, current: UserSCD, new_attributes: Dict[str, Any]) -> bool:
        """Check if user attributes have changed."""
        fields_to_check = ["name", "email", "role", "department", "major", 
                          "year_level", "enrollment_status", "gpa"]
        
        for field in fields_to_check:
            current_value = getattr(current, field, None)
            new_value = new_attributes.get(field)
            if current_value != new_value:
                return True
        
        return False
    
    async def update_course_scd(self, course_id: int, new_attributes: Dict[str, Any],
                              change_reason: str, changed_by: int):
        """Update course SCD with new attributes."""
        try:
            async with AsyncSessionLocal() as db:
                today = date.today()
                
                # Get current record
                current_record = await db.execute(
                    select(CourseSCD)
                    .where(and_(CourseSCD.course_id == course_id, CourseSCD.is_current == True))
                )
                current = current_record.scalar_one_or_none()
                
                if current:
                    # Check if attributes have actually changed
                    if not self._has_course_attributes_changed(current, new_attributes):
                        return current
                    
                    # Expire current record
                    current.expiry_date = today
                    current.is_current = False
                    
                    # Create new version
                    new_version = current.version + 1
                else:
                    new_version = 1
                
                # Create new current record
                new_record = CourseSCD(
                    course_id=course_id,
                    effective_date=today,
                    expiry_date=None,
                    is_current=True,
                    version=new_version,
                    name=new_attributes.get("name", ""),
                    code=new_attributes.get("code", ""),
                    description=new_attributes.get("description"),
                    credits=new_attributes.get("credits"),
                    department=new_attributes.get("department"),
                    instructor_id=new_attributes.get("instructor_id"),
                    instructor_name=new_attributes.get("instructor_name"),
                    enrollment_count=new_attributes.get("enrollment_count", 0),
                    capacity=new_attributes.get("capacity"),
                    status=new_attributes.get("status", "active"),
                    term_id=new_attributes.get("term_id"),
                    academic_year_id=new_attributes.get("academic_year_id"),
                    change_reason=change_reason,
                    changed_by=changed_by
                )
                
                db.add(new_record)
                await db.commit()
                await db.refresh(new_record)
                
                logger.info(f"Updated course SCD for course {course_id}, version {new_version}")
                return new_record
                
        except Exception as e:
            logger.error(f"Error updating course SCD: {e}")
            raise
    
    def _has_course_attributes_changed(self, current: CourseSCD, new_attributes: Dict[str, Any]) -> bool:
        """Check if course attributes have changed."""
        fields_to_check = ["name", "code", "description", "credits", "department",
                          "instructor_id", "instructor_name", "enrollment_count",
                          "capacity", "status", "term_id", "academic_year_id"]
        
        for field in fields_to_check:
            current_value = getattr(current, field, None)
            new_value = new_attributes.get(field)
            if current_value != new_value:
                return True
        
        return False
    
    async def get_user_history(self, user_id: int) -> List[UserSCD]:
        """Get the complete history of a user's attributes."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(UserSCD)
                    .where(UserSCD.user_id == user_id)
                    .order_by(UserSCD.effective_date.desc())
                )
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Error getting user history: {e}")
            return []
    
    async def get_user_attributes_at_date(self, user_id: int, target_date: date) -> Optional[UserSCD]:
        """Get user attributes as they were on a specific date."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(UserSCD)
                    .where(and_(
                        UserSCD.user_id == user_id,
                        UserSCD.effective_date <= target_date,
                        or_(UserSCD.expiry_date.is_(None), UserSCD.expiry_date > target_date)
                    ))
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Error getting user attributes at date: {e}")
            return None


# Global service instances
academic_calendar_service = AcademicCalendarService()
scd_service = SCDService()
