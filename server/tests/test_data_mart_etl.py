"""Tests for data mart ETL service."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date

from app.services.data_mart_etl import (
    DataMartETLService,
    DimensionManager,
    FactTableManager,
    DataMartType,
    ETLStatus,
    MigrationRisk,
    ETLJobConfig,
    DataLineage
)


@pytest.fixture
def etl_service():
    """Create an ETL service instance for testing."""
    return DataMartETLService()


@pytest.fixture
def dimension_manager():
    """Create a dimension manager instance for testing."""
    return DimensionManager()


@pytest.fixture
def fact_manager():
    """Create a fact table manager instance for testing."""
    return FactTableManager()


class TestDimensionManager:
    """Test dimension manager functionality."""
    
    @pytest.mark.asyncio
    async def test_create_dimension_tables(self, dimension_manager):
        """Test dimension table creation."""
        mock_db = AsyncMock()
        
        with patch.object(dimension_manager, '_create_date_dimension') as mock_date:
            with patch.object(dimension_manager, '_create_student_dimension') as mock_student:
                with patch.object(dimension_manager, '_create_course_dimension') as mock_course:
                    with patch.object(dimension_manager, '_create_assignment_dimension') as mock_assignment:
                        with patch.object(dimension_manager, '_create_instructor_dimension') as mock_instructor:
                            await dimension_manager.create_dimension_tables(mock_db)
                            
                            mock_date.assert_called_once_with(mock_db)
                            mock_student.assert_called_once_with(mock_db)
                            mock_course.assert_called_once_with(mock_db)
                            mock_assignment.assert_called_once_with(mock_db)
                            mock_instructor.assert_called_once_with(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_date_dimension(self, dimension_manager):
        """Test date dimension creation."""
        mock_db = AsyncMock()
        
        with patch.object(dimension_manager, '_populate_date_dimension') as mock_populate:
            await dimension_manager._create_date_dimension(mock_db)
            
            mock_db.execute.assert_called_once()
            mock_populate.assert_called_once_with(mock_db)
    
    @pytest.mark.asyncio
    async def test_populate_date_dimension_existing_data(self, dimension_manager):
        """Test date dimension population when data already exists."""
        mock_db = AsyncMock()
        mock_db.scalar.return_value = 100  # Existing records
        
        await dimension_manager._populate_date_dimension(mock_db)
        
        # Should check for existing data and skip population
        mock_db.scalar.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_populate_date_dimension_new_data(self, dimension_manager):
        """Test date dimension population with new data."""
        mock_db = AsyncMock()
        mock_db.scalar.return_value = 0  # No existing records
        
        with patch.object(dimension_manager, '_insert_date_batch') as mock_insert:
            await dimension_manager._populate_date_dimension(mock_db)
            
            # Should call insert batch multiple times
            assert mock_insert.call_count > 0
    
    @pytest.mark.asyncio
    async def test_insert_date_batch(self, dimension_manager):
        """Test date batch insertion."""
        mock_db = AsyncMock()
        dates_batch = [
            {
                'date_key': 20240101,
                'date_actual': date(2024, 1, 1),
                'year': 2024,
                'month': 1,
                'day': 1
            }
        ]
        
        await dimension_manager._insert_date_batch(mock_db, dates_batch)
        
        mock_db.execute.assert_called_once()


class TestFactTableManager:
    """Test fact table manager functionality."""
    
    @pytest.mark.asyncio
    async def test_create_fact_tables(self, fact_manager):
        """Test fact table creation."""
        mock_db = AsyncMock()
        
        with patch.object(fact_manager, '_create_student_performance_fact') as mock_performance:
            with patch.object(fact_manager, '_create_course_engagement_fact') as mock_engagement:
                with patch.object(fact_manager, '_create_assignment_submission_fact') as mock_submission:
                    with patch.object(fact_manager, '_create_learning_outcome_fact') as mock_outcome:
                        await fact_manager.create_fact_tables(mock_db)
                        
                        mock_performance.assert_called_once_with(mock_db)
                        mock_engagement.assert_called_once_with(mock_db)
                        mock_submission.assert_called_once_with(mock_db)
                        mock_outcome.assert_called_once_with(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_student_performance_fact(self, fact_manager):
        """Test student performance fact table creation."""
        mock_db = AsyncMock()
        
        await fact_manager._create_student_performance_fact(mock_db)
        
        mock_db.execute.assert_called_once()
        
        # Check that the SQL contains expected table name and columns
        call_args = mock_db.execute.call_args[0][0]
        assert "fact_student_performance" in str(call_args)
        assert "student_key" in str(call_args)
        assert "course_key" in str(call_args)


class TestDataMartETLService:
    """Test main ETL service functionality."""
    
    @pytest.mark.asyncio
    async def test_initialize_data_marts(self, etl_service):
        """Test data mart initialization."""
        with patch('app.services.data_mart_etl.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            with patch.object(etl_service.dimension_manager, 'create_dimension_tables') as mock_dim:
                with patch.object(etl_service.fact_manager, 'create_fact_tables') as mock_fact:
                    with patch.object(etl_service, '_create_lineage_table') as mock_lineage:
                        with patch.object(etl_service, '_create_etl_job_table') as mock_job:
                            await etl_service.initialize_data_marts()
                            
                            mock_dim.assert_called_once_with(mock_db)
                            mock_fact.assert_called_once_with(mock_db)
                            mock_lineage.assert_called_once_with(mock_db)
                            mock_job.assert_called_once_with(mock_db)
                            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_etl_pipeline_single_mart(self, etl_service):
        """Test running ETL pipeline for single mart."""
        with patch('app.services.data_mart_etl.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            with patch.object(etl_service, '_log_etl_job') as mock_log:
                with patch.object(etl_service, '_process_data_mart') as mock_process:
                    mock_process.return_value = {
                        "mart_type": "student_performance",
                        "status": "completed",
                        "records_processed": 100
                    }
                    
                    result = await etl_service.run_etl_pipeline(DataMartType.STUDENT_PERFORMANCE)
                    
                    assert result["marts_processed"]
                    assert result["records_processed"] == 100
                    assert len(result["errors"]) == 0
                    mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_etl_pipeline_all_marts(self, etl_service):
        """Test running ETL pipeline for all marts."""
        with patch('app.services.data_mart_etl.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            with patch.object(etl_service, '_log_etl_job') as mock_log:
                with patch.object(etl_service, '_process_data_mart') as mock_process:
                    mock_process.return_value = {
                        "mart_type": "test",
                        "status": "completed",
                        "records_processed": 50
                    }
                    
                    result = await etl_service.run_etl_pipeline()
                    
                    # Should process all mart types
                    assert len(result["marts_processed"]) == len(DataMartType)
                    assert mock_process.call_count == len(DataMartType)
    
    @pytest.mark.asyncio
    async def test_process_student_performance_mart(self, etl_service):
        """Test processing student performance mart."""
        mock_db = AsyncMock()
        mock_db.execute.return_value.rowcount = 150
        
        with patch.object(etl_service, '_track_data_lineage') as mock_lineage:
            result = await etl_service._process_student_performance_mart(mock_db)
            
            assert result["mart_type"] == DataMartType.STUDENT_PERFORMANCE.value
            assert result["status"] == "completed"
            assert result["records_processed"] == 150
            assert result["lineage_tracked"] is True
            mock_lineage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_data_mart_unknown_type(self, etl_service):
        """Test processing unknown mart type."""
        mock_db = AsyncMock()
        
        # Create a mock enum value that doesn't exist
        class UnknownMartType:
            value = "unknown_mart"
        
        unknown_mart = UnknownMartType()
        
        with pytest.raises(ValueError, match="Unknown mart type"):
            await etl_service._process_data_mart(mock_db, unknown_mart)
    
    @pytest.mark.asyncio
    async def test_track_data_lineage(self, etl_service):
        """Test data lineage tracking."""
        mock_db = AsyncMock()
        
        lineage = DataLineage(
            source_system="Canvas LMS",
            source_table="grades",
            source_columns=["grade_points", "points_earned"],
            target_table="fact_student_performance",
            target_columns=["grade_points", "points_earned"],
            transformation_logic="Direct copy with percentage calculation",
            created_at=datetime.utcnow(),
            created_by="ETL Service"
        )
        
        await etl_service._track_data_lineage(mock_db, lineage)
        
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert "data_lineage" in str(call_args[0][0])
    
    @pytest.mark.asyncio
    async def test_log_etl_job(self, etl_service):
        """Test ETL job logging."""
        mock_db = AsyncMock()
        
        await etl_service._log_etl_job(
            mock_db,
            "test_job_123",
            ETLStatus.RUNNING,
            DataMartType.STUDENT_PERFORMANCE,
            {"test": "data"}
        )
        
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert "etl_jobs" in str(call_args[0][0])
    
    @pytest.mark.asyncio
    async def test_get_etl_status(self, etl_service):
        """Test getting ETL status."""
        with patch('app.services.data_mart_etl.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock recent jobs query
            mock_result = Mock()
            mock_result.fetchall.return_value = [
                Mock(_mapping={
                    "job_id": "job_1",
                    "mart_type": "student_performance",
                    "status": "completed",
                    "start_time": datetime.utcnow(),
                    "end_time": datetime.utcnow(),
                    "duration_seconds": 45.5,
                    "records_processed": 100
                })
            ]
            
            # Mock table count queries
            mock_db.execute.side_effect = [
                mock_result,  # Recent jobs query
                Mock(scalar=Mock(return_value=1000)),  # fact_student_performance count
                Mock(scalar=Mock(return_value=500)),   # fact_course_engagement count
                Mock(scalar=Mock(return_value=2000)),  # fact_assignment_submission count
                Mock(scalar=Mock(return_value=150))    # fact_learning_outcome count
            ]
            
            status = await etl_service.get_etl_status()
            
            assert "recent_jobs" in status
            assert "mart_sizes" in status
            assert "status" in status
            assert "last_update" in status
            assert status["status"] == "active"
            assert len(status["recent_jobs"]) == 1


class TestETLDataClasses:
    """Test ETL data classes and enums."""
    
    def test_etl_job_config(self):
        """Test ETL job configuration dataclass."""
        config = ETLJobConfig(
            mart_type=DataMartType.STUDENT_PERFORMANCE,
            source_tables=["grades", "submissions"],
            target_table="fact_student_performance",
            schedule="0 2 * * *",  # Daily at 2 AM
            retention_days=90,
            data_quality_checks=["not_null", "referential_integrity"],
            dependencies=["dim_student", "dim_course"]
        )
        
        assert config.mart_type == DataMartType.STUDENT_PERFORMANCE
        assert config.source_tables == ["grades", "submissions"]
        assert config.target_table == "fact_student_performance"
        assert config.schedule == "0 2 * * *"
        assert config.retention_days == 90
        assert "not_null" in config.data_quality_checks
        assert "dim_student" in config.dependencies
    
    def test_data_lineage(self):
        """Test data lineage dataclass."""
        now = datetime.utcnow()
        
        lineage = DataLineage(
            source_system="Canvas LMS",
            source_table="assignments",
            source_columns=["id", "name", "points_possible"],
            target_table="dim_assignment",
            target_columns=["assignment_id", "assignment_name", "points_possible"],
            transformation_logic="Direct mapping with ID transformation",
            created_at=now,
            created_by="ETL Service"
        )
        
        assert lineage.source_system == "Canvas LMS"
        assert lineage.source_table == "assignments"
        assert lineage.target_table == "dim_assignment"
        assert lineage.transformation_logic == "Direct mapping with ID transformation"
        assert lineage.created_at == now
        assert lineage.created_by == "ETL Service"
    
    def test_data_mart_type_enum(self):
        """Test DataMartType enum values."""
        assert DataMartType.STUDENT_PERFORMANCE.value == "student_performance"
        assert DataMartType.COURSE_ANALYTICS.value == "course_analytics"
        assert DataMartType.ASSIGNMENT_METRICS.value == "assignment_metrics"
        assert DataMartType.ENGAGEMENT_TRENDS.value == "engagement_trends"
        assert DataMartType.LEARNING_OUTCOMES.value == "learning_outcomes"
    
    def test_etl_status_enum(self):
        """Test ETLStatus enum values."""
        assert ETLStatus.PENDING.value == "pending"
        assert ETLStatus.RUNNING.value == "running"
        assert ETLStatus.COMPLETED.value == "completed"
        assert ETLStatus.FAILED.value == "failed"
        assert ETLStatus.CANCELLED.value == "cancelled"


class TestETLIntegration:
    """Integration tests for ETL functionality."""
    
    @pytest.mark.asyncio
    async def test_full_etl_workflow(self, etl_service):
        """Test complete ETL workflow."""
        # Test initialization -> processing -> status check
        
        with patch('app.services.data_mart_etl.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock all required methods
            with patch.object(etl_service.dimension_manager, 'create_dimension_tables'):
                with patch.object(etl_service.fact_manager, 'create_fact_tables'):
                    with patch.object(etl_service, '_create_lineage_table'):
                        with patch.object(etl_service, '_create_etl_job_table'):
                            # Initialize
                            await etl_service.initialize_data_marts()
                            
                            # Run ETL
                            with patch.object(etl_service, '_process_data_mart') as mock_process:
                                mock_process.return_value = {
                                    "mart_type": "student_performance",
                                    "status": "completed",
                                    "records_processed": 100
                                }
                                
                                result = await etl_service.run_etl_pipeline(DataMartType.STUDENT_PERFORMANCE)
                                
                                assert result["marts_processed"]
                                assert result["records_processed"] == 100
    
    @pytest.mark.asyncio
    async def test_etl_error_handling(self, etl_service):
        """Test ETL error handling."""
        with patch('app.services.data_mart_etl.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            
            # Mock database error
            mock_db.execute.side_effect = Exception("Database connection failed")
            
            with patch.object(etl_service, '_log_etl_job') as mock_log:
                with pytest.raises(Exception, match="Database connection failed"):
                    await etl_service.run_etl_pipeline(DataMartType.STUDENT_PERFORMANCE)
                
                # Should log the failure
                mock_log.assert_called()


# Performance tests
class TestETLPerformance:
    """Performance tests for ETL operations."""
    
    @pytest.mark.benchmark
    def test_date_dimension_generation_performance(self, dimension_manager, benchmark):
        """Benchmark date dimension generation performance."""
        def generate_date_records():
            records = []
            for i in range(365):  # One year of dates
                date_obj = date(2024, 1, 1)
                records.append({
                    'date_key': int(date_obj.strftime("%Y%m%d")),
                    'date_actual': date_obj,
                    'year': date_obj.year,
                    'month': date_obj.month
                })
            return records
        
        result = benchmark(generate_date_records)
        assert len(result) == 365
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_lineage_tracking_performance(self, etl_service, benchmark):
        """Benchmark lineage tracking performance."""
        mock_db = AsyncMock()
        
        lineage = DataLineage(
            source_system="Canvas LMS",
            source_table="grades",
            source_columns=["grade_points"],
            target_table="fact_student_performance",
            target_columns=["grade_points"],
            transformation_logic="Direct copy",
            created_at=datetime.utcnow(),
            created_by="ETL Service"
        )
        
        async def track_lineage():
            await etl_service._track_data_lineage(mock_db, lineage)
        
        await benchmark(track_lineage)
