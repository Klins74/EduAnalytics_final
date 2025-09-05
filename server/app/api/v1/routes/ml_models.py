"""API routes for ML model management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.ml_training_service import ml_training_service
from app.services.ml_inference_service import ml_inference_service
from app.db.session import get_async_session

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


class TrainingJobRequest(BaseModel):
    model_name: str
    model_type: str
    description: Optional[str] = None
    course_id: Optional[int] = None
    algorithm: Optional[str] = "random_forest"
    hyperparameters: Optional[Dict[str, Any]] = None


class TrainingJobResponse(BaseModel):
    job_id: str
    message: str


class ModelListResponse(BaseModel):
    models: List[Dict[str, Any]]
    total: int


class JobStatusResponse(BaseModel):
    job_details: Dict[str, Any]


@router.post("/train", response_model=TrainingJobResponse, summary="Start ML model training")
async def start_model_training(
    request: TrainingJobRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> TrainingJobResponse:
    """Start training a new ML model."""
    try:
        # Prepare training configuration
        config = {
            "model_type": request.model_type,
            "description": request.description,
            "course_id": request.course_id,
            "algorithm": request.algorithm,
            "hyperparameters": request.hyperparameters or {},
            "created_by": current_user.id
        }
        
        # Validate model type
        valid_types = ["performance_predictor", "risk_classifier", "engagement_predictor"]
        if request.model_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model type. Must be one of: {valid_types}"
            )
        
        # Start training job
        job_id = await ml_training_service.start_training_job(
            model_name=request.model_name,
            model_type=request.model_type,
            config=config,
            user_id=current_user.id
        )
        
        return TrainingJobResponse(
            job_id=job_id,
            message=f"Training job started successfully. Job ID: {job_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start training job: {str(e)}"
        )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse, summary="Get training job status")
async def get_training_job_status(
    job_id: str,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> JobStatusResponse:
    """Get the status of a training job."""
    try:
        job_details = await ml_training_service.get_training_job_status(job_id)
        
        if not job_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training job {job_id} not found"
            )
        
        return JobStatusResponse(job_details=job_details)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/models", response_model=ModelListResponse, summary="List ML models")
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> ModelListResponse:
    """List all registered ML models."""
    try:
        models = await ml_training_service.list_models(model_type=model_type)
        
        return ModelListResponse(
            models=models,
            total=len(models)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.post("/models/{model_id}/deploy", summary="Deploy model to production")
async def deploy_model(
    model_id: int,
    current_user: User = Depends(require_role(UserRole.admin))
):
    """Deploy a model to production."""
    try:
        success = await ml_training_service.deploy_model(model_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found or cannot be deployed"
            )
        
        return {
            "message": f"Model {model_id} deployed successfully",
            "model_id": model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy model: {str(e)}"
        )


@router.get("/models/active", summary="Get active models")
async def get_active_models(
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    """Get all currently active/deployed models."""
    try:
        models = await ml_training_service.list_models()
        active_models = [m for m in models if m.get('is_active', False)]
        
        return {
            "active_models": active_models,
            "total": len(active_models)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active models: {str(e)}"
        )


@router.get("/predict/performance/{student_id}", summary="Predict student performance")
async def predict_student_performance(
    student_id: int,
    course_id: int = Query(..., description="Course ID for prediction"),
    model_id: Optional[int] = Query(None, description="Specific model ID (uses active model if not provided)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    """Predict performance for a specific student."""
    try:
        # Check if user has access to the course/student
        # In production, you'd want to verify course access
        
        result = await ml_inference_service.predict_student_performance(
            student_id=student_id,
            course_id=course_id,
            model_id=model_id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to generate prediction. Check if model is active and student data is available."
            )
        
        # Add recommendations based on prediction
        if result["prediction"]["performance_level"] == "low":
            result["recommendations"] = [
                "Schedule one-on-one meeting to discuss challenges",
                "Provide additional practice materials",
                "Consider extending deadlines for upcoming assignments",
                "Connect with academic support services"
            ]
            result["risk_factors"] = [
                "Low predicted performance score",
                "Historical pattern suggests intervention needed"
            ]
        else:
            result["recommendations"] = [
                "Continue current learning approach",
                "Consider advanced or enrichment materials",
                "Potential peer mentoring opportunity"
            ]
            result["success_factors"] = [
                "Strong predicted performance score",
                "Positive learning trajectory"
            ]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict performance: {str(e)}"
        )


@router.post("/predict/batch", summary="Batch predict for multiple students")
async def batch_predict(
    course_id: int,
    student_ids: Optional[List[int]] = None,
    model_id: Optional[int] = Query(None, description="Specific model ID (uses active model if not provided)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    """Run batch predictions for multiple students in a course."""
    try:
        # Check if user has access to the course
        # In production, you'd want to verify course access
        
        result = await ml_inference_service.batch_predict(
            course_id=course_id,
            student_ids=student_ids,
            model_id=model_id
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run batch prediction: {str(e)}"
        )


@router.get("/analytics/model-performance", summary="Get model performance analytics")
async def get_model_performance_analytics(
    model_id: Optional[int] = Query(None, description="Specific model ID"),
    current_user: User = Depends(require_role(UserRole.admin))
):
    """Get analytics on model performance and accuracy."""
    try:
        if not model_id:
            # Get active models and their stats
            models = await ml_training_service.list_models()
            active_models = [m for m in models if m.get('is_active', False)]
            
            if not active_models:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active models found"
                )
            
            # Use the first active model
            model_id = active_models[0]['id']
        
        analytics = await ml_inference_service.get_model_performance_stats(model_id)
        
        if "error" in analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analytics["error"]
            )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model analytics: {str(e)}"
        )


@router.get("/models/{model_id}/performance", summary="Get specific model performance")
async def get_specific_model_performance(
    model_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
):
    """Get detailed performance metrics for a specific model."""
    try:
        stats = await ml_inference_service.get_model_performance_stats(model_id)
        
        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=stats["error"]
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model performance: {str(e)}"
        )
