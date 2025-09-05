from sqlalchemy import Column, Integer, String, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.db.base import Base


class CanvasCourse(Base):
    __tablename__ = 'canvas_courses'

    id = Column(Integer, primary_key=True)
    canvas_id = Column(Integer, nullable=False)
    owner_user_id = Column(Integer, nullable=True)
    data = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('canvas_id', name='uq_canvas_courses_canvas_id'),
        Index('ix_canvas_courses_canvas_id', 'canvas_id'),
    )


class CanvasEnrollment(Base):
    __tablename__ = 'canvas_enrollments'

    id = Column(Integer, primary_key=True)
    canvas_id = Column(Integer, nullable=False)
    course_canvas_id = Column(Integer, nullable=False)
    data = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('canvas_id', name='uq_canvas_enrollments_canvas_id'),
        Index('ix_canvas_enrollments_course_canvas_id', 'course_canvas_id'),
    )


class CanvasAssignment(Base):
    __tablename__ = 'canvas_assignments'

    id = Column(Integer, primary_key=True)
    canvas_id = Column(Integer, nullable=False)
    course_canvas_id = Column(Integer, nullable=False)
    data = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('canvas_id', name='uq_canvas_assignments_canvas_id'),
        Index('ix_canvas_assignments_course_canvas_id', 'course_canvas_id'),
    )


class CanvasSubmission(Base):
    __tablename__ = 'canvas_submissions'

    id = Column(Integer, primary_key=True)
    canvas_id = Column(Integer, nullable=False)
    assignment_canvas_id = Column(Integer, nullable=False)
    course_canvas_id = Column(Integer, nullable=True)
    data = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('canvas_id', name='uq_canvas_submissions_canvas_id'),
        Index('ix_canvas_submissions_assignment_canvas_id', 'assignment_canvas_id'),
    )


