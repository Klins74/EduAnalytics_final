"""API routes for quiz question banks and item analysis."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, date

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.quiz_bank_service import question_bank_service, item_analysis_service

router = APIRouter(prefix="/quiz-banks", tags=["Quiz Banks & Item Analysis"])


# Pydantic models for requests
class QuestionBankCreateRequest(BaseModel):
    """Request model for creating a question bank."""
    name: str
    course_id: int
    description: Optional[str] = None
    subject_area: Optional[str] = None
    topic: Optional[str] = None
    is_public: bool = False
    allow_random_selection: bool = True
    shared_with_instructors: bool = False
    canvas_question_bank_id: Optional[str] = None


class BankQuestionCreateRequest(BaseModel):
    """Request model for creating a question in a bank."""
    question_bank_id: int
    question_text: str
    question_type: str
    points: float = 1.0
    options: Optional[Dict[str, Any]] = None
    correct_answers: Optional[Dict[str, Any]] = None
    difficulty_level: str = "medium"
    estimated_time_minutes: int = 2
    tags: Optional[List[str]] = None
    learning_objective: Optional[str] = None
    bloom_taxonomy_level: Optional[str] = None
    canvas_question_id: Optional[str] = None


class QuestionUpdateRequest(BaseModel):
    """Request model for updating a question."""
    question_text: Optional[str] = None
    question_type: Optional[str] = None
    points: Optional[float] = None
    options: Optional[Dict[str, Any]] = None
    correct_answers: Optional[Dict[str, Any]] = None
    difficulty_level: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    tags: Optional[List[str]] = None
    learning_objective: Optional[str] = None
    bloom_taxonomy_level: Optional[str] = None


class QuestionSearchRequest(BaseModel):
    """Request model for searching questions."""
    course_id: Optional[int] = None
    question_bank_id: Optional[int] = None
    question_type: Optional[str] = None
    difficulty_level: Optional[str] = None
    tags: Optional[List[str]] = None
    text_search: Optional[str] = None
    point_range: Optional[Dict[str, float]] = None


class ItemAnalysisRequest(BaseModel):
    """Request model for item analysis."""
    question_ids: List[int]
    quiz_id: Optional[int] = None


# Question Bank endpoints
@router.post("/banks", summary="Create question bank")
async def create_question_bank(
    request: QuestionBankCreateRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Create a new question bank."""
    try:
        bank_data = request.dict()
        bank_data["created_by"] = current_user.id
        
        bank = await question_bank_service.create_question_bank(bank_data)
        
        return {
            "success": True,
            "message": "Question bank created successfully",
            "bank": {
                "id": bank.id,
                "name": bank.name,
                "course_id": bank.course_id,
                "description": bank.description,
                "subject_area": bank.subject_area,
                "topic": bank.topic,
                "is_public": bank.is_public,
                "allow_random_selection": bank.allow_random_selection,
                "shared_with_instructors": bank.shared_with_instructors,
                "created_by": bank.created_by,
                "is_active": bank.is_active,
                "created_at": bank.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create question bank: {str(e)}"
        )


@router.get("/banks/{bank_id}", summary="Get question bank")
async def get_question_bank(
    bank_id: int,
    include_questions: bool = Query(False, description="Include questions in response"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get question bank details."""
    try:
        bank = await question_bank_service.get_question_bank(bank_id, include_questions)
        
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question bank {bank_id} not found"
            )
        
        response_data = {
            "success": True,
            "bank": {
                "id": bank.id,
                "name": bank.name,
                "course_id": bank.course_id,
                "description": bank.description,
                "subject_area": bank.subject_area,
                "topic": bank.topic,
                "is_public": bank.is_public,
                "allow_random_selection": bank.allow_random_selection,
                "shared_with_instructors": bank.shared_with_instructors,
                "created_by": bank.created_by,
                "is_active": bank.is_active,
                "created_at": bank.created_at.isoformat(),
                "updated_at": bank.updated_at.isoformat()
            }
        }
        
        if include_questions and hasattr(bank, 'questions'):
            response_data["bank"]["questions"] = [
                {
                    "id": q.id,
                    "question_text": q.question_text[:200] + "..." if len(q.question_text) > 200 else q.question_text,
                    "question_type": q.question_type,
                    "points": q.points,
                    "difficulty_level": q.difficulty_level,
                    "tags": q.tags,
                    "usage_count": q.usage_count,
                    "needs_review": q.needs_review,
                    "created_at": q.created_at.isoformat()
                }
                for q in bank.questions
            ]
            response_data["bank"]["question_count"] = len(bank.questions)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get question bank: {str(e)}"
        )


@router.get("/courses/{course_id}/banks", summary="Get course question banks")
async def get_course_question_banks(
    course_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all question banks for a course."""
    try:
        banks = await question_bank_service.get_course_question_banks(course_id, current_user.id)
        
        return {
            "success": True,
            "course_id": course_id,
            "banks": [
                {
                    "id": bank.id,
                    "name": bank.name,
                    "description": bank.description,
                    "subject_area": bank.subject_area,
                    "topic": bank.topic,
                    "question_count": len(bank.questions) if hasattr(bank, 'questions') else 0,
                    "is_public": bank.is_public,
                    "shared_with_instructors": bank.shared_with_instructors,
                    "creator": {
                        "id": bank.creator.id,
                        "name": bank.creator.name
                    } if hasattr(bank, 'creator') and bank.creator else None,
                    "created_at": bank.created_at.isoformat()
                }
                for bank in banks
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course question banks: {str(e)}"
        )


# Question endpoints
@router.post("/questions", summary="Add question to bank")
async def add_question_to_bank(
    request: BankQuestionCreateRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Add a new question to a question bank."""
    try:
        question_data = request.dict()
        question_data["created_by"] = current_user.id
        
        question = await question_bank_service.add_question_to_bank(question_data)
        
        return {
            "success": True,
            "message": "Question added to bank successfully",
            "question": {
                "id": question.id,
                "question_bank_id": question.question_bank_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "points": question.points,
                "difficulty_level": question.difficulty_level,
                "estimated_time_minutes": question.estimated_time_minutes,
                "tags": question.tags,
                "learning_objective": question.learning_objective,
                "bloom_taxonomy_level": question.bloom_taxonomy_level,
                "created_by": question.created_by,
                "created_at": question.created_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add question to bank: {str(e)}"
        )


@router.put("/questions/{question_id}", summary="Update question")
async def update_question(
    question_id: int,
    request: QuestionUpdateRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Update a question in a bank."""
    try:
        question_data = {k: v for k, v in request.dict().items() if v is not None}
        
        question = await question_bank_service.update_question(question_id, question_data, current_user.id)
        
        return {
            "success": True,
            "message": "Question updated successfully",
            "question": {
                "id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "points": question.points,
                "difficulty_level": question.difficulty_level,
                "tags": question.tags,
                "last_modified_by": question.last_modified_by,
                "updated_at": question.updated_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update question: {str(e)}"
        )


@router.post("/questions/search", summary="Search questions")
async def search_questions(
    request: QuestionSearchRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Search questions in banks based on criteria."""
    try:
        search_criteria = {k: v for k, v in request.dict().items() if v is not None}
        
        questions = await question_bank_service.search_questions(search_criteria)
        
        return {
            "success": True,
            "search_criteria": search_criteria,
            "total_results": len(questions),
            "questions": [
                {
                    "id": q.id,
                    "question_bank_id": q.question_bank_id,
                    "question_text": q.question_text[:300] + "..." if len(q.question_text) > 300 else q.question_text,
                    "question_type": q.question_type,
                    "points": q.points,
                    "difficulty_level": q.difficulty_level,
                    "tags": q.tags,
                    "learning_objective": q.learning_objective,
                    "bloom_taxonomy_level": q.bloom_taxonomy_level,
                    "usage_count": q.usage_count,
                    "difficulty_index": q.difficulty_index,
                    "discrimination_index": q.discrimination_index,
                    "needs_review": q.needs_review,
                    "created_at": q.created_at.isoformat()
                }
                for q in questions
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search questions: {str(e)}"
        )


@router.get("/questions/{question_id}/statistics", summary="Get question statistics")
async def get_question_statistics(
    question_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get comprehensive statistics for a question."""
    try:
        stats = await question_bank_service.get_question_statistics(question_id)
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get question statistics: {str(e)}"
        )


# Item Analysis endpoints
@router.post("/item-analysis", summary="Perform item analysis")
async def perform_item_analysis(
    request: ItemAnalysisRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Perform item analysis on selected questions."""
    try:
        analyses = await item_analysis_service.bulk_analyze_questions(
            request.question_ids, request.quiz_id
        )
        
        return {
            "success": True,
            "message": f"Item analysis completed for {len(analyses)} questions",
            "quiz_id": request.quiz_id,
            "analyses": [
                {
                    "question_id": analysis.question_id,
                    "sample_size": analysis.sample_size,
                    "difficulty_index": analysis.difficulty_index,
                    "discrimination_index": analysis.discrimination_index,
                    "point_biserial_correlation": analysis.point_biserial_correlation,
                    "quality_score": analysis.quality_score,
                    "quality_flags": analysis.quality_flags,
                    "recommendation": analysis.recommendation,
                    "analysis_date": analysis.analysis_date.isoformat()
                }
                for analysis in analyses
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform item analysis: {str(e)}"
        )


@router.get("/questions/{question_id}/analysis", summary="Get question analysis")
async def get_question_analysis(
    question_id: int,
    quiz_id: Optional[int] = Query(None, description="Specific quiz analysis"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get item analysis for a specific question."""
    try:
        analysis = await item_analysis_service.analyze_question(question_id, quiz_id)
        
        return {
            "success": True,
            "analysis": {
                "id": analysis.id,
                "question_id": analysis.question_id,
                "quiz_id": analysis.quiz_id,
                "sample_size": analysis.sample_size,
                "difficulty_index": analysis.difficulty_index,
                "discrimination_index": analysis.discrimination_index,
                "point_biserial_correlation": analysis.point_biserial_correlation,
                "quality_score": analysis.quality_score,
                "quality_flags": analysis.quality_flags,
                "recommendation": analysis.recommendation,
                "distractor_analysis": analysis.distractor_analysis,
                "revision_suggestions": analysis.revision_suggestions,
                "analysis_date": analysis.analysis_date.isoformat(),
                "created_at": analysis.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get question analysis: {str(e)}"
        )


@router.get("/courses/{course_id}/analysis-report", summary="Get course analysis report")
async def get_course_analysis_report(
    course_id: int,
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get comprehensive item analysis report for a course."""
    try:
        date_range = None
        if start_date and end_date:
            date_range = (
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )
        
        report = await item_analysis_service.get_analysis_report(course_id, date_range)
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis report: {str(e)}"
        )


@router.get("/questions/needs-review", summary="Get questions needing review")
async def get_questions_needing_review(
    course_id: Optional[int] = Query(None, description="Filter by course"),
    limit: int = Query(50, description="Maximum number of questions", le=100),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get questions that need review based on item analysis."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.quiz_bank import BankQuestion, QuestionBank
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            query = select(BankQuestion).where(BankQuestion.needs_review == True)
            
            if course_id:
                query = query.join(QuestionBank).where(QuestionBank.course_id == course_id)
            
            query = query.order_by(BankQuestion.last_analyzed.desc()).limit(limit)
            
            result = await db.execute(query)
            questions = result.scalars().all()
            
            return {
                "success": True,
                "course_id": course_id,
                "total_questions": len(questions),
                "questions": [
                    {
                        "id": q.id,
                        "question_bank_id": q.question_bank_id,
                        "question_text": q.question_text[:200] + "..." if len(q.question_text) > 200 else q.question_text,
                        "question_type": q.question_type,
                        "difficulty_level": q.difficulty_level,
                        "difficulty_index": q.difficulty_index,
                        "discrimination_index": q.discrimination_index,
                        "point_biserial_correlation": q.point_biserial_correlation,
                        "review_reason": q.review_reason,
                        "usage_count": q.usage_count,
                        "last_analyzed": q.last_analyzed.isoformat() if q.last_analyzed else None,
                        "created_at": q.created_at.isoformat()
                    }
                    for q in questions
                ]
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get questions needing review: {str(e)}"
        )


@router.get("/analytics/summary", summary="Get quiz bank analytics summary")
async def get_quiz_bank_analytics_summary(
    course_id: Optional[int] = Query(None, description="Filter by course"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get summary analytics for quiz banks and questions."""
    try:
        from app.db.session import AsyncSessionLocal
        from app.models.quiz_bank import QuestionBank, BankQuestion, ItemAnalysis
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as db:
            # Base queries
            bank_query = select(QuestionBank)
            question_query = select(BankQuestion).join(QuestionBank)
            analysis_query = select(ItemAnalysis).join(BankQuestion).join(QuestionBank)
            
            if course_id:
                bank_query = bank_query.where(QuestionBank.course_id == course_id)
                question_query = question_query.where(QuestionBank.course_id == course_id)
                analysis_query = analysis_query.where(QuestionBank.course_id == course_id)
            
            # Get counts
            bank_count = await db.execute(select(func.count()).select_from(bank_query.subquery()))
            question_count = await db.execute(select(func.count()).select_from(question_query.subquery()))
            analysis_count = await db.execute(select(func.count()).select_from(analysis_query.subquery()))
            
            # Get questions by difficulty
            difficulty_stats = await db.execute(
                select(
                    BankQuestion.difficulty_level,
                    func.count(BankQuestion.id).label('count')
                )
                .select_from(question_query.subquery())
                .group_by(BankQuestion.difficulty_level)
            )
            
            # Get questions by type
            type_stats = await db.execute(
                select(
                    BankQuestion.question_type,
                    func.count(BankQuestion.id).label('count')
                )
                .select_from(question_query.subquery())
                .group_by(BankQuestion.question_type)
            )
            
            # Get questions needing review
            review_count = await db.execute(
                select(func.count())
                .select_from(question_query.where(BankQuestion.needs_review == True).subquery())
            )
            
            # Get recent analyses
            recent_analyses = await db.execute(
                select(ItemAnalysis)
                .join(BankQuestion)
                .join(QuestionBank)
                .where(QuestionBank.course_id == course_id if course_id else True)
                .order_by(ItemAnalysis.analysis_date.desc())
                .limit(5)
            )
            
            return {
                "success": True,
                "course_id": course_id,
                "summary": {
                    "total_banks": bank_count.scalar(),
                    "total_questions": question_count.scalar(),
                    "total_analyses": analysis_count.scalar(),
                    "questions_needing_review": review_count.scalar()
                },
                "difficulty_distribution": {
                    row.difficulty_level: row.count 
                    for row in difficulty_stats.fetchall()
                },
                "type_distribution": {
                    row.question_type: row.count 
                    for row in type_stats.fetchall()
                },
                "recent_analyses": [
                    {
                        "question_id": analysis.question_id,
                        "difficulty_index": analysis.difficulty_index,
                        "discrimination_index": analysis.discrimination_index,
                        "recommendation": analysis.recommendation,
                        "analysis_date": analysis.analysis_date.isoformat()
                    }
                    for analysis in recent_analyses.scalars().all()
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics summary: {str(e)}"
        )
