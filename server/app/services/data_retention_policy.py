"""
Data Retention and Privacy Policy Management.

Implements GDPR-compliant data retention, anonymization, and deletion policies.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import json
import hashlib
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, and_, or_, text
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.submission import Submission
from app.models.grade import Grade
from app.models.notification_log import NotificationLog
from app.models.ml_model import MLPrediction
from app.core.config import settings

logger = logging.getLogger(__name__)


class RetentionPeriod(Enum):
    """Data retention periods."""
    IMMEDIATE = 0
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_180 = 180
    YEAR_1 = 365
    YEARS_2 = 730
    YEARS_5 = 1825
    YEARS_7 = 2555  # Legal requirement in many jurisdictions
    PERMANENT = -1


class DataCategory(Enum):
    """Categories of data for retention policies."""
    PERSONAL_IDENTIFIABLE = "pii"
    ACADEMIC_RECORDS = "academic"
    SYSTEM_LOGS = "logs"
    ANALYTICS_DATA = "analytics"
    COMMUNICATION = "communication"
    ML_PREDICTIONS = "ml_predictions"
    AUDIT_TRAILS = "audit"
    TEMPORARY_FILES = "temp_files"


class AnonymizationLevel(Enum):
    """Levels of data anonymization."""
    NONE = "none"
    PSEUDONYMIZE = "pseudonymize"  # Replace with consistent pseudonyms
    HASH = "hash"  # One-way hash
    REMOVE = "remove"  # Remove completely
    AGGREGATE = "aggregate"  # Convert to aggregated statistics


@dataclass
class RetentionRule:
    """Data retention rule definition."""
    data_category: DataCategory
    retention_period: RetentionPeriod
    anonymization_level: AnonymizationLevel
    conditions: Optional[Dict[str, Any]] = None
    exceptions: Optional[List[str]] = None


@dataclass
class PIIField:
    """Personally Identifiable Information field definition."""
    table_name: str
    column_name: str
    field_type: str  # email, name, phone, etc.
    anonymization_method: AnonymizationLevel
    is_required: bool = False


class DataRetentionPolicyManager:
    """Manager for data retention and privacy policies."""
    
    def __init__(self):
        self.retention_rules = self._load_retention_rules()
        self.pii_fields = self._define_pii_fields()
        self.pseudonym_cache = {}  # For consistent pseudonymization
    
    def _load_retention_rules(self) -> List[RetentionRule]:
        """Load data retention rules."""
        return [
            # Personal data - GDPR compliant
            RetentionRule(
                data_category=DataCategory.PERSONAL_IDENTIFIABLE,
                retention_period=RetentionPeriod.YEARS_7,
                anonymization_level=AnonymizationLevel.PSEUDONYMIZE,
                conditions={"user_status": "inactive"}
            ),
            
            # Academic records - typically kept longer
            RetentionRule(
                data_category=DataCategory.ACADEMIC_RECORDS,
                retention_period=RetentionPeriod.YEARS_7,
                anonymization_level=AnonymizationLevel.PSEUDONYMIZE,
                conditions={"academic_year_ended": True}
            ),
            
            # System logs - shorter retention
            RetentionRule(
                data_category=DataCategory.SYSTEM_LOGS,
                retention_period=RetentionPeriod.DAYS_90,
                anonymization_level=AnonymizationLevel.HASH
            ),
            
            # Analytics data - aggregated after period
            RetentionRule(
                data_category=DataCategory.ANALYTICS_DATA,
                retention_period=RetentionPeriod.YEAR_1,
                anonymization_level=AnonymizationLevel.AGGREGATE
            ),
            
            # ML predictions - pseudonymized
            RetentionRule(
                data_category=DataCategory.ML_PREDICTIONS,
                retention_period=RetentionPeriod.YEARS_2,
                anonymization_level=AnonymizationLevel.PSEUDONYMIZE
            ),
            
            # Communication logs
            RetentionRule(
                data_category=DataCategory.COMMUNICATION,
                retention_period=RetentionPeriod.YEAR_1,
                anonymization_level=AnonymizationLevel.HASH
            ),
            
            # Audit trails - kept longer for compliance
            RetentionRule(
                data_category=DataCategory.AUDIT_TRAILS,
                retention_period=RetentionPeriod.YEARS_7,
                anonymization_level=AnonymizationLevel.PSEUDONYMIZE
            ),
            
            # Temporary files - short retention
            RetentionRule(
                data_category=DataCategory.TEMPORARY_FILES,
                retention_period=RetentionPeriod.DAYS_30,
                anonymization_level=AnonymizationLevel.REMOVE
            )
        ]
    
    def _define_pii_fields(self) -> List[PIIField]:
        """Define PII fields across the application."""
        return [
            # User table
            PIIField("users", "email", "email", AnonymizationLevel.HASH),
            PIIField("users", "username", "username", AnonymizationLevel.PSEUDONYMIZE),
            PIIField("users", "first_name", "name", AnonymizationLevel.PSEUDONYMIZE),
            PIIField("users", "last_name", "name", AnonymizationLevel.PSEUDONYMIZE),
            PIIField("users", "phone", "phone", AnonymizationLevel.HASH),
            PIIField("users", "address", "address", AnonymizationLevel.REMOVE),
            
            # Notification logs
            PIIField("notification_logs", "recipient", "contact", AnonymizationLevel.HASH),
            PIIField("notification_logs", "message_content", "content", AnonymizationLevel.REMOVE),
            
            # Submissions (may contain PII in files)
            PIIField("submissions", "file_path", "file_reference", AnonymizationLevel.HASH),
            PIIField("submissions", "original_filename", "filename", AnonymizationLevel.PSEUDONYMIZE),
            
            # ML predictions context
            PIIField("ml_predictions", "context", "ml_context", AnonymizationLevel.PSEUDONYMIZE)
        ]
    
    def _generate_pseudonym(self, original_value: str, field_type: str) -> str:
        """Generate consistent pseudonym for a value."""
        # Create a hash key for consistency
        hash_key = f"{field_type}:{original_value}"
        
        if hash_key in self.pseudonym_cache:
            return self.pseudonym_cache[hash_key]
        
        # Generate pseudonym based on field type
        hash_obj = hashlib.sha256(hash_key.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        
        if field_type == "email":
            pseudonym = f"user_{hash_hex}@anonymized.local"
        elif field_type == "name":
            pseudonym = f"User_{hash_hex}"
        elif field_type == "username":
            pseudonym = f"user_{hash_hex}"
        elif field_type == "phone":
            pseudonym = f"+1-555-{hash_hex[:4]}"
        elif field_type == "filename":
            pseudonym = f"file_{hash_hex}.dat"
        else:
            pseudonym = f"anon_{hash_hex}"
        
        self.pseudonym_cache[hash_key] = pseudonym
        return pseudonym
    
    def _anonymize_value(self, value: str, field: PIIField) -> Optional[str]:
        """Anonymize a single value according to the field's anonymization method."""
        if not value:
            return value
        
        if field.anonymization_level == AnonymizationLevel.NONE:
            return value
        elif field.anonymization_level == AnonymizationLevel.REMOVE:
            return None
        elif field.anonymization_level == AnonymizationLevel.HASH:
            # One-way hash
            return hashlib.sha256(value.encode()).hexdigest()[:16]
        elif field.anonymization_level == AnonymizationLevel.PSEUDONYMIZE:
            return self._generate_pseudonym(value, field.field_type)
        elif field.anonymization_level == AnonymizationLevel.AGGREGATE:
            # For aggregation, this would be handled at the query level
            return "[AGGREGATED]"
        
        return value
    
    async def apply_retention_policy(self, dry_run: bool = True) -> Dict[str, Any]:
        """Apply data retention policies across all data categories."""
        results = {
            "dry_run": dry_run,
            "processed_categories": [],
            "total_records_affected": 0,
            "errors": [],
            "started_at": datetime.utcnow().isoformat()
        }
        
        async with AsyncSessionLocal() as db:
            for rule in self.retention_rules:
                try:
                    category_result = await self._apply_category_retention(db, rule, dry_run)
                    results["processed_categories"].append(category_result)
                    results["total_records_affected"] += category_result.get("records_affected", 0)
                    
                except Exception as e:
                    error_info = {
                        "category": rule.data_category.value,
                        "error": str(e)
                    }
                    results["errors"].append(error_info)
                    logger.error(f"Error applying retention for {rule.data_category}: {e}")
            
            if not dry_run:
                await db.commit()
        
        results["completed_at"] = datetime.utcnow().isoformat()
        return results
    
    async def _apply_category_retention(
        self, 
        db: AsyncSession, 
        rule: RetentionRule, 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Apply retention policy for a specific data category."""
        if rule.retention_period == RetentionPeriod.PERMANENT:
            return {
                "category": rule.data_category.value,
                "action": "skipped",
                "reason": "permanent_retention",
                "records_affected": 0
            }
        
        cutoff_date = datetime.utcnow() - timedelta(days=rule.retention_period.value)
        
        if rule.data_category == DataCategory.SYSTEM_LOGS:
            return await self._clean_system_logs(db, cutoff_date, rule, dry_run)
        elif rule.data_category == DataCategory.COMMUNICATION:
            return await self._clean_communication_logs(db, cutoff_date, rule, dry_run)
        elif rule.data_category == DataCategory.ML_PREDICTIONS:
            return await self._clean_ml_predictions(db, cutoff_date, rule, dry_run)
        elif rule.data_category == DataCategory.PERSONAL_IDENTIFIABLE:
            return await self._anonymize_pii_data(db, cutoff_date, rule, dry_run)
        elif rule.data_category == DataCategory.TEMPORARY_FILES:
            return await self._clean_temporary_files(db, cutoff_date, rule, dry_run)
        else:
            return {
                "category": rule.data_category.value,
                "action": "not_implemented",
                "records_affected": 0
            }
    
    async def _clean_system_logs(
        self, 
        db: AsyncSession, 
        cutoff_date: datetime, 
        rule: RetentionRule, 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean system logs older than cutoff date."""
        # This would clean application logs, audit logs, etc.
        # For now, we'll clean notification logs as an example
        
        query = select(NotificationLog).where(
            NotificationLog.created_at < cutoff_date
        )
        
        old_logs = await db.execute(query)
        logs_to_process = old_logs.scalars().all()
        
        records_affected = len(logs_to_process)
        
        if not dry_run and records_affected > 0:
            if rule.anonymization_level == AnonymizationLevel.REMOVE:
                # Delete old logs
                delete_query = delete(NotificationLog).where(
                    NotificationLog.created_at < cutoff_date
                )
                await db.execute(delete_query)
            else:
                # Anonymize logs
                for log in logs_to_process:
                    if log.recipient:
                        log.recipient = self._anonymize_value(
                            log.recipient, 
                            PIIField("notification_logs", "recipient", "contact", rule.anonymization_level)
                        )
                    if log.message_content:
                        log.message_content = "[REDACTED]"
        
        return {
            "category": rule.data_category.value,
            "action": "anonymized" if rule.anonymization_level != AnonymizationLevel.REMOVE else "deleted",
            "records_affected": records_affected,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    async def _clean_communication_logs(
        self, 
        db: AsyncSession, 
        cutoff_date: datetime, 
        rule: RetentionRule, 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean communication logs (emails, SMS, etc.)."""
        # Similar to system logs but specifically for communication
        return await self._clean_system_logs(db, cutoff_date, rule, dry_run)
    
    async def _clean_ml_predictions(
        self, 
        db: AsyncSession, 
        cutoff_date: datetime, 
        rule: RetentionRule, 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean old ML predictions."""
        query = select(MLPrediction).where(
            MLPrediction.predicted_at < cutoff_date
        )
        
        old_predictions = await db.execute(query)
        predictions_to_process = old_predictions.scalars().all()
        
        records_affected = len(predictions_to_process)
        
        if not dry_run and records_affected > 0:
            if rule.anonymization_level == AnonymizationLevel.REMOVE:
                delete_query = delete(MLPrediction).where(
                    MLPrediction.predicted_at < cutoff_date
                )
                await db.execute(delete_query)
            elif rule.anonymization_level == AnonymizationLevel.PSEUDONYMIZE:
                for prediction in predictions_to_process:
                    if prediction.context:
                        # Anonymize student/user references in context
                        context = prediction.context
                        if isinstance(context, dict):
                            if 'student_id' in context:
                                context['student_id'] = f"anon_student_{context['student_id'] % 1000}"
                            prediction.context = context
        
        return {
            "category": rule.data_category.value,
            "action": "processed",
            "records_affected": records_affected,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    async def _anonymize_pii_data(
        self, 
        db: AsyncSession, 
        cutoff_date: datetime, 
        rule: RetentionRule, 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Anonymize PII data for inactive users."""
        # Find users who have been inactive for the retention period
        query = select(User).where(
            and_(
                User.last_login < cutoff_date,
                User.is_active == False
            )
        )
        
        inactive_users = await db.execute(query)
        users_to_process = inactive_users.scalars().all()
        
        records_affected = len(users_to_process)
        
        if not dry_run and records_affected > 0:
            for user in users_to_process:
                # Anonymize PII fields
                pii_fields = [f for f in self.pii_fields if f.table_name == "users"]
                
                for field in pii_fields:
                    current_value = getattr(user, field.column_name, None)
                    if current_value:
                        anonymized_value = self._anonymize_value(current_value, field)
                        setattr(user, field.column_name, anonymized_value)
                
                # Mark as anonymized
                user.is_anonymized = True
        
        return {
            "category": rule.data_category.value,
            "action": "anonymized",
            "records_affected": records_affected,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    async def _clean_temporary_files(
        self, 
        db: AsyncSession, 
        cutoff_date: datetime, 
        rule: RetentionRule, 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Clean temporary files and uploads."""
        import os
        from pathlib import Path
        
        upload_dir = Path(settings.UPLOAD_DIRECTORY)
        temp_dir = upload_dir / "temp"
        
        files_removed = 0
        
        if temp_dir.exists() and not dry_run:
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        try:
                            file_path.unlink()
                            files_removed += 1
                        except Exception as e:
                            logger.error(f"Error removing temp file {file_path}: {e}")
        
        return {
            "category": rule.data_category.value,
            "action": "files_removed",
            "records_affected": files_removed,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    async def generate_privacy_report(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate a privacy and data retention report."""
        report = {
            "report_generated_at": datetime.utcnow().isoformat(),
            "retention_rules": [],
            "pii_fields": [],
            "data_summary": {},
            "user_specific": None
        }
        
        # Add retention rules info
        for rule in self.retention_rules:
            report["retention_rules"].append({
                "category": rule.data_category.value,
                "retention_days": rule.retention_period.value,
                "anonymization": rule.anonymization_level.value
            })
        
        # Add PII fields info
        for field in self.pii_fields:
            report["pii_fields"].append({
                "table": field.table_name,
                "column": field.column_name,
                "type": field.field_type,
                "anonymization": field.anonymization_method.value
            })
        
        # Generate data summary
        async with AsyncSessionLocal() as db:
            # Count various data types
            user_count = await db.scalar(select(func.count(User.id)))
            submission_count = await db.scalar(select(func.count(Submission.id)))
            prediction_count = await db.scalar(select(func.count(MLPrediction.id)))
            
            report["data_summary"] = {
                "total_users": user_count,
                "total_submissions": submission_count,
                "total_ml_predictions": prediction_count
            }
            
            # User-specific data if requested
            if user_id:
                user_data = await self._get_user_data_summary(db, user_id)
                report["user_specific"] = user_data
        
        return report
    
    async def _get_user_data_summary(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Get data summary for a specific user."""
        user = await db.get(User, user_id)
        if not user:
            return {"error": "User not found"}
        
        # Count user's data
        user_submissions = await db.scalar(
            select(func.count(Submission.id)).where(Submission.student_id == user_id)
        )
        
        user_predictions = await db.scalar(
            select(func.count(MLPrediction.id)).where(
                MLPrediction.context.contains(json.dumps({"student_id": user_id}))
            )
        )
        
        return {
            "user_id": user_id,
            "username": user.username,
            "is_anonymized": getattr(user, 'is_anonymized', False),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "data_counts": {
                "submissions": user_submissions,
                "ml_predictions": user_predictions
            },
            "retention_applicable": not user.is_active and user.last_login and 
                                  user.last_login < datetime.utcnow() - timedelta(days=365)
        }


# Global data retention policy manager
data_retention_manager = DataRetentionPolicyManager()
