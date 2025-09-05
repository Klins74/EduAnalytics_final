"""
ML Inference Service for making predictions with deployed models.

Handles model loading, prediction serving, and drift monitoring.
"""

import logging
import pickle
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_model import MLModel, MLPrediction
from app.crud.ml_model import MLModelCRUD, MLPredictionCRUD
from app.services.ml_training_service import MLFeatureExtractor
from app.db.session import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelCache:
    """Cache for loaded ML models to avoid repeated disk reads."""
    
    def __init__(self, cache_size: int = 5):
        self.cache_size = cache_size
        self.models = {}  # model_id -> (model_artifacts, loaded_at)
        self.access_times = {}  # model_id -> last_access_time
    
    def get(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Get model from cache."""
        if model_id in self.models:
            self.access_times[model_id] = datetime.utcnow()
            return self.models[model_id][0]
        return None
    
    def put(self, model_id: int, model_artifacts: Dict[str, Any]):
        """Put model in cache, evicting old models if necessary."""
        # Evict least recently used models if cache is full
        if len(self.models) >= self.cache_size:
            lru_model_id = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.models[lru_model_id]
            del self.access_times[lru_model_id]
        
        self.models[model_id] = (model_artifacts, datetime.utcnow())
        self.access_times[model_id] = datetime.utcnow()
    
    def clear(self):
        """Clear the cache."""
        self.models.clear()
        self.access_times.clear()


class DriftMonitor:
    """Monitor model performance and feature drift."""
    
    def __init__(self):
        self.prediction_crud = MLPredictionCRUD()
    
    async def calculate_feature_drift(
        self,
        db: AsyncSession,
        model_id: int,
        current_features: Dict[str, float],
        window_days: int = 30
    ) -> float:
        """Calculate feature drift score compared to recent predictions."""
        try:
            # Get recent predictions for this model
            cutoff_date = datetime.utcnow() - timedelta(days=window_days)
            recent_predictions = await self.prediction_crud.list_predictions(
                db, model_id=model_id, limit=1000
            )
            
            # Filter by date
            recent_predictions = [
                p for p in recent_predictions 
                if p.predicted_at >= cutoff_date
            ]
            
            if len(recent_predictions) < 10:
                return 0.0  # Not enough data for drift calculation
            
            # Extract feature values from recent predictions
            historical_features = []
            for pred in recent_predictions:
                features = pred.input_features
                if isinstance(features, dict):
                    historical_features.append(features)
            
            if not historical_features:
                return 0.0
            
            # Calculate drift using simple statistical measures
            drift_scores = []
            for feature_name, current_value in current_features.items():
                historical_values = [
                    hf.get(feature_name) for hf in historical_features
                    if feature_name in hf and hf[feature_name] is not None
                ]
                
                if historical_values:
                    historical_mean = np.mean(historical_values)
                    historical_std = np.std(historical_values)
                    
                    if historical_std > 0:
                        # Normalized difference from historical mean
                        drift_score = abs(current_value - historical_mean) / historical_std
                        drift_scores.append(drift_score)
            
            # Return average drift score
            return np.mean(drift_scores) if drift_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating feature drift: {e}")
            return 0.0
    
    async def calculate_performance_drift(
        self,
        db: AsyncSession,
        model_id: int,
        window_days: int = 30
    ) -> Dict[str, float]:
        """Calculate model performance drift."""
        try:
            # Get recent predictions with actual outcomes
            cutoff_date = datetime.utcnow() - timedelta(days=window_days)
            recent_predictions = await self.prediction_crud.list_predictions(
                db, model_id=model_id, limit=1000
            )
            
            # Filter by date and availability of actual outcomes
            validated_predictions = [
                p for p in recent_predictions 
                if (p.predicted_at >= cutoff_date and 
                    p.actual_outcome is not None and 
                    p.is_correct is not None)
            ]
            
            if len(validated_predictions) < 5:
                return {"accuracy": 0.0, "sample_size": 0}
            
            # Calculate accuracy
            correct_predictions = sum(1 for p in validated_predictions if p.is_correct)
            accuracy = correct_predictions / len(validated_predictions)
            
            return {
                "accuracy": accuracy,
                "sample_size": len(validated_predictions),
                "total_predictions": len(recent_predictions)
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance drift: {e}")
            return {"accuracy": 0.0, "sample_size": 0}


class MLInferenceService:
    """Service for ML model inference and prediction serving."""
    
    def __init__(self):
        self.ml_crud = MLModelCRUD()
        self.prediction_crud = MLPredictionCRUD()
        self.feature_extractor = MLFeatureExtractor()
        self.model_cache = ModelCache()
        self.drift_monitor = DriftMonitor()
        self.models_dir = Path(settings.UPLOAD_DIRECTORY) / "ml_models"
    
    async def load_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Load a model from cache or disk."""
        try:
            # Check cache first
            cached_model = self.model_cache.get(model_id)
            if cached_model:
                return cached_model
            
            # Load from database
            async with AsyncSessionLocal() as db:
                model = await self.ml_crud.get_model(db, model_id)
                if not model or not model.model_path:
                    return None
                
                # Load model artifacts from disk
                model_path = Path(model.model_path)
                if not model_path.exists():
                    logger.error(f"Model file not found: {model_path}")
                    return None
                
                with open(model_path, 'rb') as f:
                    model_artifacts = pickle.load(f)
                
                # Cache the model
                self.model_cache.put(model_id, model_artifacts)
                
                return model_artifacts
                
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return None
    
    async def predict_student_performance(
        self,
        student_id: int,
        course_id: int,
        model_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Predict student performance using the active or specified model."""
        try:
            async with AsyncSessionLocal() as db:
                # Get model to use
                if model_id:
                    model = await self.ml_crud.get_model(db, model_id)
                else:
                    model = await self.ml_crud.get_active_model(db, "performance_predictor")
                
                if not model:
                    logger.error("No active performance prediction model found")
                    return None
                
                # Load model artifacts
                model_artifacts = await self.load_model(model.id)
                if not model_artifacts:
                    logger.error(f"Failed to load model {model.id}")
                    return None
                
                # Extract features for the student
                features = await self.feature_extractor.extract_student_features(
                    db, student_id, course_id
                )
                
                if not features:
                    logger.error(f"Failed to extract features for student {student_id}")
                    return None
                
                # Prepare features for prediction
                feature_columns = model_artifacts['feature_columns']
                X = []
                for col in feature_columns:
                    value = features.get(col, 0.0)
                    X.append(value)
                
                X = np.array(X).reshape(1, -1)
                
                # Apply scaling if needed
                if 'scaler' in model_artifacts and model_artifacts['scaler']:
                    X = model_artifacts['scaler'].transform(X)
                
                # Make prediction
                ml_model = model_artifacts['model']
                prediction = ml_model.predict(X)[0]
                
                # Get prediction probabilities if available
                prediction_proba = None
                if hasattr(ml_model, 'predict_proba'):
                    probabilities = ml_model.predict_proba(X)[0]
                    prediction_proba = {
                        "low_performance": float(probabilities[0]),
                        "high_performance": float(probabilities[1])
                    }
                
                # Calculate confidence score
                confidence_score = 0.5  # Default
                if prediction_proba:
                    confidence_score = max(prediction_proba.values())
                
                # Monitor drift
                feature_dict = dict(zip(feature_columns, X[0]))
                drift_score = await self.drift_monitor.calculate_feature_drift(
                    db, model.id, feature_dict
                )
                
                # Create prediction record
                prediction_id = str(uuid.uuid4())
                prediction_record = await self.prediction_crud.create_prediction(
                    db,
                    {
                        "model_id": model.id,
                        "prediction_id": prediction_id,
                        "input_features": features,
                        "context": {
                            "student_id": student_id,
                            "course_id": course_id
                        },
                        "prediction": {
                            "performance_level": "high" if prediction == 1 else "low",
                            "raw_prediction": int(prediction)
                        },
                        "confidence_score": confidence_score,
                        "prediction_probabilities": prediction_proba,
                        "prediction_type": "performance"
                    }
                )
                
                # Prepare response
                result = {
                    "prediction_id": prediction_id,
                    "student_id": student_id,
                    "course_id": course_id,
                    "prediction": {
                        "performance_level": "high" if prediction == 1 else "low",
                        "confidence": confidence_score,
                        "probabilities": prediction_proba
                    },
                    "model_info": {
                        "model_id": model.id,
                        "model_name": model.name,
                        "model_version": model.version,
                        "model_type": model.model_type
                    },
                    "features_used": len(feature_columns),
                    "drift_score": drift_score,
                    "predicted_at": datetime.utcnow().isoformat()
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Error predicting student performance: {e}")
            return None
    
    async def batch_predict(
        self,
        course_id: int,
        student_ids: Optional[List[int]] = None,
        model_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run batch predictions for multiple students."""
        try:
            async with AsyncSessionLocal() as db:
                # Get students to predict for
                if student_ids is None:
                    # Get all students in the course
                    from app.models.enrollment import Enrollment
                    from sqlalchemy import and_
                    
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
                    student_ids = [e.user_id for e in enrollments]
                
                if not student_ids:
                    return {"error": "No students found for prediction"}
                
                # Run predictions for each student
                batch_id = str(uuid.uuid4())
                predictions = []
                successful_predictions = 0
                failed_predictions = 0
                
                for student_id in student_ids:
                    try:
                        result = await self.predict_student_performance(
                            student_id, course_id, model_id
                        )
                        
                        if result:
                            result["batch_id"] = batch_id
                            predictions.append(result)
                            successful_predictions += 1
                        else:
                            failed_predictions += 1
                            
                    except Exception as e:
                        logger.error(f"Error predicting for student {student_id}: {e}")
                        failed_predictions += 1
                
                # Aggregate results
                summary = {
                    "high_performers": len([p for p in predictions if p["prediction"]["performance_level"] == "high"]),
                    "low_performers": len([p for p in predictions if p["prediction"]["performance_level"] == "low"]),
                    "avg_confidence": np.mean([p["prediction"]["confidence"] for p in predictions]) if predictions else 0.0,
                    "successful_predictions": successful_predictions,
                    "failed_predictions": failed_predictions
                }
                
                return {
                    "batch_id": batch_id,
                    "course_id": course_id,
                    "predictions": predictions,
                    "summary": summary,
                    "processing_time": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in batch prediction: {e}")
            return {"error": str(e)}
    
    async def get_model_performance_stats(self, model_id: int) -> Dict[str, Any]:
        """Get performance statistics for a model."""
        try:
            async with AsyncSessionLocal() as db:
                # Get basic model info
                model = await self.ml_crud.get_model(db, model_id)
                if not model:
                    return {"error": "Model not found"}
                
                # Get performance drift
                performance_drift = await self.drift_monitor.calculate_performance_drift(
                    db, model_id
                )
                
                # Get prediction volume
                total_predictions = await self.prediction_crud.list_predictions(
                    db, model_id=model_id, limit=10000
                )
                
                # Recent predictions (last 7 days)
                recent_cutoff = datetime.utcnow() - timedelta(days=7)
                recent_predictions = [
                    p for p in total_predictions 
                    if p.predicted_at >= recent_cutoff
                ]
                
                stats = {
                    "model_info": {
                        "id": model.id,
                        "name": model.name,
                        "version": model.version,
                        "type": model.model_type,
                        "status": model.status,
                        "is_active": model.is_active
                    },
                    "training_metrics": model.metrics or {},
                    "performance_drift": performance_drift,
                    "prediction_volume": {
                        "total_predictions": len(total_predictions),
                        "recent_predictions": len(recent_predictions),
                        "avg_daily_predictions": len(recent_predictions) / 7 if recent_predictions else 0
                    },
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting model performance stats: {e}")
            return {"error": str(e)}


# Global inference service instance
ml_inference_service = MLInferenceService()
