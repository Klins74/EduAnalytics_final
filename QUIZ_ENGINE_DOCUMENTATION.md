# Quiz Engine Documentation

## Overview

Quiz Engine is a module for EduAnalytics that provides functionality for creating and managing quizzes, questions, and student attempts. It supports multiple question types, automatic grading, and AI-assisted feedback.

## Features

- Create and manage quizzes
- Support for multiple question types (multiple choice, true/false, essay, short answer)
- Student attempts tracking
- Automatic grading
- AI-assisted feedback for essay and short answer questions

## Architecture

### Models

The Quiz Engine consists of the following models:

#### Quiz

Represents a quiz that can be assigned to students.

```python
class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    time_limit = Column(Integer)  # in minutes, 0 = no limit
    attempts_allowed = Column(Integer, default=1)
    randomize_questions = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    course = relationship("Course", back_populates="quizzes")
    creator = relationship("User", back_populates="created_quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
```

#### Question

Represents a question in a quiz.

```python
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    text = Column(String, nullable=False)
    type = Column(SQLEnum(QuestionType), nullable=False)
    options = Column(JSON)  # for multiple_choice: [{"text": "Option A", "is_correct": true}]
    correct_answer = Column(String)  # for simple types
    points = Column(Float, default=1.0)
    position = Column(Integer)  # order in quiz
    
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question")
```

#### QuizAttempt

Represents a student's attempt at a quiz.

```python
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
```

#### Answer

Represents a student's answer to a question.

```python
class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(String)
    selected_options = Column(JSON)  # for multiple_choice
    is_correct = Column(Boolean)
    points_earned = Column(Float, default=0.0)
    feedback = Column(String)  # AI-generated feedback
    
    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")
```

### API Endpoints

#### Quiz Management

- `POST /api/quizzes/`: Create a new quiz
  - Required role: teacher or admin
  - Request body: `QuizCreate` schema
  - Response: `Quiz` schema

- `GET /api/quizzes/{quiz_id}`: Get quiz details
  - Response: `Quiz` schema

#### Question Management

- `POST /api/quizzes/{quiz_id}/questions/`: Add a question to a quiz
  - Request body: `QuestionCreate` schema
  - Response: `Question` schema

#### Quiz Attempts

- `POST /api/quizzes/{quiz_id}/attempts/`: Start a quiz attempt
  - Required role: student
  - Request body: `QuizAttemptCreate` schema
  - Response: `QuizAttempt` schema

- `POST /api/quizzes/{attempt_id}/submit/`: Submit answers for a quiz attempt
  - Request body: List of `AnswerCreate` schema
  - Response: `QuizAttempt` schema

### AI Integration

The Quiz Engine integrates with AI to provide automatic grading and feedback for essay and short answer questions. The AI integration is implemented in `server/app/services/ai_quiz.py`.

#### AI Functions

- `generate_questions(course_id, num_questions, topic)`: Generates quiz questions based on a topic
- `auto_grade_answer(question_text, answer_text, max_points)`: Grades an answer and provides feedback

## Usage Examples

### Creating a Quiz

```python
# Example: Creating a quiz
quiz_data = {
    "course_id": 1,
    "title": "Introduction to Python",
    "description": "Test your Python knowledge",
    "time_limit": 30,  # 30 minutes
    "attempts_allowed": 2,
    "randomize_questions": True
}
quiz = await create_quiz(db, QuizCreate(**quiz_data), teacher_id)
```

### Adding a Question

```python
# Example: Adding a multiple choice question
question_data = {
    "quiz_id": quiz.id,
    "text": "What is the output of print(1 + 2)?",
    "type": "multiple_choice",
    "options": [
        {"text": "1", "is_correct": False},
        {"text": "2", "is_correct": False},
        {"text": "3", "is_correct": True},
        {"text": "4", "is_correct": False}
    ],
    "points": 1.0,
    "position": 1
}
question = await create_question(db, QuestionCreate(**question_data))
```

### Starting a Quiz Attempt

```python
# Example: Starting a quiz attempt
attempt_data = {
    "quiz_id": quiz.id
}
attempt = await create_attempt(db, QuizAttemptCreate(**attempt_data), student_id)
```

### Submitting Answers

```python
# Example: Submitting answers
answers_data = [
    {
        "question_id": question.id,
        "answer_text": "3",
        "is_correct": None,  # Will be determined by the system
        "feedback": None  # Will be generated by AI
    }
]
result = await submit_attempt(db, attempt.id, [AnswerCreate(**answer) for answer in answers_data])
```

## Frontend Integration

The Quiz Engine can be integrated with the frontend using the provided API endpoints. A test page is available at `public/test-quiz.html` for testing the API.

## Future Improvements

- Support for more question types (matching, fill-in-the-blank, etc.)
- Quiz templates for easy creation of common quiz types
- More advanced AI grading for essay questions
- Quiz statistics and analytics
- Quiz sharing between teachers

