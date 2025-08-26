from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.quiz import Quiz, Question, QuestionOption, QuizAttempt, Answer
from app.schemas.quiz import QuizCreate, QuestionCreate, QuestionUpdate, QuizAttemptCreate, AnswerCreate
from datetime import datetime
from typing import List
from app.services.ai_quiz import auto_grade_answer

async def create_quiz(db: AsyncSession, quiz: QuizCreate, created_by: int):
    db_quiz = Quiz(**quiz.dict(), created_by_id=created_by)
    db.add(db_quiz)
    await db.commit()
    await db.refresh(db_quiz)
    return db_quiz

async def get_quiz(db: AsyncSession, quiz_id: int):
    result = await db.execute(select(Quiz).filter(Quiz.id == quiz_id))
    return result.scalar_one_or_none()

async def create_question(db: AsyncSession, question: QuestionCreate):
    from app.models.quiz import QuestionType
    
    # Prepare question data without options
    question_data = question.dict(exclude={'options'})
    question_type_str = question_data.get('type')
    if isinstance(question_type_str, str):
        try:
            question_data['type'] = QuestionType[question_type_str.upper()]
        except (KeyError, AttributeError):
            question_data['type'] = QuestionType.SHORT_ANSWER
    
    # Create question
    db_question = Question(**question_data)
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    
    # Create options if provided (Canvas-style)
    if question.options:
        for i, option_data in enumerate(question.options):
            option_dict = option_data.dict()
            option_dict['question_id'] = db_question.id
            option_dict['position'] = i + 1
            db_option = QuestionOption(**option_dict)
            db.add(db_option)
        
        await db.commit()
    
    # Always return question with loaded options (Canvas-style)
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .filter(Question.id == db_question.id)
    )
    return result.scalar_one()

async def create_attempt(db: AsyncSession, attempt: QuizAttemptCreate, student_id: int):
    db_attempt = QuizAttempt(**attempt.dict(), student_id=student_id)
    db.add(db_attempt)
    await db.commit()
    await db.refresh(db_attempt)
    return db_attempt

async def get_attempt(db: AsyncSession, attempt_id: int):
    result = await db.execute(select(QuizAttempt).filter(QuizAttempt.id == attempt_id))
    return result.scalar_one_or_none()

async def get_question(db: AsyncSession, question_id: int):
    # Canvas-style: load question with options
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .filter(Question.id == question_id)
    )
    return result.scalar_one_or_none()

async def submit_attempt(db: AsyncSession, attempt_id: int, answers: List[AnswerCreate]):
    attempt = await get_attempt(db, attempt_id)
    if not attempt:
        return None
    attempt.submitted_at = datetime.utcnow()
    attempt.status = "submitted"
    
    score = 0.0
    for ans in answers:
        db_ans = Answer(**ans.dict(), attempt_id=attempt_id)
        question = await get_question(db, ans.question_id)
        if question:
            # Canvas-style grading logic
            from app.models.quiz import QuestionType
            
            if question.type == QuestionType.MULTIPLE_CHOICE:
                # Check if selected options match correct ones
                if ans.selected_options and question.options:
                    correct_option_ids = [opt.id for opt in question.options if opt.is_correct]
                    if set(ans.selected_options) == set(correct_option_ids):
                        db_ans.is_correct = True
                        db_ans.points_earned = question.points
            elif question.type in [QuestionType.TRUE_FALSE, QuestionType.SHORT_ANSWER] and ans.answer_text == question.correct_answer:
                db_ans.is_correct = True
                db_ans.points_earned = question.points
            elif question.type in [QuestionType.ESSAY, QuestionType.SHORT_ANSWER]:
                # AI grading for text responses
                grading = await auto_grade_answer(question.text, ans.answer_text, question.points)
                db_ans.points_earned = grading['score']
                db_ans.feedback = grading['feedback']
                db_ans.is_correct = db_ans.points_earned > 0
            
            score += db_ans.points_earned
        db.add(db_ans)
    
    attempt.score = score
    await db.commit()
    await db.refresh(attempt)
    return attempt

async def list_quizzes_by_course(db: AsyncSession, course_id: int):
    result = await db.execute(select(Quiz).filter(Quiz.course_id == course_id))
    return result.scalars().all()

async def update_quiz(db: AsyncSession, quiz_id: int, data: dict):
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        return None
    for k, v in data.items():
        if hasattr(quiz, k) and v is not None:
            setattr(quiz, k, v)
    await db.commit()
    await db.refresh(quiz)
    return quiz

async def delete_quiz(db: AsyncSession, quiz_id: int) -> bool:
    quiz = await get_quiz(db, quiz_id)
    if not quiz:
        return False
    await db.delete(quiz)
    await db.commit()
    return True

async def list_questions(db: AsyncSession, quiz_id: int):
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.position.nulls_last())
    )
    return result.scalars().all()

async def update_question(db: AsyncSession, question_id: int, data: QuestionUpdate):
    q = await get_question(db, question_id)
    if not q:
        return None
    # Update base fields
    payload = data.dict(exclude_unset=True)
    options_payload = payload.pop("options", None)
    for k, v in payload.items():
        if k == "type" and isinstance(v, str):
            from app.models.quiz import QuestionType
            try:
                v = QuestionType[v.upper()]
            except Exception:
                continue
        setattr(q, k, v)
    await db.commit()
    await db.refresh(q)
    # Replace options if provided
    if options_payload is not None:
        # delete old
        for opt in list(q.options):
            await db.delete(opt)
        await db.commit()
        # add new with positions
        for idx, opt_in in enumerate(options_payload):
            opt_dict = opt_in.dict()
            opt = QuestionOption(
                question_id=q.id,
                text=opt_dict["text"],
                is_correct=opt_dict.get("is_correct", False),
                position=idx + 1,
            )
            db.add(opt)
        await db.commit()
        await db.refresh(q)
    # return with options
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .filter(Question.id == q.id)
    )
    return result.scalar_one()

async def delete_question(db: AsyncSession, question_id: int) -> bool:
    q = await get_question(db, question_id)
    if not q:
        return False
    await db.delete(q)
    await db.commit()
    return True
