"""
Quiz Question Bank and Item Analysis Service.

Provides comprehensive management of question banks, item analysis,
and question quality assessment for educational assessments.
"""

import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.quiz_bank import (
    QuestionBank, BankQuestion, QuizQuestionSelection, QuestionResponse,
    ItemAnalysis, QuestionTag, QuestionUsageLog, QuestionType, DifficultyLevel
)

logger = logging.getLogger(__name__)


class QuestionBankService:
    """Service for managing question banks."""
    
    async def create_question_bank(self, bank_data: Dict[str, Any]) -> QuestionBank:
        """Create a new question bank."""
        try:
            async with AsyncSessionLocal() as db:
                bank = QuestionBank(
                    name=bank_data["name"],
                    course_id=bank_data["course_id"],
                    description=bank_data.get("description"),
                    subject_area=bank_data.get("subject_area"),
                    topic=bank_data.get("topic"),
                    is_public=bank_data.get("is_public", False),
                    allow_random_selection=bank_data.get("allow_random_selection", True),
                    created_by=bank_data["created_by"],
                    shared_with_instructors=bank_data.get("shared_with_instructors", False),
                    canvas_question_bank_id=bank_data.get("canvas_question_bank_id")
                )
                
                db.add(bank)
                await db.commit()
                await db.refresh(bank)
                
                logger.info(f"Created question bank: {bank.name} (ID: {bank.id})")
                return bank
                
        except Exception as e:
            logger.error(f"Error creating question bank: {e}")
            raise
    
    async def get_question_bank(self, bank_id: int, include_questions: bool = False) -> Optional[QuestionBank]:
        """Get question bank by ID."""
        try:
            async with AsyncSessionLocal() as db:
                query = select(QuestionBank).where(QuestionBank.id == bank_id)
                
                if include_questions:
                    query = query.options(
                        selectinload(QuestionBank.questions),
                        selectinload(QuestionBank.creator)
                    )
                
                result = await db.execute(query)
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Error getting question bank: {e}")
            return None
    
    async def get_course_question_banks(self, course_id: int, user_id: Optional[int] = None) -> List[QuestionBank]:
        """Get all question banks for a course."""
        try:
            async with AsyncSessionLocal() as db:
                query = select(QuestionBank).where(
                    and_(
                        QuestionBank.course_id == course_id,
                        QuestionBank.is_active == True
                    )
                )
                
                # If user_id provided, include banks they created or that are shared
                if user_id:
                    query = query.where(
                        or_(
                            QuestionBank.created_by == user_id,
                            QuestionBank.shared_with_instructors == True,
                            QuestionBank.is_public == True
                        )
                    )
                
                query = query.options(
                    selectinload(QuestionBank.creator),
                    selectinload(QuestionBank.questions)
                ).order_by(QuestionBank.name)
                
                result = await db.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Error getting course question banks: {e}")
            return []
    
    async def add_question_to_bank(self, question_data: Dict[str, Any]) -> BankQuestion:
        """Add a question to a question bank."""
        try:
            async with AsyncSessionLocal() as db:
                # Validate question bank exists
                bank = await db.execute(
                    select(QuestionBank).where(QuestionBank.id == question_data["question_bank_id"])
                )
                if not bank.scalar_one_or_none():
                    raise ValueError(f"Question bank {question_data['question_bank_id']} not found")
                
                # Create question
                question = BankQuestion(
                    question_bank_id=question_data["question_bank_id"],
                    question_text=question_data["question_text"],
                    question_type=question_data["question_type"],
                    points=question_data.get("points", 1.0),
                    options=question_data.get("options"),
                    correct_answers=question_data.get("correct_answers"),
                    difficulty_level=question_data.get("difficulty_level", "medium"),
                    estimated_time_minutes=question_data.get("estimated_time_minutes", 2),
                    tags=question_data.get("tags", []),
                    learning_objective=question_data.get("learning_objective"),
                    bloom_taxonomy_level=question_data.get("bloom_taxonomy_level"),
                    created_by=question_data["created_by"],
                    canvas_question_id=question_data.get("canvas_question_id")
                )
                
                db.add(question)
                await db.commit()
                await db.refresh(question)
                
                logger.info(f"Added question to bank: {question.id} to bank {question.question_bank_id}")
                return question
                
        except Exception as e:
            logger.error(f"Error adding question to bank: {e}")
            raise
    
    async def update_question(self, question_id: int, question_data: Dict[str, Any], user_id: int) -> BankQuestion:
        """Update a question in a bank."""
        try:
            async with AsyncSessionLocal() as db:
                question = await db.execute(
                    select(BankQuestion).where(BankQuestion.id == question_id)
                )
                question_obj = question.scalar_one_or_none()
                
                if not question_obj:
                    raise ValueError(f"Question {question_id} not found")
                
                # Update fields
                update_data = {k: v for k, v in question_data.items() if v is not None}
                update_data["last_modified_by"] = user_id
                update_data["updated_at"] = datetime.utcnow()
                
                await db.execute(
                    update(BankQuestion)
                    .where(BankQuestion.id == question_id)
                    .values(**update_data)
                )
                
                await db.commit()
                await db.refresh(question_obj)
                
                logger.info(f"Updated question {question_id}")
                return question_obj
                
        except Exception as e:
            logger.error(f"Error updating question: {e}")
            raise
    
    async def search_questions(self, search_criteria: Dict[str, Any]) -> List[BankQuestion]:
        """Search questions in banks based on criteria."""
        try:
            async with AsyncSessionLocal() as db:
                query = select(BankQuestion)
                
                # Apply filters
                if "course_id" in search_criteria:
                    query = query.join(QuestionBank).where(QuestionBank.course_id == search_criteria["course_id"])
                
                if "question_bank_id" in search_criteria:
                    query = query.where(BankQuestion.question_bank_id == search_criteria["question_bank_id"])
                
                if "question_type" in search_criteria:
                    query = query.where(BankQuestion.question_type == search_criteria["question_type"])
                
                if "difficulty_level" in search_criteria:
                    query = query.where(BankQuestion.difficulty_level == search_criteria["difficulty_level"])
                
                if "tags" in search_criteria and search_criteria["tags"]:
                    # Search for questions that have any of the specified tags
                    tag_conditions = [
                        BankQuestion.tags.op('?')('$[*]')(tag) for tag in search_criteria["tags"]
                    ]
                    query = query.where(or_(*tag_conditions))
                
                if "text_search" in search_criteria and search_criteria["text_search"]:
                    search_text = f"%{search_criteria['text_search']}%"
                    query = query.where(BankQuestion.question_text.ilike(search_text))
                
                if "point_range" in search_criteria:
                    point_range = search_criteria["point_range"]
                    if "min" in point_range:
                        query = query.where(BankQuestion.points >= point_range["min"])
                    if "max" in point_range:
                        query = query.where(BankQuestion.points <= point_range["max"])
                
                # Order by relevance (usage count, quality, recency)
                query = query.order_by(
                    desc(BankQuestion.usage_count),
                    desc(BankQuestion.quality_score),
                    desc(BankQuestion.created_at)
                ).limit(100)
                
                result = await db.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Error searching questions: {e}")
            return []
    
    async def get_question_statistics(self, question_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a question."""
        try:
            async with AsyncSessionLocal() as db:
                # Get question details
                question = await db.execute(
                    select(BankQuestion).where(BankQuestion.id == question_id)
                )
                question_obj = question.scalar_one_or_none()
                
                if not question_obj:
                    raise ValueError(f"Question {question_id} not found")
                
                # Get response statistics
                response_stats = await db.execute(
                    select(
                        func.count(QuestionResponse.id).label('total_responses'),
                        func.count(QuestionResponse.id).filter(QuestionResponse.is_correct == True).label('correct_responses'),
                        func.avg(QuestionResponse.points_earned).label('avg_points'),
                        func.avg(QuestionResponse.time_spent_seconds).label('avg_time')
                    ).where(QuestionResponse.question_id == question_id)
                )
                
                stats = response_stats.fetchone()
                
                # Calculate derived metrics
                total_responses = stats.total_responses or 0
                correct_responses = stats.correct_responses or 0
                difficulty_index = (correct_responses / total_responses) if total_responses > 0 else None
                
                # Get usage statistics
                usage_stats = await db.execute(
                    select(
                        func.count(QuestionUsageLog.id).label('usage_count'),
                        func.count(func.distinct(QuestionUsageLog.quiz_id)).label('unique_quizzes')
                    ).where(QuestionUsageLog.question_id == question_id)
                )
                
                usage = usage_stats.fetchone()
                
                return {
                    "question_id": question_id,
                    "question_type": question_obj.question_type,
                    "difficulty_level": question_obj.difficulty_level,
                    "points": question_obj.points,
                    "usage_statistics": {
                        "total_responses": total_responses,
                        "correct_responses": correct_responses,
                        "difficulty_index": difficulty_index,
                        "average_points": float(stats.avg_points or 0),
                        "average_time_seconds": float(stats.avg_time or 0),
                        "usage_count": usage.usage_count or 0,
                        "unique_quizzes": usage.unique_quizzes or 0
                    },
                    "quality_metrics": {
                        "discrimination_index": question_obj.discrimination_index,
                        "point_biserial_correlation": question_obj.point_biserial_correlation,
                        "needs_review": question_obj.needs_review,
                        "review_reason": question_obj.review_reason
                    },
                    "last_analyzed": question_obj.last_analyzed.isoformat() if question_obj.last_analyzed else None
                }
                
        except Exception as e:
            logger.error(f"Error getting question statistics: {e}")
            raise


class ItemAnalysisService:
    """Service for performing item analysis on questions."""
    
    async def analyze_question(self, question_id: int, quiz_id: Optional[int] = None) -> ItemAnalysis:
        """Perform comprehensive item analysis on a question."""
        try:
            async with AsyncSessionLocal() as db:
                # Get question responses
                query = select(QuestionResponse).where(QuestionResponse.question_id == question_id)
                if quiz_id:
                    query = query.where(QuestionResponse.quiz_submission_id.in_(
                        select(QuizSubmission.id).where(QuizSubmission.quiz_id == quiz_id)
                    ))
                
                responses = await db.execute(query)
                response_list = responses.scalars().all()
                
                if len(response_list) < 10:  # Minimum sample size
                    logger.warning(f"Insufficient responses for reliable analysis: {len(response_list)}")
                
                # Perform analysis
                analysis_results = self._calculate_item_statistics(response_list)
                
                # Create or update analysis record
                existing_analysis = await db.execute(
                    select(ItemAnalysis).where(
                        and_(
                            ItemAnalysis.question_id == question_id,
                            ItemAnalysis.quiz_id == quiz_id
                        )
                    )
                )
                
                analysis_obj = existing_analysis.scalar_one_or_none()
                
                if analysis_obj:
                    # Update existing analysis
                    await db.execute(
                        update(ItemAnalysis)
                        .where(ItemAnalysis.id == analysis_obj.id)
                        .values(**analysis_results, updated_at=datetime.utcnow())
                    )
                    await db.refresh(analysis_obj)
                else:
                    # Create new analysis
                    analysis_obj = ItemAnalysis(
                        question_id=question_id,
                        quiz_id=quiz_id,
                        **analysis_results
                    )
                    db.add(analysis_obj)
                
                await db.commit()
                
                # Update question statistics
                await self._update_question_statistics(db, question_id, analysis_results)
                
                logger.info(f"Completed item analysis for question {question_id}")
                return analysis_obj
                
        except Exception as e:
            logger.error(f"Error analyzing question: {e}")
            raise
    
    def _calculate_item_statistics(self, responses: List[QuestionResponse]) -> Dict[str, Any]:
        """Calculate classical test theory statistics for a question."""
        if not responses:
            return {
                "sample_size": 0,
                "difficulty_index": None,
                "discrimination_index": None,
                "point_biserial_correlation": None,
                "quality_score": 0,
                "recommendation": "insufficient_data"
            }
        
        sample_size = len(responses)
        correct_responses = sum(1 for r in responses if r.is_correct)
        
        # Difficulty Index (P-value)
        difficulty_index = correct_responses / sample_size
        
        # For discrimination analysis, we need total scores
        # This is a simplified version - in practice, you'd use total quiz scores
        total_scores = [r.points_earned for r in responses]
        
        # Sort by total score and split into high/low groups
        sorted_responses = sorted(responses, key=lambda r: r.points_earned, reverse=True)
        group_size = max(1, sample_size // 3)  # Top and bottom 27%
        
        high_group = sorted_responses[:group_size]
        low_group = sorted_responses[-group_size:]
        
        # Discrimination Index (D-value)
        high_correct = sum(1 for r in high_group if r.is_correct)
        low_correct = sum(1 for r in low_group if r.is_correct)
        
        discrimination_index = (high_correct / len(high_group)) - (low_correct / len(low_group))
        
        # Point-biserial correlation (simplified)
        if len(set(total_scores)) > 1:  # Need variance in scores
            correct_scores = [r.points_earned for r in responses if r.is_correct]
            incorrect_scores = [r.points_earned for r in responses if not r.is_correct]
            
            if correct_scores and incorrect_scores:
                mean_correct = statistics.mean(correct_scores)
                mean_incorrect = statistics.mean(incorrect_scores)
                overall_std = statistics.stdev(total_scores)
                
                point_biserial = ((mean_correct - mean_incorrect) / overall_std) * \
                               (correct_responses / sample_size * (1 - correct_responses / sample_size)) ** 0.5
            else:
                point_biserial = 0
        else:
            point_biserial = 0
        
        # Quality assessment
        quality_score, quality_flags, recommendation = self._assess_question_quality(
            difficulty_index, discrimination_index, point_biserial, sample_size
        )
        
        # Distractor analysis (for multiple choice)
        distractor_analysis = self._analyze_distractors(responses)
        
        return {
            "sample_size": sample_size,
            "difficulty_index": difficulty_index,
            "discrimination_index": discrimination_index,
            "point_biserial_correlation": point_biserial,
            "quality_score": quality_score,
            "quality_flags": quality_flags,
            "recommendation": recommendation,
            "distractor_analysis": distractor_analysis,
            "analysis_date": datetime.utcnow()
        }
    
    def _assess_question_quality(self, difficulty: float, discrimination: float, 
                               correlation: float, sample_size: int) -> Tuple[float, List[str], str]:
        """Assess overall question quality and provide recommendations."""
        quality_flags = []
        quality_score = 100
        
        # Difficulty assessment
        if difficulty < 0.2:
            quality_flags.append("too_difficult")
            quality_score -= 20
        elif difficulty > 0.9:
            quality_flags.append("too_easy")
            quality_score -= 15
        elif 0.3 <= difficulty <= 0.7:
            quality_score += 10  # Ideal difficulty range
        
        # Discrimination assessment
        if discrimination < 0.2:
            quality_flags.append("poor_discrimination")
            quality_score -= 25
        elif discrimination < 0.3:
            quality_flags.append("fair_discrimination")
            quality_score -= 10
        elif discrimination >= 0.4:
            quality_score += 15  # Good discrimination
        
        # Point-biserial correlation
        if correlation < 0.2:
            quality_flags.append("low_correlation")
            quality_score -= 20
        elif correlation >= 0.3:
            quality_score += 10
        
        # Sample size consideration
        if sample_size < 30:
            quality_flags.append("small_sample")
            quality_score -= 10
        
        # Determine recommendation
        if quality_score >= 80:
            recommendation = "keep"
        elif quality_score >= 60:
            recommendation = "revise"
        else:
            recommendation = "discard"
        
        return max(0, quality_score), quality_flags, recommendation
    
    def _analyze_distractors(self, responses: List[QuestionResponse]) -> Dict[str, Any]:
        """Analyze distractor effectiveness for multiple choice questions."""
        if not responses:
            return {}
        
        # Count selections for each option
        option_counts = defaultdict(int)
        total_responses = len(responses)
        
        for response in responses:
            if response.selected_options:
                try:
                    selected = json.loads(response.selected_options) if isinstance(response.selected_options, str) else response.selected_options
                    if isinstance(selected, list):
                        for option in selected:
                            option_counts[str(option)] += 1
                    else:
                        option_counts[str(selected)] += 1
                except (json.JSONDecodeError, TypeError):
                    continue
        
        # Calculate percentages and effectiveness
        distractor_stats = {}
        for option, count in option_counts.items():
            percentage = (count / total_responses) * 100
            distractor_stats[option] = {
                "count": count,
                "percentage": round(percentage, 1),
                "is_effective": 5 <= percentage <= 25  # Good distractors attract 5-25% of responses
            }
        
        return {
            "option_statistics": distractor_stats,
            "total_responses": total_responses,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    async def _update_question_statistics(self, db: AsyncSession, question_id: int, analysis: Dict[str, Any]):
        """Update question statistics based on analysis results."""
        try:
            needs_review = analysis["recommendation"] in ["revise", "discard"]
            review_reason = ", ".join(analysis["quality_flags"]) if analysis["quality_flags"] else None
            
            await db.execute(
                update(BankQuestion)
                .where(BankQuestion.id == question_id)
                .values(
                    difficulty_index=analysis["difficulty_index"],
                    discrimination_index=analysis["discrimination_index"],
                    point_biserial_correlation=analysis["point_biserial_correlation"],
                    needs_review=needs_review,
                    review_reason=review_reason,
                    last_analyzed=datetime.utcnow()
                )
            )
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error updating question statistics: {e}")
    
    async def bulk_analyze_questions(self, question_ids: List[int], quiz_id: Optional[int] = None) -> List[ItemAnalysis]:
        """Perform bulk item analysis on multiple questions."""
        try:
            analyses = []
            
            for question_id in question_ids:
                try:
                    analysis = await self.analyze_question(question_id, quiz_id)
                    analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Error analyzing question {question_id}: {e}")
                    continue
            
            logger.info(f"Completed bulk analysis of {len(analyses)} questions")
            return analyses
            
        except Exception as e:
            logger.error(f"Error in bulk analysis: {e}")
            return []
    
    async def get_analysis_report(self, course_id: int, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Generate comprehensive item analysis report for a course."""
        try:
            async with AsyncSessionLocal() as db:
                # Build base query
                query = (
                    select(ItemAnalysis)
                    .join(BankQuestion, ItemAnalysis.question_id == BankQuestion.id)
                    .join(QuestionBank, BankQuestion.question_bank_id == QuestionBank.id)
                    .where(QuestionBank.course_id == course_id)
                )
                
                if date_range:
                    start_date, end_date = date_range
                    query = query.where(
                        ItemAnalysis.analysis_date.between(start_date, end_date)
                    )
                
                analyses = await db.execute(query)
                analysis_list = analyses.scalars().all()
                
                if not analysis_list:
                    return {
                        "course_id": course_id,
                        "total_questions": 0,
                        "summary": {},
                        "recommendations": []
                    }
                
                # Calculate summary statistics
                difficulties = [a.difficulty_index for a in analysis_list if a.difficulty_index is not None]
                discriminations = [a.discrimination_index for a in analysis_list if a.discrimination_index is not None]
                correlations = [a.point_biserial_correlation for a in analysis_list if a.point_biserial_correlation is not None]
                
                # Count recommendations
                recommendations = defaultdict(int)
                for analysis in analysis_list:
                    recommendations[analysis.recommendation] += 1
                
                # Identify problem questions
                problem_questions = [
                    {
                        "question_id": a.question_id,
                        "difficulty_index": a.difficulty_index,
                        "discrimination_index": a.discrimination_index,
                        "quality_flags": a.quality_flags,
                        "recommendation": a.recommendation
                    }
                    for a in analysis_list
                    if a.recommendation in ["revise", "discard"]
                ]
                
                return {
                    "course_id": course_id,
                    "total_questions": len(analysis_list),
                    "date_range": {
                        "start": date_range[0].isoformat() if date_range else None,
                        "end": date_range[1].isoformat() if date_range else None
                    },
                    "summary": {
                        "average_difficulty": statistics.mean(difficulties) if difficulties else 0,
                        "average_discrimination": statistics.mean(discriminations) if discriminations else 0,
                        "average_correlation": statistics.mean(correlations) if correlations else 0,
                        "difficulty_distribution": {
                            "very_easy": len([d for d in difficulties if d > 0.8]),
                            "easy": len([d for d in difficulties if 0.7 < d <= 0.8]),
                            "medium": len([d for d in difficulties if 0.3 <= d <= 0.7]),
                            "hard": len([d for d in difficulties if 0.2 <= d < 0.3]),
                            "very_hard": len([d for d in difficulties if d < 0.2])
                        }
                    },
                    "recommendations": dict(recommendations),
                    "problem_questions": problem_questions[:20],  # Top 20 problem questions
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating analysis report: {e}")
            raise


# Global service instances
question_bank_service = QuestionBankService()
item_analysis_service = ItemAnalysisService()
