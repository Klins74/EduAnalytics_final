from sqlalchemy import Column, Integer, String, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base


class CanvasSyncState(Base):
    __tablename__ = 'canvas_sync_state'

    id = Column(Integer, primary_key=True)
    scope = Column(String, nullable=False)  # e.g., 'courses', 'course:123:assignments'
    cursor = Column(String, nullable=True)  # for incremental sync (if applicable)
    extra = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('scope', name='uq_canvas_sync_scope'),
    )


