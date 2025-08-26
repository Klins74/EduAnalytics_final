from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import enum

class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    ESSAY = "essay"
    SHORT_ANSWER = "short_answer"

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    time_limit = Column(Integer)  # в минутах, 0 = без лимита
    attempts_allowed = Column(Integer, default=1)
    randomize_questions = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))  # учитель/админ
    
    course = relationship("Course", back_populates="quizzes")
    creator = relationship("User", back_populates="created_quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    text = Column(String, nullable=False)
    type = Column(SQLEnum(QuestionType), nullable=False)
    correct_answer = Column(String)  # для simple types (true_false, short_answer)
    points = Column(Float, default=1.0)
    position = Column(Integer)  # порядок в квизе
    
    quiz = relationship("Quiz", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="question")

class QuestionOption(Base):
    __tablename__ = "question_options"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    position = Column(Integer)  # порядок варианта в вопросе
    
    question = relationship("Question", back_populates="options")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime)
    score = Column(Float, default=0.0)
    status = Column(String, default="in_progress")  # "in_progress", "submitted", "graded"
    
    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(String)
    selected_options = Column(JSON)  # для multiple_choice
    is_correct = Column(Boolean)
    points_earned = Column(Float, default=0.0)
    feedback = Column(String)  # AI-generated feedback
    
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")
