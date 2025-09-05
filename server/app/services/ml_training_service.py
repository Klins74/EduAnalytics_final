"""
ML Training Service for student performance prediction models.

Handles data preparation, model training, validation, and registry management.
"""

import logging
import uuid
import json
import asyncio
import pickle
import joblib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.ml_model import MLModel, MLTrainingJob, MLPrediction
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.grade import Grade
from app.models.enrollment import Enrollment
from app.crud.ml_model import MLModelCRUD
from app.db.session import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class MLFeatureExtractor:
    """Extract features for ML models from student data."""
    
    def __init__(self):
        self.ml_crud = MLModelCRUD()
    
    async def extract_student_features(
        self, 
        db: AsyncSession, 
        student_id: int, 
        course_id: Optional[int] = None,
        feature_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Extract features for a specific student."""
        if feature_date is None:
            feature_date = datetime.utcnow()
        
        features = {}
        
        try:
            # Student basic info
            student_result = await db.execute(
                select(User).where(User.id == student_id)
            )
            student = student_result.scalar_one_or_none()
            if not student:
                return features
            
            # Account age in days
            if student.created_at:
                features['account_age_days'] = (feature_date - student.created_at).days
            else:
                features['account_age_days'] = 0
            
            # Enrollment features
            enrollment_query = select(Enrollment).where(
                and_(
                    Enrollment.user_id == student_id,
                    Enrollment.status == 'active'
                )
            )
            if course_id:
                enrollment_query = enrollment_query.where(Enrollment.course_id == course_id)
            
            enrollments_result = await db.execute(enrollment_query)
            enrollments = enrollments_result.scalars().all()
            
            features['total_enrollments'] = len(enrollments)
            features['enrollment_roles'] = [e.role for e in enrollments]
            
            # Course-specific features
            if course_id:
                course_enrollment = next((e for e in enrollments if e.course_id == course_id), None)
                if course_enrollment:
                    features['enrollment_date'] = course_enrollment.created_at.isoformat() if course_enrollment.created_at else None
                    features['enrollment_role'] = course_enrollment.role
                    
                    # Days since enrollment
                    if course_enrollment.created_at:
                        features['days_since_enrollment'] = (feature_date - course_enrollment.created_at).days
                    else:
                        features['days_since_enrollment'] = 0
            
            # Assignment and submission features
            if course_id:
                # Get assignments for the course
                assignments_result = await db.execute(
                    select(Assignment).where(Assignment.course_id == course_id)
                )
                assignments = assignments_result.scalars().all()
                assignment_ids = [a.id for a in assignments]
                
                if assignment_ids:
                    # Get submissions for this student
                    submissions_result = await db.execute(
                        select(Submission).where(
                            and_(
                                Submission.student_id == student_id,
                                Submission.assignment_id.in_(assignment_ids),
                                Submission.created_at <= feature_date
                            )
                        )
                    )
                    submissions = submissions_result.scalars().all()
                    
                    features['total_submissions'] = len(submissions)
                    features['total_assignments'] = len(assignment_ids)
                    features['submission_rate'] = len(submissions) / len(assignment_ids) if assignment_ids else 0.0
                    
                    # Submission timing features
                    if submissions:
                        submission_times = []
                        for submission in submissions:
                            assignment = next((a for a in assignments if a.id == submission.assignment_id), None)
                            if assignment and assignment.due_date and submission.submitted_at:
                                time_diff = (submission.submitted_at - assignment.due_date).total_seconds() / 3600  # hours
                                submission_times.append(time_diff)
                        
                        if submission_times:
                            features['avg_submission_timing'] = np.mean(submission_times)  # Negative = early, positive = late
                            features['late_submissions'] = sum(1 for t in submission_times if t > 0)
                            features['early_submissions'] = sum(1 for t in submission_times if t < 0)
                    
                    # Grade features
                    grades_result = await db.execute(
                        select(Grade).where(
                            and_(
                                Grade.student_id == student_id,
                                Grade.assignment_id.in_(assignment_ids),
                                Grade.created_at <= feature_date
                            )
                        )
                    )
                    grades = grades_result.scalars().all()
                    
                    if grades:
                        grade_values = [g.points_earned for g in grades if g.points_earned is not None]
                        if grade_values:
                            features['avg_grade'] = np.mean(grade_values)
                            features['grade_std'] = np.std(grade_values)
                            features['min_grade'] = min(grade_values)
                            features['max_grade'] = max(grade_values)
                            features['total_graded'] = len(grade_values)
            
            # Activity patterns (simplified)
            features['feature_extraction_date'] = feature_date.isoformat()
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for student {student_id}: {e}")
            return {}
    
    async def extract_course_dataset(
        self, 
        db: AsyncSession, 
        course_id: int,
        cutoff_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Extract dataset for all students in a course."""
        if cutoff_date is None:
            cutoff_date = datetime.utcnow()
        
        try:
            # Get all enrolled students
            enrollments_result = await db.execute(
                select(Enrollment).where(
                    and_(
                        Enrollment.course_id == course_id,
                        Enrollment.status == 'active',
                        Enrollment.role == 'student'
                    )
                )
            )
            enrollments = enrollments_result.scalars().all()
            
            dataset = []
            for enrollment in enrollments:
                features = await self.extract_student_features(
                    db, enrollment.user_id, course_id, cutoff_date
                )
                features['student_id'] = enrollment.user_id
                features['course_id'] = course_id
                dataset.append(features)
            
            return pd.DataFrame(dataset)
            
        except Exception as e:
            logger.error(f"Error extracting course dataset for course {course_id}: {e}")
            return pd.DataFrame()


class MLTrainingService:
    """Service for training and managing ML models."""
    
    def __init__(self):
        self.feature_extractor = MLFeatureExtractor()
        self.ml_crud = MLModelCRUD()
        self.models_dir = Path(settings.UPLOAD_DIRECTORY) / "ml_models"
        self.models_dir.mkdir(exist_ok=True)
    
    async def start_training_job(
        self,
        model_name: str,
        model_type: str,
        config: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> str:
        """Start a new ML training job."""
        job_id = str(uuid.uuid4())
        
        try:
            async with AsyncSessionLocal() as db:
                # Create training job record
                training_job = MLTrainingJob(
                    job_id=job_id,
                    model_name=model_name,
                    model_version=f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    config=config,
                    status="queued",
                    created_by=user_id,
                    started_at=datetime.utcnow()
                )
                
                db.add(training_job)
                await db.commit()
            
            # Start training in background
            asyncio.create_task(self._run_training_job(job_id))
            
            logger.info(f"Started ML training job {job_id} for model {model_name}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error starting training job: {e}")
            raise
    
    async def _run_training_job(self, job_id: str):
        """Run the actual training job."""
        async with AsyncSessionLocal() as db:
            try:
                # Get job details
                job_result = await db.execute(
                    select(MLTrainingJob).where(MLTrainingJob.job_id == job_id)
                )
                job = job_result.scalar_one_or_none()
                if not job:
                    logger.error(f"Training job {job_id} not found")
                    return
                
                # Update status to running
                job.status = "running"
                job.progress_percent = 0.0
                job.current_step = "Preparing data"
                await db.commit()
                
                # Train the model based on type
                if job.config.get('model_type') == 'performance_predictor':
                    model_path, metrics = await self._train_performance_predictor(db, job)
                else:
                    raise ValueError(f"Unknown model type: {job.config.get('model_type')}")
                
                # Create model registry entry
                model = MLModel(
                    name=job.model_name,
                    version=job.model_version,
                    model_type=job.config.get('model_type'),
                    description=job.config.get('description'),
                    model_path=str(model_path),
                    config=job.config,
                    training_started_at=job.started_at,
                    training_completed_at=datetime.utcnow(),
                    training_duration_seconds=(datetime.utcnow() - job.started_at).total_seconds(),
                    validation_score=metrics.get('validation_score'),
                    test_score=metrics.get('test_score'),
                    metrics=metrics,
                    status="trained"
                )
                
                db.add(model)
                
                # Update job status
                job.status = "completed"
                job.progress_percent = 100.0
                job.current_step = "Training completed"
                job.completed_at = datetime.utcnow()
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
                job.result_metrics = metrics
                
                await db.commit()
                
                logger.info(f"Training job {job_id} completed successfully")
                
            except Exception as e:
                logger.error(f"Error in training job {job_id}: {e}")
                
                # Update job status to failed
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                if job.started_at:
                    job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
                
                await db.commit()
    
    async def _train_performance_predictor(
        self, 
        db: AsyncSession, 
        job: MLTrainingJob
    ) -> Tuple[Path, Dict[str, Any]]:
        """Train a student performance prediction model."""
        try:
            # Extract training data
            course_id = job.config.get('course_id')
            if not course_id:
                raise ValueError("course_id required for performance predictor")
            
            job.current_step = "Extracting features"
            job.progress_percent = 10.0
            await db.commit()
            
            # Get historical data
            cutoff_date = datetime.utcnow() - timedelta(days=30)  # Use data up to 30 days ago
            dataset = await self.feature_extractor.extract_course_dataset(
                db, course_id, cutoff_date
            )
            
            if dataset.empty or len(dataset) < 10:
                raise ValueError("Insufficient training data")
            
            job.current_step = "Preparing features"
            job.progress_percent = 30.0
            await db.commit()
            
            # Prepare features and target
            feature_columns = [
                'account_age_days', 'total_enrollments', 'days_since_enrollment',
                'total_submissions', 'submission_rate', 'avg_submission_timing',
                'late_submissions', 'early_submissions', 'total_graded'
            ]
            
            # Filter to available columns
            available_columns = [col for col in feature_columns if col in dataset.columns]
            if not available_columns:
                raise ValueError("No valid feature columns found")
            
            X = dataset[available_columns].fillna(0)
            
            # Create target variable (simplified: above/below average grade)
            if 'avg_grade' in dataset.columns:
                y = (dataset['avg_grade'] > dataset['avg_grade'].median()).astype(int)
            else:
                # Fallback: predict high engagement based on submission rate
                y = (dataset['submission_rate'] > 0.7).astype(int)
            
            job.current_step = "Training model"
            job.progress_percent = 50.0
            await db.commit()
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            model_type = job.config.get('algorithm', 'random_forest')
            
            if model_type == 'random_forest':
                model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            elif model_type == 'logistic_regression':
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)
                model = LogisticRegression(random_state=42)
            else:
                raise ValueError(f"Unknown algorithm: {model_type}")
            
            model.fit(X_train, y_train)
            
            job.current_step = "Evaluating model"
            job.progress_percent = 80.0
            await db.commit()
            
            # Evaluate model
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
            
            metrics = {
                'test_accuracy': accuracy_score(y_test, y_pred),
                'test_precision': precision_score(y_test, y_pred, average='weighted'),
                'test_recall': recall_score(y_test, y_pred, average='weighted'),
                'test_f1': f1_score(y_test, y_pred, average='weighted'),
                'feature_columns': available_columns,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'algorithm': model_type,
                'test_score': accuracy_score(y_test, y_pred),
                'validation_score': cross_val_score(model, X_train, y_train, cv=5).mean()
            }
            
            # Feature importance (if available)
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(available_columns, model.feature_importances_))
                metrics['feature_importance'] = feature_importance
            
            job.current_step = "Saving model"
            job.progress_percent = 90.0
            await db.commit()
            
            # Save model
            model_filename = f"{job.model_name}_{job.model_version}.pkl"
            model_path = self.models_dir / model_filename
            
            model_artifacts = {
                'model': model,
                'feature_columns': available_columns,
                'metrics': metrics,
                'scaler': scaler if model_type == 'logistic_regression' else None
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_artifacts, f)
            
            return model_path, metrics
            
        except Exception as e:
            logger.error(f"Error training performance predictor: {e}")
            raise
    
    async def get_training_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a training job."""
        try:
            async with AsyncSessionLocal() as db:
                job_result = await db.execute(
                    select(MLTrainingJob).where(MLTrainingJob.job_id == job_id)
                )
                job = job_result.scalar_one_or_none()
                
                if not job:
                    return None
                
                return {
                    'job_id': job.job_id,
                    'model_name': job.model_name,
                    'model_version': job.model_version,
                    'status': job.status,
                    'progress_percent': job.progress_percent,
                    'current_step': job.current_step,
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'duration_seconds': job.duration_seconds,
                    'result_metrics': job.result_metrics,
                    'error_message': job.error_message
                }
                
        except Exception as e:
            logger.error(f"Error getting training job status: {e}")
            return None
    
    async def list_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered models."""
        try:
            async with AsyncSessionLocal() as db:
                query = select(MLModel).order_by(desc(MLModel.created_at))
                
                if model_type:
                    query = query.where(MLModel.model_type == model_type)
                
                models_result = await db.execute(query)
                models = models_result.scalars().all()
                
                return [
                    {
                        'id': model.id,
                        'name': model.name,
                        'version': model.version,
                        'model_type': model.model_type,
                        'description': model.description,
                        'status': model.status,
                        'is_active': model.is_active,
                        'validation_score': model.validation_score,
                        'test_score': model.test_score,
                        'created_at': model.created_at.isoformat() if model.created_at else None,
                        'training_duration_seconds': model.training_duration_seconds
                    }
                    for model in models
                ]
                
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def deploy_model(self, model_id: int) -> bool:
        """Deploy a model to production."""
        try:
            async with AsyncSessionLocal() as db:
                # Get the model
                model_result = await db.execute(
                    select(MLModel).where(MLModel.id == model_id)
                )
                model = model_result.scalar_one_or_none()
                
                if not model:
                    return False
                
                # Deactivate other models of the same type
                await db.execute(
                    select(MLModel).where(
                        and_(
                            MLModel.model_type == model.model_type,
                            MLModel.is_active == True
                        )
                    ).update({'is_active': False})
                )
                
                # Activate this model
                model.is_active = True
                model.status = "deployed"
                
                await db.commit()
                
                logger.info(f"Deployed model {model.name} v{model.version}")
                return True
                
        except Exception as e:
            logger.error(f"Error deploying model {model_id}: {e}")
            return False


# Global training service instance
ml_training_service = MLTrainingService()
