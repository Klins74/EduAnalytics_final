from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class FeedbackBase(BaseModel):
    """Базовая схема для комментариев."""
    text: str = Field(..., min_length=1, max_length=5000, description="Текст комментария")


class FeedbackCreate(FeedbackBase):
    """Схема для создания комментария."""
    pass


class FeedbackUpdate(BaseModel):
    """Схема для обновления комментария."""
    text: Optional[str] = Field(None, min_length=1, max_length=5000, description="Текст комментария")


class FeedbackRead(FeedbackBase):
    """Схема для чтения комментария."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    submission_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class FeedbackReadWithAuthor(FeedbackRead):
    """Схема для чтения комментария с информацией об авторе."""
    author_name: Optional[str] = Field(None, description="Имя автора комментария")
    author_email: Optional[str] = Field(None, description="Email автора комментария")


class FeedbackList(BaseModel):
    """Схема для списка комментариев с пагинацией."""
    items: list[FeedbackReadWithAuthor]
    total: int
    page: int
    size: int
    pages: int


class FeedbackStats(BaseModel):
    """Схема для статистики комментариев."""
    total_feedbacks: int
    feedbacks_by_submission: dict[str, int]
    recent_feedbacks_count: int
    average_feedback_length: float