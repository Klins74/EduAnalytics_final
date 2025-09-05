"""
Quiz Question Banks and Item Analysis models.

Provides comprehensive question banking system with item analysis,
difficulty tracking, and performance analytics for quiz questions.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from app.db.base_class import Base


class QuestionType(str, Enum):
    """Question type enumeration."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    ESSAY = "essay"
    MATCHING = "matching"
    NUMERICAL = "numerical"
    CALCULATED = "calculated"
    MULTIPLE_ANSWER = "multiple_answer"
    HOTSPOT = "hotspot"
    ORDERING = "ordering"


class DifficultyLevel(str, Enum):
    """Question difficulty level."""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class QuestionBank(Base):
    """Question bank model for organizing quiz questions."""
    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    # Bank details
    description = Column(Text)
    subject_area = Column(String(100))  # e.g., "Mathematics", "Biology", "History"
    topic = Column(String(100))  # More specific topic within subject
    
    # Settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # Can be shared across courses
    allow_random_selection = Column(Boolean, default=True)
    
    # Canvas integration
    canvas_question_bank_id = Column(String(50), unique=True, index=True)
    
    # Ownership and permissions
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_instructors = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="question_banks")
    creator = relationship("User", foreign_keys=[created_by])
    questions = relationship("BankQuestion", back_populates="bank")
    quiz_question_selections = relationship("QuizQuestionSelection", back_populates="question_bank")

    def __repr__(self):
        return f"<QuestionBank(id={self.id}, name='{self.name}', course_id={self.course_id})>"


class BankQuestion(Base):
    """Individual question within a question bank."""
    __tablename__ = "bank_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False)
    
    # Question content
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # QuestionType enum
    points = Column(Float, default=1.0)
    
    # Question options (JSON for flexibility)
    options = Column(JSON)  # For multiple choice, matching, etc.
    correct_answers = Column(JSON)  # Correct answer(s)
    
    # Question settings
    difficulty_level = Column(String(20), default="medium")  # DifficultyLevel enum
    estimated_time_minutes = Column(Integer, default=2)
    
    # Tags and categorization
    tags = Column(JSON)  # Array of tags
    learning_objective = Column(String(255))
    bloom_taxonomy_level = Column(String(50))  # remembering, understanding, applying, etc.
    
    # Question statistics (calculated from item analysis)
    usage_count = Column(Integer, default=0)
    average_score = Column(Float)
    difficulty_index = Column(Float)  # P-value (percentage who got it right)
    discrimination_index = Column(Float)  # How well it discriminates between high/low performers
    point_biserial_correlation = Column(Float)
    
    # Quality metrics
    needs_review = Column(Boolean, default=False)
    review_reason = Column(String(255))
    last_analyzed = Column(DateTime)
    
    # Canvas integration
    canvas_question_id = Column(String(50), unique=True, index=True)
    
    # Authorship
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_modified_by = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bank = relationship("QuestionBank", back_populates="questions")
    creator = relationship("User", foreign_keys=[created_by])
    modifier = relationship("User", foreign_keys=[last_modified_by])
    quiz_questions = relationship("QuizQuestion", back_populates="bank_question")
    responses = relationship("QuestionResponse", back_populates="question")

    def __repr__(self):
        return f"<BankQuestion(id={self.id}, type='{self.question_type}', bank_id={self.question_bank_id})>"


class QuizQuestionSelection(Base):
    """Tracks which questions from banks are selected for specific quizzes."""
    __tablename__ = "quiz_question_selections"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False)
    
    # Selection criteria
    num_questions = Column(Integer, default=1)  # How many questions to select from this bank
    selection_method = Column(String(50), default="random")  # random, difficulty_weighted, manual
    
    # Filtering criteria (JSON for flexibility)
    difficulty_filter = Column(JSON)  # e.g., ["easy", "medium"]
    tag_filter = Column(JSON)  # Only questions with these tags
    point_range = Column(JSON)  # e.g., {"min": 1, "max": 5}
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quiz = relationship("Quiz")
    question_bank = relationship("QuestionBank", back_populates="quiz_question_selections")

    def __repr__(self):
        return f"<QuizQuestionSelection(quiz_id={self.quiz_id}, bank_id={self.question_bank_id})>"


class QuestionResponse(Base):
    """Individual student responses to questions for item analysis."""
    __tablename__ = "question_responses"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("bank_questions.id", ondelete="CASCADE"), nullable=False)
    quiz_submission_id = Column(Integer, ForeignKey("quiz_submissions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Response data
    response_text = Column(Text)  # Student's answer
    selected_options = Column(JSON)  # For multiple choice, multiple answer
    is_correct = Column(Boolean)
    points_earned = Column(Float, default=0.0)
    points_possible = Column(Float)
    
    # Response metadata
    time_spent_seconds = Column(Integer)
    attempt_number = Column(Integer, default=1)
    
    # Analysis flags
    is_outlier = Column(Boolean, default=False)  # Statistical outlier
    confidence_level = Column(String(20))  # high, medium, low (for self-assessment)
    
    # Metadata
    responded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("BankQuestion", back_populates="responses")
    submission = relationship("QuizSubmission")
    user = relationship("User")

    def __repr__(self):
        return f"<QuestionResponse(question_id={self.question_id}, user_id={self.user_id}, correct={self.is_correct})>"


class ItemAnalysis(Base):
    """Comprehensive item analysis results for questions."""
    __tablename__ = "item_analyses"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("bank_questions.id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=True)
    
    # Analysis parameters
    analysis_date = Column(DateTime, default=datetime.utcnow)
    sample_size = Column(Integer)  # Number of responses analyzed
    min_sample_size = Column(Integer, default=10)  # Minimum for reliable analysis
    
    # Classical Test Theory metrics
    difficulty_index = Column(Float)  # P-value: % of students who got it right
    discrimination_index = Column(Float)  # D-value: difference between high/low performers
    point_biserial_correlation = Column(Float)  # Correlation with total score
    
    # Distractor analysis (for multiple choice)
    distractor_analysis = Column(JSON)  # Analysis of each option's selection rate
    
    # Item Response Theory metrics (if available)
    irt_difficulty = Column(Float)  # b parameter
    irt_discrimination = Column(Float)  # a parameter
    irt_guessing = Column(Float)  # c parameter
    
    # Quality indicators
    quality_score = Column(Float)  # Overall quality score (0-100)
    quality_flags = Column(JSON)  # Array of quality issues
    
    # Recommendations
    recommendation = Column(String(50))  # keep, revise, discard
    revision_suggestions = Column(JSON)  # Specific suggestions for improvement
    
    # Performance by group (optional demographic analysis)
    group_performance = Column(JSON)  # Performance breakdown by groups
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    question = relationship("BankQuestion")
    quiz = relationship("Quiz")

    def __repr__(self):
        return f"<ItemAnalysis(question_id={self.question_id}, difficulty={self.difficulty_index}, discrimination={self.discrimination_index})>"


class QuestionTag(Base):
    """Tags for categorizing and organizing questions."""
    __tablename__ = "question_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True)
    
    # Tag properties
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    is_system_tag = Column(Boolean, default=False)  # System-defined vs user-defined
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    course = relationship("Course")
    
    # Unique constraint on name per course
    __table_args__ = (
        UniqueConstraint('name', 'course_id', name='uq_question_tag_name_course'),
    )

    def __repr__(self):
        return f"<QuestionTag(id={self.id}, name='{self.name}')>"


class QuestionUsageLog(Base):
    """Log of question usage for tracking and analytics."""
    __tablename__ = "question_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("bank_questions.id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    # Usage context
    usage_type = Column(String(50), default="quiz")  # quiz, practice, assessment
    selection_method = Column(String(50))  # random, manual, algorithm
    
    # Performance data
    total_responses = Column(Integer, default=0)
    correct_responses = Column(Integer, default=0)
    average_time_seconds = Column(Float)
    
    # Metadata
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("BankQuestion")
    quiz = relationship("Quiz")
    course = relationship("Course")

    def __repr__(self):
        return f"<QuestionUsageLog(question_id={self.question_id}, quiz_id={self.quiz_id})>"


# Add relationships to existing models (these would be added to existing model files)

# Add to Course model:
"""
question_banks = relationship("QuestionBank", back_populates="course")
"""

# Add to Quiz model:
"""
question_selections = relationship("QuizQuestionSelection", back_populates="quiz")
"""

# Add to QuizQuestion model (if it exists):
"""
bank_question_id = Column(Integer, ForeignKey("bank_questions.id"), nullable=True)
bank_question = relationship("BankQuestion", back_populates="quiz_questions")
"""

# Add to QuizSubmission model (if it exists):
"""
question_responses = relationship("QuestionResponse", back_populates="submission")
"""
