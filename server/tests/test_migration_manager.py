"""Tests for migration manager service."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.migration_manager import (
    MigrationManager,
    DatabaseBackupManager,
    MigrationAnalyzer,
    MigrationStatus,
    MigrationRisk,
    MigrationInfo,
    MigrationResult
)


@pytest.fixture
def migration_manager():
    """Create a migration manager instance for testing."""
    return MigrationManager()


@pytest.fixture
def backup_manager():
    """Create a backup manager instance for testing."""
    return DatabaseBackupManager()


@pytest.fixture
def migration_analyzer():
    """Create a migration analyzer instance for testing."""
    return MigrationAnalyzer()


class TestMigrationAnalyzer:
    """Test migration analyzer functionality."""
    
    def test_assess_risk_critical(self, migration_analyzer):
        """Test critical risk assessment."""
        content = "DROP TABLE users; TRUNCATE assignments;"
        risk = migration_analyzer._assess_risk(content)
        assert risk == MigrationRisk.CRITICAL
    
    def test_assess_risk_medium(self, migration_analyzer):
        """Test medium risk assessment."""
        content = "ALTER TABLE users ADD COLUMN email VARCHAR(255) NOT NULL;"
        risk = migration_analyzer._assess_risk(content)
        assert risk == MigrationRisk.MEDIUM
    
    def test_assess_risk_low(self, migration_analyzer):
        """Test low risk assessment."""
        content = "CREATE INDEX idx_users_email ON users(email);"
        risk = migration_analyzer._assess_risk(content)
        assert risk == MigrationRisk.LOW
    
    def test_estimate_duration(self, migration_analyzer):
        """Test duration estimation."""
        content = """
        op.create_table('test_table',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False)
        )
        op.create_index('idx_test_name', 'test_table', ['name'])
        """
        duration = migration_analyzer._estimate_duration(content)
        assert duration > 10  # Should be more than base duration
        assert duration <= 300  # Should be capped at 5 minutes
    
    @patch('app.services.migration_manager.ScriptDirectory')
    @patch('app.services.migration_manager.Config')
    def test_analyze_migration(self, mock_config, mock_script_dir, migration_analyzer):
        """Test migration analysis."""
        # Mock revision
        mock_revision = Mock()
        mock_revision.revision = "abc123"
        mock_revision.doc = "Test migration"
        mock_revision.down_revision = "xyz789"
        mock_revision.branch_labels = None
        mock_revision.depends_on = None
        mock_revision.path = "/fake/path/abc123_test.py"
        
        # Mock script directory
        mock_script_dir.from_config.return_value.get_revision.return_value = mock_revision
        
        # Mock file content
        with patch('pathlib.Path.read_text', return_value="def upgrade():\n    pass\n\ndef downgrade():\n    op.drop_table('test')"):
            result = migration_analyzer.analyze_migration("abc123")
            
            assert isinstance(result, MigrationInfo)
            assert result.revision_id == "abc123"
            assert result.description == "Test migration"
            assert result.down_revision == "xyz789"
            assert result.rollback_available is True


class TestDatabaseBackupManager:
    """Test database backup manager functionality."""
    
    def test_init(self, backup_manager):
        """Test backup manager initialization."""
        assert backup_manager.backup_dir.exists()
    
    def test_list_backups_empty(self, backup_manager):
        """Test listing backups when none exist."""
        backups = backup_manager.list_backups()
        assert isinstance(backups, list)
    
    @patch('shutil.copy2')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.services.migration_manager.settings')
    async def test_create_backup_sqlite(self, mock_settings, mock_exists, mock_copy, backup_manager):
        """Test creating SQLite backup."""
        mock_settings.DATABASE_URL = "sqlite+aiosqlite:///test.db"
        
        backup_path = await backup_manager.create_backup("test_revision")
        
        assert backup_path is not None
        assert "backup_test_revision_" in backup_path
        mock_copy.assert_called_once()
    
    @patch('asyncio.create_subprocess_exec')
    @patch('app.services.migration_manager.settings')
    async def test_create_backup_postgresql(self, mock_settings, mock_subprocess, backup_manager):
        """Test creating PostgreSQL backup."""
        mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        
        # Mock successful subprocess
        mock_process = Mock()
        mock_process.communicate.return_value = asyncio.coroutine(lambda: (b"Success", b""))()
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process
        
        backup_path = await backup_manager.create_backup("test_revision")
        
        assert backup_path is not None
        assert "backup_test_revision_" in backup_path
        mock_subprocess.assert_called_once()


class TestMigrationManager:
    """Test migration manager functionality."""
    
    @pytest.mark.asyncio
    async def test_get_migration_status(self, migration_manager):
        """Test getting migration status."""
        with patch('app.services.migration_manager.create_async_engine') as mock_engine:
            # Mock database connection
            mock_connection = AsyncMock()
            mock_engine.return_value.__aenter__.return_value.connect.return_value.__aenter__.return_value = mock_connection
            mock_connection.run_sync.return_value = "abc123"
            
            # Mock script directory
            with patch('app.services.migration_manager.ScriptDirectory') as mock_script_dir:
                mock_script_dir.from_config.return_value.walk_revisions.return_value = []
                
                status = await migration_manager.get_migration_status()
                
                assert "current_revision" in status
                assert "pending_migrations" in status
                assert "total_pending" in status
                assert "high_risk_count" in status
                assert "backup_available" in status
    
    @pytest.mark.asyncio
    async def test_dry_run_migration_success(self, migration_manager):
        """Test successful dry run migration."""
        with patch.object(migration_manager, '_create_temp_database', return_value="temp://test"):
            with patch.object(migration_manager, '_copy_schema_to_temp'):
                with patch.object(migration_manager, '_create_temp_alembic_config'):
                    with patch.object(migration_manager, '_cleanup_temp_database'):
                        with patch('app.services.migration_manager.command.upgrade'):
                            result = await migration_manager.dry_run_migration("head")
                            
                            assert result["success"] is True
                            assert result["target_revision"] == "head"
                            assert "message" in result
    
    @pytest.mark.asyncio
    async def test_upgrade_with_safety_no_pending(self, migration_manager):
        """Test upgrade when no pending migrations exist."""
        with patch.object(migration_manager, 'get_migration_status', return_value={"pending_migrations": []}):
            result = await migration_manager.upgrade_with_safety()
            
            assert result.success is True
            assert result.message == "No pending migrations"
            assert result.duration == 0
    
    @pytest.mark.asyncio
    async def test_upgrade_with_safety_high_risk_no_force(self, migration_manager):
        """Test upgrade with high-risk migrations without force flag."""
        status = {
            "pending_migrations": [
                {"revision_id": "abc123", "risk_level": "critical", "backup_required": True}
            ]
        }
        
        with patch.object(migration_manager, 'get_migration_status', return_value=status):
            result = await migration_manager.upgrade_with_safety(force=False)
            
            assert result.success is False
            assert "High-risk migrations detected" in result.message
    
    @pytest.mark.asyncio
    async def test_rollback_migration_success(self, migration_manager):
        """Test successful migration rollback."""
        with patch.object(migration_manager.backup_manager, 'create_backup', return_value="/fake/backup"):
            with patch('app.services.migration_manager.command.downgrade'):
                result = await migration_manager.rollback_migration("abc123")
                
                assert result.success is True
                assert result.revision_id == "abc123"
                assert result.operation == "rollback"
                assert result.backup_path == "/fake/backup"
    
    @pytest.mark.asyncio
    async def test_temp_database_postgresql(self, migration_manager):
        """Test temporary database creation for PostgreSQL."""
        with patch('app.services.migration_manager.settings') as mock_settings:
            mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
            
            with patch('app.services.migration_manager.create_engine') as mock_create_engine:
                mock_engine = Mock()
                mock_connection = Mock()
                mock_engine.connect.return_value.__enter__.return_value = mock_connection
                mock_create_engine.return_value = mock_engine
                
                temp_url = await migration_manager._create_temp_database()
                
                assert "postgresql+asyncpg://" in temp_url
                assert "temp_migration_" in temp_url
                mock_connection.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_temp_database_sqlite(self, migration_manager):
        """Test temporary database creation for SQLite."""
        with patch('app.services.migration_manager.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite+aiosqlite:///test.db"
            
            temp_url = await migration_manager._create_temp_database()
            
            assert "sqlite+aiosqlite://" in temp_url
            assert "temp_migration_" in temp_url
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_database_postgresql(self, migration_manager):
        """Test temporary database cleanup for PostgreSQL."""
        temp_url = "postgresql+asyncpg://user:pass@localhost:5432/temp_migration_test"
        
        with patch('app.services.migration_manager.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_connection = Mock()
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            mock_create_engine.return_value = mock_engine
            
            await migration_manager._cleanup_temp_database(temp_url)
            
            # Should call terminate connections and drop database
            assert mock_connection.execute.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_database_sqlite(self, migration_manager):
        """Test temporary database cleanup for SQLite."""
        temp_url = "sqlite+aiosqlite:///temp_migration_test.db"
        
        with patch('pathlib.Path.unlink') as mock_unlink:
            await migration_manager._cleanup_temp_database(temp_url)
            mock_unlink.assert_called_once()


class TestMigrationIntegration:
    """Integration tests for migration functionality."""
    
    @pytest.mark.asyncio
    async def test_full_migration_workflow(self, migration_manager):
        """Test complete migration workflow."""
        # Test the full workflow: status -> dry run -> backup -> upgrade
        
        # Mock status check
        status = {
            "pending_migrations": [
                {
                    "revision_id": "abc123",
                    "risk_level": "low",
                    "backup_required": False,
                    "rollback_available": True
                }
            ]
        }
        
        with patch.object(migration_manager, 'get_migration_status', return_value=status):
            with patch.object(migration_manager, 'dry_run_migration', return_value={"success": True}):
                with patch('app.services.migration_manager.command.upgrade'):
                    result = await migration_manager.upgrade_with_safety(
                        target_revision="abc123",
                        create_backup=False,
                        force=True
                    )
                    
                    assert result.success is True
                    assert result.revision_id == "abc123"
                    assert result.operation == "upgrade"
    
    def test_migration_result_dataclass(self):
        """Test MigrationResult dataclass."""
        result = MigrationResult(
            success=True,
            revision_id="abc123",
            operation="upgrade",
            duration=45.5,
            message="Migration completed",
            backup_path="/backup/file",
            error=None,
            dry_run=False
        )
        
        assert result.success is True
        assert result.revision_id == "abc123"
        assert result.operation == "upgrade"
        assert result.duration == 45.5
        assert result.message == "Migration completed"
        assert result.backup_path == "/backup/file"
        assert result.error is None
        assert result.dry_run is False
    
    def test_migration_info_dataclass(self):
        """Test MigrationInfo dataclass."""
        info = MigrationInfo(
            revision_id="abc123",
            description="Test migration",
            down_revision="xyz789",
            branch_labels=None,
            depends_on=None,
            status=MigrationStatus.PENDING,
            risk_level=MigrationRisk.LOW,
            estimated_duration=30,
            backup_required=False,
            rollback_available=True
        )
        
        assert info.revision_id == "abc123"
        assert info.description == "Test migration"
        assert info.status == MigrationStatus.PENDING
        assert info.risk_level == MigrationRisk.LOW
        assert info.estimated_duration == 30
        assert info.backup_required is False
        assert info.rollback_available is True


# Performance tests
class TestMigrationPerformance:
    """Performance tests for migration operations."""
    
    @pytest.mark.benchmark
    def test_risk_assessment_performance(self, migration_analyzer, benchmark):
        """Benchmark risk assessment performance."""
        large_migration_content = """
        def upgrade():
            # Large migration with many operations
        """ + "\n".join([f"    op.add_column('table_{i}', sa.Column('col_{i}', sa.String(255)))" for i in range(100)])
        
        result = benchmark(migration_analyzer._assess_risk, large_migration_content)
        assert isinstance(result, MigrationRisk)
    
    @pytest.mark.benchmark
    def test_duration_estimation_performance(self, migration_analyzer, benchmark):
        """Benchmark duration estimation performance."""
        large_migration_content = """
        def upgrade():
            # Large migration with many operations
        """ + "\n".join([f"    op.create_index('idx_{i}', 'table_{i}', ['col_{i}'])" for i in range(50)])
        
        result = benchmark(migration_analyzer._estimate_duration, large_migration_content)
        assert isinstance(result, int)
