"""CRUD operations for ML models."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, update
from app.models.ml_model import MLModel, MLTrainingJob, MLPrediction


class MLModelCRUD:
    """CRUD operations for ML models."""
    
    async def create_model(self, db: AsyncSession, model_data: Dict[str, Any]) -> MLModel:
        """Create a new ML model."""
        model = MLModel(**model_data)
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model
    
    async def get_model(self, db: AsyncSession, model_id: int) -> Optional[MLModel]:
        """Get a model by ID."""
        result = await db.execute(select(MLModel).where(MLModel.id == model_id))
        return result.scalar_one_or_none()
    
    async def get_model_by_name_version(
        self, 
        db: AsyncSession, 
        name: str, 
        version: str
    ) -> Optional[MLModel]:
        """Get a model by name and version."""
        result = await db.execute(
            select(MLModel).where(
                and_(MLModel.name == name, MLModel.version == version)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_model(
        self, 
        db: AsyncSession, 
        model_type: str
    ) -> Optional[MLModel]:
        """Get the active model for a given type."""
        result = await db.execute(
            select(MLModel).where(
                and_(
                    MLModel.model_type == model_type,
                    MLModel.is_active == True,
                    MLModel.status == "deployed"
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_models(
        self, 
        db: AsyncSession, 
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[MLModel]:
        """List models with optional filtering."""
        query = select(MLModel).order_by(desc(MLModel.created_at)).limit(limit)
        
        if model_type:
            query = query.where(MLModel.model_type == model_type)
        
        if status:
            query = query.where(MLModel.status == status)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_model(
        self, 
        db: AsyncSession, 
        model_id: int, 
        updates: Dict[str, Any]
    ) -> Optional[MLModel]:
        """Update a model."""
        await db.execute(
            update(MLModel)
            .where(MLModel.id == model_id)
            .values(**updates)
        )
        await db.commit()
        return await self.get_model(db, model_id)
    
    async def delete_model(self, db: AsyncSession, model_id: int) -> bool:
        """Soft delete a model by archiving it."""
        model = await self.get_model(db, model_id)
        if not model:
            return False
        
        model.status = "archived"
        model.is_active = False
        await db.commit()
        return True


class MLTrainingJobCRUD:
    """CRUD operations for ML training jobs."""
    
    async def create_job(self, db: AsyncSession, job_data: Dict[str, Any]) -> MLTrainingJob:
        """Create a new training job."""
        job = MLTrainingJob(**job_data)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    
    async def get_job(self, db: AsyncSession, job_id: str) -> Optional[MLTrainingJob]:
        """Get a training job by ID."""
        result = await db.execute(
            select(MLTrainingJob).where(MLTrainingJob.job_id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def list_jobs(
        self, 
        db: AsyncSession, 
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> List[MLTrainingJob]:
        """List training jobs with optional filtering."""
        query = select(MLTrainingJob).order_by(desc(MLTrainingJob.created_at)).limit(limit)
        
        if status:
            query = query.where(MLTrainingJob.status == status)
        
        if user_id:
            query = query.where(MLTrainingJob.created_by == user_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_job(
        self, 
        db: AsyncSession, 
        job_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[MLTrainingJob]:
        """Update a training job."""
        await db.execute(
            update(MLTrainingJob)
            .where(MLTrainingJob.job_id == job_id)
            .values(**updates)
        )
        await db.commit()
        return await self.get_job(db, job_id)


class MLPredictionCRUD:
    """CRUD operations for ML predictions."""
    
    async def create_prediction(
        self, 
        db: AsyncSession, 
        prediction_data: Dict[str, Any]
    ) -> MLPrediction:
        """Create a new prediction record."""
        prediction = MLPrediction(**prediction_data)
        db.add(prediction)
        await db.commit()
        await db.refresh(prediction)
        return prediction
    
    async def get_prediction(
        self, 
        db: AsyncSession, 
        prediction_id: str
    ) -> Optional[MLPrediction]:
        """Get a prediction by ID."""
        result = await db.execute(
            select(MLPrediction).where(MLPrediction.prediction_id == prediction_id)
        )
        return result.scalar_one_or_none()
    
    async def list_predictions(
        self,
        db: AsyncSession,
        model_id: Optional[int] = None,
        prediction_type: Optional[str] = None,
        batch_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[MLPrediction]:
        """List predictions with optional filtering."""
        query = select(MLPrediction).order_by(desc(MLPrediction.predicted_at)).limit(limit)
        
        if model_id:
            query = query.where(MLPrediction.model_id == model_id)
        
        if prediction_type:
            query = query.where(MLPrediction.prediction_type == prediction_type)
        
        if batch_id:
            query = query.where(MLPrediction.batch_id == batch_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_prediction_outcome(
        self,
        db: AsyncSession,
        prediction_id: str,
        actual_outcome: Dict[str, Any],
        is_correct: Optional[bool] = None
    ) -> Optional[MLPrediction]:
        """Update a prediction with actual outcome."""
        prediction = await self.get_prediction(db, prediction_id)
        if not prediction:
            return None
        
        prediction.actual_outcome = actual_outcome
        prediction.is_correct = is_correct
        prediction.outcome_recorded_at = db.current_timestamp()
        
        await db.commit()
        await db.refresh(prediction)
        return prediction
