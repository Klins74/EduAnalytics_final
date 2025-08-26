from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    ESSAY = "essay"
    SHORT_ANSWER = "short_answer"

# QuestionOption schemas
class QuestionOptionBase(BaseModel):
    text: str
    is_correct: bool = False
    position: Optional[int] = None

class QuestionOptionCreate(QuestionOptionBase):
    pass

class QuestionOption(QuestionOptionBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True

# Quiz schemas
class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit: Optional[int] = None
    attempts_allowed: int = 1
    randomize_questions: bool = False

class QuizCreate(QuizBase):
    course_id: int

class QuizUpdate(QuizBase):
    pass

class Quiz(QuizBase):
    id: int
    course_id: int
    created_at: datetime
    created_by_id: int

    class Config:
        from_attributes = True

# Question schemas
class QuestionBase(BaseModel):
    text: str
    type: QuestionType
    correct_answer: Optional[str] = None
    points: float = 1.0
    position: Optional[int] = None

class QuestionCreate(QuestionBase):
    quiz_id: int
    options: Optional[List[QuestionOptionCreate]] = None  # for multiple_choice

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    type: Optional[QuestionType] = None
    correct_answer: Optional[str] = None
    points: Optional[float] = None
    position: Optional[int] = None
    options: Optional[List[QuestionOptionCreate]] = None

class Question(QuestionBase):
    id: int
    quiz_id: int
    options: List[QuestionOption] = []  # Canvas-style: list of options

    class Config:
        from_attributes = True

class QuizAttemptBase(BaseModel):
    status: Optional[str] = "in_progress"

class QuizAttemptCreate(BaseModel):
    quiz_id: int

class QuizAttempt(QuizAttemptBase):
    id: int
    quiz_id: int
    student_id: int
    started_at: datetime
    submitted_at: Optional[datetime]
    score: float

    class Config:
        from_attributes = True

class AnswerBase(BaseModel):
    answer_text: Optional[str]
    selected_options: Optional[List[int]] = None
    is_correct: Optional[bool]
    points_earned: float = 0.0
    feedback: Optional[str]

class AnswerCreate(AnswerBase):
    question_id: int

class Answer(AnswerBase):
    id: int
    attempt_id: int
    question_id: int

    class Config:
        from_attributes = True
