"""
Data Mart ETL Service for transforming Canvas DAP raw data to analytics marts.

Implements dimensional modeling with star schema and data lineage tracking.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.models.canvas_sync import CanvasSyncState
from app.crud.canvas_sync import CanvasSyncCRUD
from app.core.config import settings
from app.services.migration_manager import MigrationRisk

logger = logging.getLogger(__name__)


class ETLStatus(Enum):
    """ETL job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataMartType(Enum):
    """Data mart type enumeration."""
    STUDENT_PERFORMANCE = "student_performance"
    COURSE_ANALYTICS = "course_analytics"
    ASSIGNMENT_METRICS = "assignment_metrics"
    ENGAGEMENT_TRENDS = "engagement_trends"
    LEARNING_OUTCOMES = "learning_outcomes"


@dataclass
class ETLJobConfig:
    """Configuration for ETL job."""
    mart_type: DataMartType
    source_tables: List[str]
    target_table: str
    schedule: str  # Cron expression
    retention_days: int
    data_quality_checks: List[str]
    dependencies: List[str]  # Other jobs this depends on


@dataclass
class DataLineage:
    """Data lineage tracking information."""
    source_system: str
    source_table: str
    source_columns: List[str]
    target_table: str
    target_columns: List[str]
    transformation_logic: str
    created_at: datetime
    created_by: str


class DimensionManager:
    """Manages dimension tables for star schema."""
    
    def __init__(self):
        self.sync_crud = CanvasSyncCRUD()
    
    async def create_dimension_tables(self, db: AsyncSession):
        """Create or update dimension tables."""
        
        # Date dimension
        await self._create_date_dimension(db)
        
        # Student dimension
        await self._create_student_dimension(db)
        
        # Course dimension
        await self._create_course_dimension(db)
        
        # Assignment dimension
        await self._create_assignment_dimension(db)
        
        # Instructor dimension
        await self._create_instructor_dimension(db)
    
    async def _create_date_dimension(self, db: AsyncSession):
        """Create date dimension table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS dim_date (
            date_key INTEGER PRIMARY KEY,
            date_actual DATE UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            month INTEGER NOT NULL,
            month_name VARCHAR(20) NOT NULL,
            week_of_year INTEGER NOT NULL,
            day_of_year INTEGER NOT NULL,
            day_of_month INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            day_name VARCHAR(20) NOT NULL,
            is_weekend BOOLEAN NOT NULL,
            academic_year INTEGER,
            academic_quarter INTEGER,
            academic_week INTEGER,
            is_holiday BOOLEAN DEFAULT FALSE,
            holiday_name VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_dim_date_actual ON dim_date(date_actual);
        CREATE INDEX IF NOT EXISTS idx_dim_date_academic_year ON dim_date(academic_year);
        """
        
        await db.execute(text(create_table_sql))
        
        # Populate date dimension for current and next year
        await self._populate_date_dimension(db)
    
    async def _populate_date_dimension(self, db: AsyncSession):
        """Populate date dimension with date range."""
        # Check if data exists
        existing_count = await db.scalar(text("SELECT COUNT(*) FROM dim_date"))
        
        if existing_count > 0:
            logger.info("Date dimension already populated")
            return
        
        logger.info("Populating date dimension...")
        
        start_date = date(2020, 1, 1)  # Historical data
        end_date = date(2030, 12, 31)  # Future planning
        
        current_date = start_date
        batch_size = 1000
        dates_batch = []
        
        while current_date <= end_date:
            date_key = int(current_date.strftime("%Y%m%d"))
            
            # Academic year calculation (assuming September start)
            if current_date.month >= 9:
                academic_year = current_date.year
            else:
                academic_year = current_date.year - 1
            
            # Academic quarter (Fall=1, Spring=2, Summer=3)
            if current_date.month in [9, 10, 11, 12]:
                academic_quarter = 1  # Fall
            elif current_date.month in [1, 2, 3, 4]:
                academic_quarter = 2  # Spring
            else:
                academic_quarter = 3  # Summer
            
            # Academic week (week of academic year)
            academic_start = date(academic_year, 9, 1)
            academic_week = ((current_date - academic_start).days // 7) + 1
            
            date_record = {
                'date_key': date_key,
                'date_actual': current_date,
                'year': current_date.year,
                'quarter': (current_date.month - 1) // 3 + 1,
                'month': current_date.month,
                'month_name': current_date.strftime("%B"),
                'week_of_year': current_date.isocalendar()[1],
                'day_of_year': current_date.timetuple().tm_yday,
                'day_of_month': current_date.day,
                'day_of_week': current_date.weekday() + 1,  # 1=Monday, 7=Sunday
                'day_name': current_date.strftime("%A"),
                'is_weekend': current_date.weekday() >= 5,
                'academic_year': academic_year,
                'academic_quarter': academic_quarter,
                'academic_week': academic_week
            }
            
            dates_batch.append(date_record)
            
            if len(dates_batch) >= batch_size:
                await self._insert_date_batch(db, dates_batch)
                dates_batch = []
            
            current_date += timedelta(days=1)
        
        # Insert remaining dates
        if dates_batch:
            await self._insert_date_batch(db, dates_batch)
        
        logger.info(f"Date dimension populated from {start_date} to {end_date}")
    
    async def _insert_date_batch(self, db: AsyncSession, dates_batch: List[Dict]):
        """Insert batch of dates into dimension table."""
        insert_sql = """
        INSERT INTO dim_date (
            date_key, date_actual, year, quarter, month, month_name,
            week_of_year, day_of_year, day_of_month, day_of_week, day_name,
            is_weekend, academic_year, academic_quarter, academic_week
        ) VALUES (
            :date_key, :date_actual, :year, :quarter, :month, :month_name,
            :week_of_year, :day_of_year, :day_of_month, :day_of_week, :day_name,
            :is_weekend, :academic_year, :academic_quarter, :academic_week
        ) ON CONFLICT (date_actual) DO NOTHING
        """
        
        await db.execute(text(insert_sql), dates_batch)
    
    async def _create_student_dimension(self, db: AsyncSession):
        """Create student dimension table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS dim_student (
            student_key SERIAL PRIMARY KEY,
            student_id INTEGER UNIQUE NOT NULL,
            canvas_user_id INTEGER,
            student_name VARCHAR(255),
            email VARCHAR(255),
            enrollment_status VARCHAR(50),
            classification VARCHAR(50),
            major VARCHAR(100),
            department VARCHAR(100),
            advisor VARCHAR(255),
            entry_date DATE,
            expected_graduation DATE,
            gpa DECIMAL(3,2),
            credit_hours INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_dim_student_canvas_id ON dim_student(canvas_user_id);
        CREATE INDEX IF NOT EXISTS idx_dim_student_status ON dim_student(enrollment_status);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _create_course_dimension(self, db: AsyncSession):
        """Create course dimension table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS dim_course (
            course_key SERIAL PRIMARY KEY,
            course_id INTEGER UNIQUE NOT NULL,
            canvas_course_id INTEGER,
            course_code VARCHAR(20),
            course_name VARCHAR(255),
            course_description TEXT,
            department VARCHAR(100),
            college VARCHAR(100),
            credit_hours INTEGER,
            course_level VARCHAR(20),
            semester VARCHAR(20),
            academic_year INTEGER,
            start_date DATE,
            end_date DATE,
            enrollment_term VARCHAR(50),
            course_format VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_dim_course_canvas_id ON dim_course(canvas_course_id);
        CREATE INDEX IF NOT EXISTS idx_dim_course_code ON dim_course(course_code);
        CREATE INDEX IF NOT EXISTS idx_dim_course_term ON dim_course(enrollment_term);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _create_assignment_dimension(self, db: AsyncSession):
        """Create assignment dimension table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS dim_assignment (
            assignment_key SERIAL PRIMARY KEY,
            assignment_id INTEGER UNIQUE NOT NULL,
            canvas_assignment_id INTEGER,
            assignment_name VARCHAR(255),
            assignment_type VARCHAR(50),
            points_possible DECIMAL(10,2),
            grading_type VARCHAR(50),
            assignment_group VARCHAR(100),
            due_date TIMESTAMP WITH TIME ZONE,
            unlock_date TIMESTAMP WITH TIME ZONE,
            lock_date TIMESTAMP WITH TIME ZONE,
            is_published BOOLEAN,
            submission_types TEXT,
            course_key INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_dim_assignment_canvas_id ON dim_assignment(canvas_assignment_id);
        CREATE INDEX IF NOT EXISTS idx_dim_assignment_type ON dim_assignment(assignment_type);
        CREATE INDEX IF NOT EXISTS idx_dim_assignment_due_date ON dim_assignment(due_date);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _create_instructor_dimension(self, db: AsyncSession):
        """Create instructor dimension table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS dim_instructor (
            instructor_key SERIAL PRIMARY KEY,
            instructor_id INTEGER UNIQUE NOT NULL,
            canvas_user_id INTEGER,
            instructor_name VARCHAR(255),
            email VARCHAR(255),
            department VARCHAR(100),
            title VARCHAR(100),
            employment_status VARCHAR(50),
            hire_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_dim_instructor_canvas_id ON dim_instructor(canvas_user_id);
        CREATE INDEX IF NOT EXISTS idx_dim_instructor_department ON dim_instructor(department);
        """
        
        await db.execute(text(create_table_sql))


class FactTableManager:
    """Manages fact tables for star schema."""
    
    async def create_fact_tables(self, db: AsyncSession):
        """Create fact tables."""
        
        # Student performance fact
        await self._create_student_performance_fact(db)
        
        # Course engagement fact
        await self._create_course_engagement_fact(db)
        
        # Assignment submission fact
        await self._create_assignment_submission_fact(db)
        
        # Learning outcome fact
        await self._create_learning_outcome_fact(db)
    
    async def _create_student_performance_fact(self, db: AsyncSession):
        """Create student performance fact table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS fact_student_performance (
            performance_key SERIAL PRIMARY KEY,
            student_key INTEGER NOT NULL,
            course_key INTEGER NOT NULL,
            assignment_key INTEGER,
            date_key INTEGER NOT NULL,
            instructor_key INTEGER,
            
            -- Measures
            grade_points DECIMAL(10,2),
            points_earned DECIMAL(10,2),
            points_possible DECIMAL(10,2),
            grade_percentage DECIMAL(5,2),
            submission_count INTEGER DEFAULT 0,
            late_submission_count INTEGER DEFAULT 0,
            on_time_submission_count INTEGER DEFAULT 0,
            missing_submission_count INTEGER DEFAULT 0,
            revision_count INTEGER DEFAULT 0,
            
            -- Time measures
            time_to_first_submission INTEGER, -- minutes
            time_spent_on_assignment INTEGER, -- minutes
            
            -- Engagement measures
            page_views INTEGER DEFAULT 0,
            participation_count INTEGER DEFAULT 0,
            discussion_posts INTEGER DEFAULT 0,
            
            -- Quality measures
            feedback_score DECIMAL(3,2),
            peer_review_score DECIMAL(3,2),
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
            FOREIGN KEY (course_key) REFERENCES dim_course(course_key),
            FOREIGN KEY (assignment_key) REFERENCES dim_assignment(assignment_key),
            FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (instructor_key) REFERENCES dim_instructor(instructor_key)
        );
        
        CREATE INDEX IF NOT EXISTS idx_fact_student_perf_student ON fact_student_performance(student_key);
        CREATE INDEX IF NOT EXISTS idx_fact_student_perf_course ON fact_student_performance(course_key);
        CREATE INDEX IF NOT EXISTS idx_fact_student_perf_date ON fact_student_performance(date_key);
        CREATE INDEX IF NOT EXISTS idx_fact_student_perf_assignment ON fact_student_performance(assignment_key);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _create_course_engagement_fact(self, db: AsyncSession):
        """Create course engagement fact table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS fact_course_engagement (
            engagement_key SERIAL PRIMARY KEY,
            student_key INTEGER NOT NULL,
            course_key INTEGER NOT NULL,
            date_key INTEGER NOT NULL,
            instructor_key INTEGER,
            
            -- Engagement measures
            login_count INTEGER DEFAULT 0,
            page_views INTEGER DEFAULT 0,
            total_time_spent INTEGER DEFAULT 0, -- minutes
            content_views INTEGER DEFAULT 0,
            assignment_views INTEGER DEFAULT 0,
            discussion_views INTEGER DEFAULT 0,
            quiz_views INTEGER DEFAULT 0,
            
            -- Activity measures
            posts_created INTEGER DEFAULT 0,
            replies_created INTEGER DEFAULT 0,
            files_uploaded INTEGER DEFAULT 0,
            files_downloaded INTEGER DEFAULT 0,
            
            -- Learning measures
            modules_completed INTEGER DEFAULT 0,
            videos_watched INTEGER DEFAULT 0,
            reading_completed INTEGER DEFAULT 0,
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
            FOREIGN KEY (course_key) REFERENCES dim_course(course_key),
            FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (instructor_key) REFERENCES dim_instructor(instructor_key)
        );
        
        CREATE INDEX IF NOT EXISTS idx_fact_course_eng_student ON fact_course_engagement(student_key);
        CREATE INDEX IF NOT EXISTS idx_fact_course_eng_course ON fact_course_engagement(course_key);
        CREATE INDEX IF NOT EXISTS idx_fact_course_eng_date ON fact_course_engagement(date_key);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _create_assignment_submission_fact(self, db: AsyncSession):
        """Create assignment submission fact table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS fact_assignment_submission (
            submission_key SERIAL PRIMARY KEY,
            student_key INTEGER NOT NULL,
            assignment_key INTEGER NOT NULL,
            course_key INTEGER NOT NULL,
            submission_date_key INTEGER NOT NULL,
            due_date_key INTEGER,
            instructor_key INTEGER,
            
            -- Submission measures
            submission_attempt INTEGER DEFAULT 1,
            is_late BOOLEAN DEFAULT FALSE,
            is_missing BOOLEAN DEFAULT FALSE,
            days_late INTEGER DEFAULT 0,
            
            -- Grade measures
            raw_score DECIMAL(10,2),
            points_earned DECIMAL(10,2),
            points_possible DECIMAL(10,2),
            grade_percentage DECIMAL(5,2),
            letter_grade VARCHAR(5),
            
            -- Effort measures
            word_count INTEGER,
            character_count INTEGER,
            file_count INTEGER DEFAULT 0,
            revision_count INTEGER DEFAULT 0,
            
            -- Time measures
            time_to_submit INTEGER, -- minutes from assignment creation
            time_spent INTEGER, -- minutes actively working
            
            -- Quality measures
            plagiarism_score DECIMAL(5,2),
            originality_score DECIMAL(5,2),
            readability_score DECIMAL(5,2),
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
            FOREIGN KEY (assignment_key) REFERENCES dim_assignment(assignment_key),
            FOREIGN KEY (course_key) REFERENCES dim_course(course_key),
            FOREIGN KEY (submission_date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (due_date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (instructor_key) REFERENCES dim_instructor(instructor_key)
        );
        
        CREATE INDEX IF NOT EXISTS idx_fact_assignment_sub_student ON fact_assignment_submission(student_key);
        CREATE INDEX IF NOT EXISTS idx_fact_assignment_sub_assignment ON fact_assignment_submission(assignment_key);
        CREATE INDEX IF NOT EXISTS idx_fact_assignment_sub_course ON fact_assignment_submission(course_key);
        CREATE INDEX IF NOT EXISTS idx_fact_assignment_sub_date ON fact_assignment_submission(submission_date_key);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _create_learning_outcome_fact(self, db: AsyncSession):
        """Create learning outcome fact table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS fact_learning_outcome (
            outcome_key SERIAL PRIMARY KEY,
            student_key INTEGER NOT NULL,
            course_key INTEGER NOT NULL,
            assignment_key INTEGER,
            date_key INTEGER NOT NULL,
            instructor_key INTEGER,
            
            -- Outcome measures
            outcome_id VARCHAR(50),
            outcome_name VARCHAR(255),
            mastery_level INTEGER, -- 1-4 scale
            points_earned DECIMAL(10,2),
            points_possible DECIMAL(10,2),
            mastery_percentage DECIMAL(5,2),
            
            -- Assessment measures
            assessment_type VARCHAR(50),
            attempts_count INTEGER DEFAULT 1,
            improvement_trend VARCHAR(20), -- improving, declining, stable
            
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
            FOREIGN KEY (course_key) REFERENCES dim_course(course_key),
            FOREIGN KEY (assignment_key) REFERENCES dim_assignment(assignment_key),
            FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (instructor_key) REFERENCES dim_instructor(instructor_key)
        );
        
        CREATE INDEX IF NOT EXISTS idx_fact_learning_outcome_student ON fact_learning_outcome(student_key);
        CREATE INDEX IF NOT EXISTS idx_fact_learning_outcome_course ON fact_learning_outcome(course_key);
        CREATE INDEX IF NOT EXISTS idx_fact_learning_outcome_outcome ON fact_learning_outcome(outcome_id);
        """
        
        await db.execute(text(create_table_sql))


class DataMartETLService:
    """Main ETL service for data mart creation and maintenance."""
    
    def __init__(self):
        self.dimension_manager = DimensionManager()
        self.fact_manager = FactTableManager()
        self.sync_crud = CanvasSyncCRUD()
        self.data_lineage: List[DataLineage] = []
    
    async def initialize_data_marts(self):
        """Initialize all data mart structures."""
        async with AsyncSessionLocal() as db:
            try:
                logger.info("Initializing data mart structures...")
                
                # Create dimension tables
                await self.dimension_manager.create_dimension_tables(db)
                
                # Create fact tables
                await self.fact_manager.create_fact_tables(db)
                
                # Create data lineage tracking table
                await self._create_lineage_table(db)
                
                # Create ETL job tracking table
                await self._create_etl_job_table(db)
                
                await db.commit()
                logger.info("Data mart structures initialized successfully")
                
            except Exception as e:
                logger.error(f"Error initializing data marts: {e}")
                await db.rollback()
                raise
    
    async def run_etl_pipeline(self, mart_type: Optional[DataMartType] = None) -> Dict[str, Any]:
        """Run the complete ETL pipeline."""
        start_time = datetime.utcnow()
        job_id = f"etl_{mart_type.value if mart_type else 'full'}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            async with AsyncSessionLocal() as db:
                # Log ETL job start
                await self._log_etl_job(db, job_id, ETLStatus.RUNNING, mart_type)
                
                results = {
                    "job_id": job_id,
                    "start_time": start_time.isoformat(),
                    "marts_processed": [],
                    "records_processed": 0,
                    "errors": []
                }
                
                # Determine which marts to process
                if mart_type:
                    marts_to_process = [mart_type]
                else:
                    marts_to_process = list(DataMartType)
                
                # Process each mart; on error, propagate to fail the job
                for mart in marts_to_process:
                    mart_result = await self._process_data_mart(db, mart)
                    # If a mart returns failed status, raise to fail the pipeline
                    if mart_result.get("status") == "failed":
                        error_message = mart_result.get("error", f"Mart {mart.value} failed")
                        logger.error(f"Error processing mart {mart.value}: {error_message}")
                        raise Exception(error_message)

                    results["marts_processed"].append(mart_result)
                    results["records_processed"] += mart_result.get("records_processed", 0)
                
                # Calculate duration
                end_time = datetime.utcnow()
                results["end_time"] = end_time.isoformat()
                results["duration_seconds"] = (end_time - start_time).total_seconds()
                
                # Update job status
                status = ETLStatus.COMPLETED if not results["errors"] else ETLStatus.FAILED
                await self._log_etl_job(db, job_id, status, mart_type, results)
                
                await db.commit()
                
                logger.info(f"ETL pipeline completed: {len(results['marts_processed'])} marts, {results['records_processed']} records")
                return results
                
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            async with AsyncSessionLocal() as db:
                await self._log_etl_job(db, job_id, ETLStatus.FAILED, mart_type, {"error": str(e)})
                await db.commit()
            raise
    
    async def _process_data_mart(self, db: AsyncSession, mart_type: DataMartType) -> Dict[str, Any]:
        """Process a specific data mart."""
        logger.info(f"Processing data mart: {mart_type.value}")
        
        if mart_type == DataMartType.STUDENT_PERFORMANCE:
            return await self._process_student_performance_mart(db)
        elif mart_type == DataMartType.COURSE_ANALYTICS:
            return await self._process_course_analytics_mart(db)
        elif mart_type == DataMartType.ASSIGNMENT_METRICS:
            return await self._process_assignment_metrics_mart(db)
        elif mart_type == DataMartType.ENGAGEMENT_TRENDS:
            return await self._process_engagement_trends_mart(db)
        elif mart_type == DataMartType.LEARNING_OUTCOMES:
            return await self._process_learning_outcomes_mart(db)
        else:
            raise ValueError(f"Unknown mart type: {mart_type}")
    
    async def _process_student_performance_mart(self, db: AsyncSession) -> Dict[str, Any]:
        """Process student performance data mart."""
        logger.info("Processing student performance mart...")
        
        # This is a simplified example - in production, you would:
        # 1. Extract data from Canvas raw tables
        # 2. Transform according to business rules
        # 3. Load into fact table with proper dimension keys
        
        # Example transformation logic
        transform_sql = """
        INSERT INTO fact_student_performance (
            student_key, course_key, assignment_key, date_key,
            grade_points, points_earned, points_possible, grade_percentage,
            submission_count, late_submission_count
        )
        SELECT 
            ds.student_key,
            dc.course_key,
            da.assignment_key,
            dd.date_key,
            g.grade_points,
            g.points_earned,
            g.points_possible,
            CASE 
                WHEN g.points_possible > 0 THEN (g.points_earned / g.points_possible) * 100
                ELSE NULL 
            END as grade_percentage,
            1 as submission_count,
            CASE WHEN s.submitted_at > a.due_date THEN 1 ELSE 0 END as late_submission_count
        FROM grades g
        JOIN submissions s ON g.submission_id = s.id
        JOIN assignments a ON s.assignment_id = a.id
        JOIN dim_student ds ON s.student_id = ds.student_id
        JOIN dim_course dc ON a.course_id = dc.course_id
        JOIN dim_assignment da ON a.id = da.assignment_id
        JOIN dim_date dd ON DATE(g.created_at) = dd.date_actual
        WHERE g.created_at >= NOW() - INTERVAL '7 days'
        ON CONFLICT (student_key, course_key, assignment_key, date_key) 
        DO UPDATE SET
            grade_points = EXCLUDED.grade_points,
            points_earned = EXCLUDED.points_earned,
            points_possible = EXCLUDED.points_possible,
            grade_percentage = EXCLUDED.grade_percentage,
            updated_at = NOW()
        """
        
        try:
            result = await db.execute(text(transform_sql))
            records_processed = result.rowcount if result.rowcount else 0
            
            # Track data lineage
            lineage = DataLineage(
                source_system="Canvas LMS",
                source_table="grades, submissions, assignments",
                source_columns=["grade_points", "points_earned", "points_possible", "submitted_at"],
                target_table="fact_student_performance",
                target_columns=["grade_points", "points_earned", "points_possible", "grade_percentage"],
                transformation_logic="Grade percentage calculation and late submission detection",
                created_at=datetime.utcnow(),
                created_by="ETL Service"
            )
            
            await self._track_data_lineage(db, lineage)
            
            return {
                "mart_type": DataMartType.STUDENT_PERFORMANCE.value,
                "status": "completed",
                "records_processed": records_processed,
                "lineage_tracked": True
            }
            
        except Exception as e:
            logger.error(f"Error processing student performance mart: {e}")
            return {
                "mart_type": DataMartType.STUDENT_PERFORMANCE.value,
                "status": "failed",
                "error": str(e),
                "records_processed": 0
            }
    
    async def _process_course_analytics_mart(self, db: AsyncSession) -> Dict[str, Any]:
        """Process course analytics data mart."""
        logger.info("Processing course analytics mart...")
        
        # Placeholder implementation
        return {
            "mart_type": DataMartType.COURSE_ANALYTICS.value,
            "status": "completed",
            "records_processed": 0,
            "note": "Placeholder implementation"
        }
    
    async def _process_assignment_metrics_mart(self, db: AsyncSession) -> Dict[str, Any]:
        """Process assignment metrics data mart."""
        logger.info("Processing assignment metrics mart...")
        
        # Placeholder implementation
        return {
            "mart_type": DataMartType.ASSIGNMENT_METRICS.value,
            "status": "completed",
            "records_processed": 0,
            "note": "Placeholder implementation"
        }
    
    async def _process_engagement_trends_mart(self, db: AsyncSession) -> Dict[str, Any]:
        """Process engagement trends data mart."""
        logger.info("Processing engagement trends mart...")
        
        # Placeholder implementation
        return {
            "mart_type": DataMartType.ENGAGEMENT_TRENDS.value,
            "status": "completed",
            "records_processed": 0,
            "note": "Placeholder implementation"
        }
    
    async def _process_learning_outcomes_mart(self, db: AsyncSession) -> Dict[str, Any]:
        """Process learning outcomes data mart."""
        logger.info("Processing learning outcomes mart...")
        
        # Placeholder implementation
        return {
            "mart_type": DataMartType.LEARNING_OUTCOMES.value,
            "status": "completed",
            "records_processed": 0,
            "note": "Placeholder implementation"
        }
    
    async def _create_lineage_table(self, db: AsyncSession):
        """Create data lineage tracking table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS data_lineage (
            lineage_id SERIAL PRIMARY KEY,
            source_system VARCHAR(100) NOT NULL,
            source_table VARCHAR(100) NOT NULL,
            source_columns TEXT[],
            target_table VARCHAR(100) NOT NULL,
            target_columns TEXT[],
            transformation_logic TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_by VARCHAR(100) NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_data_lineage_source ON data_lineage(source_table);
        CREATE INDEX IF NOT EXISTS idx_data_lineage_target ON data_lineage(target_table);
        CREATE INDEX IF NOT EXISTS idx_data_lineage_created ON data_lineage(created_at);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _create_etl_job_table(self, db: AsyncSession):
        """Create ETL job tracking table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS etl_jobs (
            job_id VARCHAR(100) PRIMARY KEY,
            mart_type VARCHAR(50),
            status VARCHAR(20) NOT NULL,
            start_time TIMESTAMP WITH TIME ZONE,
            end_time TIMESTAMP WITH TIME ZONE,
            duration_seconds DECIMAL(10,2),
            records_processed INTEGER DEFAULT 0,
            job_details JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON etl_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_etl_jobs_mart_type ON etl_jobs(mart_type);
        CREATE INDEX IF NOT EXISTS idx_etl_jobs_start_time ON etl_jobs(start_time);
        """
        
        await db.execute(text(create_table_sql))
    
    async def _track_data_lineage(self, db: AsyncSession, lineage: DataLineage):
        """Track data lineage information."""
        insert_sql = """
        INSERT INTO data_lineage (
            source_system, source_table, source_columns, target_table,
            target_columns, transformation_logic, created_at, created_by
        ) VALUES (
            :source_system, :source_table, :source_columns, :target_table,
            :target_columns, :transformation_logic, :created_at, :created_by
        )
        """
        
        await db.execute(text(insert_sql), {
            "source_system": lineage.source_system,
            "source_table": lineage.source_table,
            "source_columns": lineage.source_columns,
            "target_table": lineage.target_table,
            "target_columns": lineage.target_columns,
            "transformation_logic": lineage.transformation_logic,
            "created_at": lineage.created_at,
            "created_by": lineage.created_by
        })
    
    async def _log_etl_job(
        self, 
        db: AsyncSession, 
        job_id: str, 
        status: ETLStatus, 
        mart_type: Optional[DataMartType] = None,
        job_details: Optional[Dict[str, Any]] = None
    ):
        """Log ETL job status."""
        upsert_sql = """
        INSERT INTO etl_jobs (job_id, mart_type, status, job_details, start_time)
        VALUES (:job_id, :mart_type, :status, :job_details, :start_time)
        ON CONFLICT (job_id) DO UPDATE SET
            status = EXCLUDED.status,
            job_details = EXCLUDED.job_details,
            end_time = CASE WHEN EXCLUDED.status IN ('completed', 'failed') THEN NOW() ELSE etl_jobs.end_time END,
            updated_at = NOW()
        """
        
        await db.execute(text(upsert_sql), {
            "job_id": job_id,
            "mart_type": mart_type.value if mart_type else None,
            "status": status.value,
            "job_details": json.dumps(job_details) if job_details else None,
            "start_time": datetime.utcnow() if status == ETLStatus.RUNNING else None
        })
    
    async def get_etl_status(self) -> Dict[str, Any]:
        """Get ETL pipeline status."""
        async with AsyncSessionLocal() as db:
            # Get recent ETL jobs
            jobs_sql = """
            SELECT job_id, mart_type, status, start_time, end_time, 
                   duration_seconds, records_processed
            FROM etl_jobs 
            ORDER BY start_time DESC 
            LIMIT 10
            """
            
            result = await db.execute(text(jobs_sql))
            recent_jobs = [dict(row._mapping) for row in result.fetchall()]
            
            # Get data mart sizes
            mart_sizes = {}
            
            fact_tables = [
                "fact_student_performance",
                "fact_course_engagement", 
                "fact_assignment_submission",
                "fact_learning_outcome"
            ]
            
            for table in fact_tables:
                try:
                    count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    mart_sizes[table] = count
                except:
                    mart_sizes[table] = 0
            
            return {
                "recent_jobs": recent_jobs,
                "mart_sizes": mart_sizes,
                "status": "active",
                "last_update": datetime.utcnow().isoformat()
            }


# Global ETL service instance
data_mart_etl = DataMartETLService()
