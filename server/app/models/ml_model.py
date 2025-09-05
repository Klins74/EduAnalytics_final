"""ML Model registry and metadata storage."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class MLModel(Base):
    """Model for storing ML model metadata and registry."""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    model_type = Column(String(100), nullable=False)  # 'performance_predictor', 'risk_classifier', etc.
    description = Column(Text, nullable=True)
    
    # Model files and artifacts
    model_path = Column(String(500), nullable=True)  # Path to serialized model
    metadata_path = Column(String(500), nullable=True)  # Path to model metadata
    config = Column(JSON, nullable=True)  # Model configuration
    
    # Training information
    training_data_version = Column(String(100), nullable=True)
    training_started_at = Column(DateTime(timezone=True), nullable=True)
    training_completed_at = Column(DateTime(timezone=True), nullable=True)
    training_duration_seconds = Column(Float, nullable=True)
    
    # Model performance metrics
    validation_score = Column(Float, nullable=True)
    test_score = Column(Float, nullable=True)
    metrics = Column(JSON, nullable=True)  # Additional metrics (precision, recall, etc.)
    
    # Model status and deployment
    status = Column(String(50), nullable=False, default="training")  # training, trained, deployed, archived
    is_active = Column(Boolean, default=False)  # Is this the active model for production?
    deployment_notes = Column(Text, nullable=True)
    
    # Lifecycle timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)


class MLTrainingJob(Base):
    """Model for tracking ML training jobs."""
    __tablename__ = "ml_training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), nullable=False, unique=True, index=True)
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Job configuration
    config = Column(JSON, nullable=False)  # Training parameters, hyperparameters, etc.
    data_version = Column(String(100), nullable=True)
    
    # Job status and progress
    status = Column(String(50), nullable=False, default="queued")  # queued, running, completed, failed, cancelled
    progress_percent = Column(Float, default=0.0)
    current_step = Column(String(255), nullable=True)
    total_steps = Column(Integer, nullable=True)
    
    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results and outputs
    result_metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    logs_path = Column(String(500), nullable=True)
    artifacts_path = Column(String(500), nullable=True)
    
    # Resource usage
    cpu_hours = Column(Float, nullable=True)
    memory_peak_gb = Column(Float, nullable=True)
    gpu_hours = Column(Float, nullable=True)
    
    # Metadata
    created_by = Column(Integer, nullable=True)  # User ID who started the job
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MLPrediction(Base):
    """Model for storing ML predictions and their results."""
    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, nullable=False, index=True)  # Reference to MLModel
    prediction_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Prediction inputs and context
    input_features = Column(JSON, nullable=False)  # Features used for prediction
    context = Column(JSON, nullable=True)  # Additional context (student_id, course_id, etc.)
    
    # Prediction outputs
    prediction = Column(JSON, nullable=False)  # Model output
    confidence_score = Column(Float, nullable=True)
    prediction_probabilities = Column(JSON, nullable=True)  # For classification models
    
    # Prediction metadata
    prediction_type = Column(String(100), nullable=False)  # 'performance', 'risk', 'recommendation', etc.
    batch_id = Column(String(255), nullable=True)  # For batch predictions
    
    # Validation and feedback
    actual_outcome = Column(JSON, nullable=True)  # Actual outcome when available
    feedback_score = Column(Float, nullable=True)  # Human feedback on prediction quality
    is_correct = Column(Boolean, nullable=True)  # Was the prediction correct?
    
    # Timestamps
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())
    outcome_recorded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
