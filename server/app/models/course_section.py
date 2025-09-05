"""
Course Section and Group models.

Defines sections within courses and groups within sections for organizing
students and managing group assignments.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


# Association table for group memberships
group_memberships = Table(
    'group_memberships',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('course_groups.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(50), default='member'),  # member, leader
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('created_at', DateTime, default=datetime.utcnow)
)

# Association table for section enrollments
section_enrollments = Table(
    'section_enrollments',
    Base.metadata,
    Column('section_id', Integer, ForeignKey('course_sections.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(50), default='student'),  # student, teacher, ta, observer
    Column('enrolled_at', DateTime, default=datetime.utcnow),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class CourseSection(Base):
    """Course section model for organizing students within a course."""
    __tablename__ = "course_sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    section_code = Column(String(50))  # e.g., "001", "A", "MWF-9AM"
    
    # Section details
    description = Column(Text)
    max_enrollment = Column(Integer)
    is_active = Column(Boolean, default=True)
    
    # Canvas integration
    canvas_section_id = Column(String(50), unique=True, index=True)
    sis_section_id = Column(String(100), index=True)
    
    # Schedule information
    meeting_times = Column(Text)  # JSON string with schedule details
    location = Column(String(255))
    instructor_id = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="sections")
    instructor = relationship("User", foreign_keys=[instructor_id])
    groups = relationship("CourseGroup", back_populates="section")
    
    # Many-to-many relationship with users through section_enrollments
    enrolled_users = relationship(
        "User",
        secondary=section_enrollments,
        back_populates="enrolled_sections"
    )
    
    # Unique constraint on course_id and section_code
    __table_args__ = (
        UniqueConstraint('course_id', 'section_code', name='uq_course_section_code'),
    )

    def __repr__(self):
        return f"<CourseSection(id={self.id}, name='{self.name}', code='{self.section_code}')>"


class CourseGroup(Base):
    """Course group model for group work and assignments."""
    __tablename__ = "course_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(Integer, ForeignKey("course_sections.id", ondelete="SET NULL"), nullable=True)
    
    # Group details
    description = Column(Text)
    max_members = Column(Integer, default=6)
    is_active = Column(Boolean, default=True)
    is_self_signup = Column(Boolean, default=False)  # Students can join themselves
    
    # Group type and category
    group_category_id = Column(Integer, ForeignKey("group_categories.id"), nullable=True)
    group_type = Column(String(50), default="study")  # study, project, lab, discussion
    
    # Canvas integration
    canvas_group_id = Column(String(50), unique=True, index=True)
    
    # Leader and management
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="groups")
    section = relationship("CourseSection", back_populates="groups")
    category = relationship("GroupCategory", back_populates="groups")
    leader = relationship("User", foreign_keys=[leader_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    # Many-to-many relationship with users through group_memberships
    members = relationship(
        "User",
        secondary=group_memberships,
        back_populates="joined_groups"
    )
    
    # Group assignments
    assignments = relationship("Assignment", back_populates="group")

    def __repr__(self):
        return f"<CourseGroup(id={self.id}, name='{self.name}', course_id={self.course_id})>"


class GroupCategory(Base):
    """Group category for organizing different types of groups."""
    __tablename__ = "group_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    # Category settings
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    auto_leader = Column(Boolean, default=False)  # Automatically assign group leaders
    group_limit = Column(Integer)  # Max number of groups in this category
    
    # Self signup settings
    enable_self_signup = Column(Boolean, default=False)
    restrict_self_signup = Column(Boolean, default=False)  # Restrict to section
    
    # Canvas integration
    canvas_group_category_id = Column(String(50), unique=True, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="group_categories")
    groups = relationship("CourseGroup", back_populates="category")

    def __repr__(self):
        return f"<GroupCategory(id={self.id}, name='{self.name}', course_id={self.course_id})>"


class GroupSubmission(Base):
    """Group submission model for tracking group assignment submissions."""
    __tablename__ = "group_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("course_groups.id", ondelete="CASCADE"), nullable=False)
    
    # Submission details
    submitted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    submission_text = Column(Text)
    submission_url = Column(String(500))
    file_ids = Column(Text)  # JSON array of file IDs
    
    # Grading
    score = Column(Integer)
    grade = Column(String(10))
    graded_by = Column(Integer, ForeignKey("users.id"))
    graded_at = Column(DateTime)
    feedback = Column(Text)
    
    # Status and workflow
    workflow_state = Column(String(50), default="unsubmitted")  # unsubmitted, submitted, graded, returned
    late = Column(Boolean, default=False)
    missing = Column(Boolean, default=False)
    
    # Canvas integration
    canvas_submission_id = Column(String(50), unique=True, index=True)
    
    # Metadata
    submitted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="group_submissions")
    group = relationship("CourseGroup")
    submitter = relationship("User", foreign_keys=[submitted_by])
    grader = relationship("User", foreign_keys=[graded_by])

    def __repr__(self):
        return f"<GroupSubmission(id={self.id}, assignment_id={self.assignment_id}, group_id={self.group_id})>"


class GroupDiscussion(Base):
    """Group discussion model for group-specific discussions."""
    __tablename__ = "group_discussions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    group_id = Column(Integer, ForeignKey("course_groups.id", ondelete="CASCADE"), nullable=False)
    
    # Discussion content
    message = Column(Text)
    discussion_type = Column(String(50), default="threaded")  # threaded, side_comment
    
    # Settings
    is_announcement = Column(Boolean, default=False)
    require_initial_post = Column(Boolean, default=False)
    allow_rating = Column(Boolean, default=False)
    only_graders_can_rate = Column(Boolean, default=True)
    sort_by_rating = Column(Boolean, default=False)
    
    # Dates
    posted_at = Column(DateTime, default=datetime.utcnow)
    lock_at = Column(DateTime)
    
    # Canvas integration
    canvas_discussion_id = Column(String(50), unique=True, index=True)
    
    # User who created the discussion
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("CourseGroup")
    author = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<GroupDiscussion(id={self.id}, title='{self.title}', group_id={self.group_id})>"


# Update the existing models to add relationships

# Add to User model (this would be added to the existing User model)
"""
# Add these relationships to the User model:

enrolled_sections = relationship(
    "CourseSection",
    secondary=section_enrollments,
    back_populates="enrolled_users"
)

joined_groups = relationship(
    "CourseGroup", 
    secondary=group_memberships,
    back_populates="members"
)
"""

# Add to Course model (this would be added to the existing Course model)
"""
# Add these relationships to the Course model:

sections = relationship("CourseSection", back_populates="course")
groups = relationship("CourseGroup", back_populates="course") 
group_categories = relationship("GroupCategory", back_populates="course")
"""

# Add to Assignment model (this would be added to the existing Assignment model)
"""
# Add these relationships to the Assignment model:

group_id = Column(Integer, ForeignKey("course_groups.id"), nullable=True)
group = relationship("CourseGroup", back_populates="assignments")
group_submissions = relationship("GroupSubmission", back_populates="assignment")
is_group_assignment = Column(Boolean, default=False)
"""
