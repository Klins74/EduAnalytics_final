"""
LTI Assignment and Grade Services (AGS) implementation.

Handles grade passback to LTI platforms (Canvas) according to LTI 1.3 AGS specification.
"""

import logging
import json
import jwt
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from decimal import Decimal

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_

from app.db.session import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LineItem:
    """LTI Line Item representation."""
    id: str
    scoreMaximum: float
    label: str
    resourceId: Optional[str] = None
    resourceLinkId: Optional[str] = None
    tag: Optional[str] = None
    startDateTime: Optional[str] = None
    endDateTime: Optional[str] = None
    submissionReview: Optional[Dict[str, Any]] = None


@dataclass
class Score:
    """LTI Score representation."""
    userId: str
    scoreGiven: Optional[float] = None
    scoreMaximum: Optional[float] = None
    comment: Optional[str] = None
    timestamp: Optional[str] = None
    activityProgress: Optional[str] = None  # Initialized, InProgress, Submitted, Completed
    gradingProgress: Optional[str] = None   # FullyGraded, Pending, PendingManual, Failed, NotReady


@dataclass
class Result:
    """LTI Result representation."""
    id: str
    userId: str
    resultScore: Optional[float] = None
    resultMaximum: Optional[float] = None
    comment: Optional[str] = None
    scoreOf: Optional[str] = None  # Line item URL


@dataclass
class AGSEndpoints:
    """AGS service endpoints."""
    lineitems: str
    lineitem: Optional[str] = None


class LTIAGSService:
    """LTI Assignment and Grade Services implementation."""
    
    def __init__(self, lti_service):
        self.lti_service = lti_service
        self.client_timeout = 30.0
    
    async def get_access_token(self, platform_id: str, scopes: List[str]) -> str:
        """Get access token for AGS operations."""
        try:
            platform = self.lti_service.platforms.get(platform_id)
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown platform: {platform_id}"
                )
            
            # Create JWT for client credentials grant
            now = int(time.time())
            jwt_payload = {
                'iss': platform.client_id,
                'sub': platform.client_id,
                'aud': platform.auth_token_url,
                'iat': now,
                'exp': now + 300,  # 5 minutes
                'jti': str(uuid.uuid4())
            }
            
            # Sign with our private key
            client_assertion = jwt.encode(
                jwt_payload,
                self.lti_service.private_key,
                algorithm='RS256',
                headers={'kid': self.lti_service.key_id}
            )
            
            # Request access token
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                token_data = {
                    'grant_type': 'client_credentials',
                    'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                    'client_assertion': client_assertion,
                    'scope': ' '.join(scopes)
                }
                
                response = await client.post(
                    platform.auth_token_url,
                    data=token_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                response.raise_for_status()
                
                token_response = response.json()
                return token_response.get('access_token')
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get access token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Access token request failed: {str(e)}"
            )
    
    async def get_line_items(self, platform_id: str, context_id: str, 
                           resource_link_id: Optional[str] = None) -> List[LineItem]:
        """Get line items from platform."""
        try:
            # Get access token with line item scope
            access_token = await self.get_access_token(
                platform_id, 
                ['https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly']
            )
            
            # Build line items URL
            lineitems_url = f"{platform_id}/api/lti/courses/{context_id}/line_items"
            
            params = {}
            if resource_link_id:
                params['resource_link_id'] = resource_link_id
            
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.get(
                    lineitems_url,
                    params=params,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                
                line_items_data = response.json()
                
                line_items = []
                for item_data in line_items_data:
                    line_item = LineItem(
                        id=item_data.get('id', ''),
                        scoreMaximum=float(item_data.get('scoreMaximum', 100)),
                        label=item_data.get('label', ''),
                        resourceId=item_data.get('resourceId'),
                        resourceLinkId=item_data.get('resourceLinkId'),
                        tag=item_data.get('tag'),
                        startDateTime=item_data.get('startDateTime'),
                        endDateTime=item_data.get('endDateTime'),
                        submissionReview=item_data.get('submissionReview')
                    )
                    line_items.append(line_item)
                
                return line_items
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting line items: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get line items: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error getting line items: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Get line items failed: {str(e)}"
            )
    
    async def create_line_item(self, platform_id: str, context_id: str, 
                             line_item: LineItem) -> LineItem:
        """Create a new line item on the platform."""
        try:
            # Get access token with line item scope
            access_token = await self.get_access_token(
                platform_id, 
                ['https://purl.imsglobal.org/spec/lti-ags/scope/lineitem']
            )
            
            # Build line items URL
            lineitems_url = f"{platform_id}/api/lti/courses/{context_id}/line_items"
            
            # Prepare line item data
            line_item_data = {
                'scoreMaximum': line_item.scoreMaximum,
                'label': line_item.label
            }
            
            if line_item.resourceId:
                line_item_data['resourceId'] = line_item.resourceId
            if line_item.resourceLinkId:
                line_item_data['resourceLinkId'] = line_item.resourceLinkId
            if line_item.tag:
                line_item_data['tag'] = line_item.tag
            if line_item.startDateTime:
                line_item_data['startDateTime'] = line_item.startDateTime
            if line_item.endDateTime:
                line_item_data['endDateTime'] = line_item.endDateTime
            if line_item.submissionReview:
                line_item_data['submissionReview'] = line_item.submissionReview
            
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.post(
                    lineitems_url,
                    json=line_item_data,
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/vnd.ims.lis.v2.lineitem+json'
                    }
                )
                response.raise_for_status()
                
                created_item_data = response.json()
                
                return LineItem(
                    id=created_item_data.get('id', ''),
                    scoreMaximum=float(created_item_data.get('scoreMaximum', line_item.scoreMaximum)),
                    label=created_item_data.get('label', line_item.label),
                    resourceId=created_item_data.get('resourceId'),
                    resourceLinkId=created_item_data.get('resourceLinkId'),
                    tag=created_item_data.get('tag'),
                    startDateTime=created_item_data.get('startDateTime'),
                    endDateTime=created_item_data.get('endDateTime'),
                    submissionReview=created_item_data.get('submissionReview')
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating line item: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create line item: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating line item: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Create line item failed: {str(e)}"
            )
    
    async def submit_score(self, platform_id: str, line_item_url: str, 
                         score: Score) -> bool:
        """Submit a score to the platform."""
        try:
            # Get access token with score scope
            access_token = await self.get_access_token(
                platform_id, 
                ['https://purl.imsglobal.org/spec/lti-ags/scope/score']
            )
            
            # Build scores URL
            scores_url = f"{line_item_url}/scores"
            
            # Prepare score data
            score_data = {
                'userId': score.userId,
                'timestamp': score.timestamp or datetime.utcnow().isoformat()
            }
            
            if score.scoreGiven is not None:
                score_data['scoreGiven'] = score.scoreGiven
            if score.scoreMaximum is not None:
                score_data['scoreMaximum'] = score.scoreMaximum
            if score.comment:
                score_data['comment'] = score.comment
            if score.activityProgress:
                score_data['activityProgress'] = score.activityProgress
            if score.gradingProgress:
                score_data['gradingProgress'] = score.gradingProgress
            
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.post(
                    scores_url,
                    json=score_data,
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/vnd.ims.lis.v1.score+json'
                    }
                )
                response.raise_for_status()
                
                logger.info(f"Score submitted successfully for user {score.userId}")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error submitting score: {e}")
            if e.response:
                logger.error(f"Response content: {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to submit score: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error submitting score: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Submit score failed: {str(e)}"
            )
    
    async def get_results(self, platform_id: str, line_item_url: str, 
                        user_id: Optional[str] = None) -> List[Result]:
        """Get results from the platform."""
        try:
            # Get access token with result scope
            access_token = await self.get_access_token(
                platform_id, 
                ['https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly']
            )
            
            # Build results URL
            results_url = f"{line_item_url}/results"
            
            params = {}
            if user_id:
                params['user_id'] = user_id
            
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.get(
                    results_url,
                    params=params,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                
                results_data = response.json()
                
                results = []
                for result_data in results_data:
                    result = Result(
                        id=result_data.get('id', ''),
                        userId=result_data.get('userId', ''),
                        resultScore=result_data.get('resultScore'),
                        resultMaximum=result_data.get('resultMaximum'),
                        comment=result_data.get('comment'),
                        scoreOf=result_data.get('scoreOf')
                    )
                    results.append(result)
                
                return results
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting results: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get results: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error getting results: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Get results failed: {str(e)}"
            )
    
    async def sync_grade_to_platform(self, platform_id: str, context_id: str,
                                   assignment_id: int, student_id: int, 
                                   score: float, max_score: float,
                                   comment: Optional[str] = None) -> bool:
        """Sync grade from our system to the platform."""
        try:
            async with AsyncSessionLocal() as db:
                # Get assignment and student information
                assignment_query = """
                SELECT a.id, a.title, a.lti_resource_link_id, a.lti_line_item_url
                FROM assignments a
                WHERE a.id = :assignment_id
                """
                
                result = await db.execute(text(assignment_query), {"assignment_id": assignment_id})
                assignment = result.fetchone()
                
                if not assignment:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assignment not found"
                    )
                
                # Get student LTI user ID
                student_query = """
                SELECT u.id, u.lti_user_id
                FROM users u
                WHERE u.id = :student_id
                """
                
                result = await db.execute(text(student_query), {"student_id": student_id})
                student = result.fetchone()
                
                if not student or not student.lti_user_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Student not found or missing LTI user ID"
                    )
                
                # Check if we have a line item URL
                line_item_url = assignment.lti_line_item_url
                
                if not line_item_url:
                    # Create line item if it doesn't exist
                    line_item = LineItem(
                        id="",  # Will be set by platform
                        scoreMaximum=max_score,
                        label=assignment.title,
                        resourceId=f"assignment-{assignment_id}",
                        resourceLinkId=assignment.lti_resource_link_id
                    )
                    
                    created_line_item = await self.create_line_item(
                        platform_id, context_id, line_item
                    )
                    line_item_url = created_line_item.id
                    
                    # Update assignment with line item URL
                    update_query = """
                    UPDATE assignments 
                    SET lti_line_item_url = :line_item_url 
                    WHERE id = :assignment_id
                    """
                    await db.execute(text(update_query), {
                        "line_item_url": line_item_url,
                        "assignment_id": assignment_id
                    })
                    await db.commit()
                
                # Submit score
                score_obj = Score(
                    userId=student.lti_user_id,
                    scoreGiven=score,
                    scoreMaximum=max_score,
                    comment=comment,
                    activityProgress="Completed",
                    gradingProgress="FullyGraded",
                    timestamp=datetime.utcnow().isoformat()
                )
                
                success = await self.submit_score(platform_id, line_item_url, score_obj)
                
                if success:
                    # Log the grade sync
                    await self._log_grade_sync(
                        db, platform_id, assignment_id, student_id, 
                        score, max_score, line_item_url, "success"
                    )
                
                return success
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error syncing grade to platform: {e}")
            # Log the failed sync
            try:
                async with AsyncSessionLocal() as db:
                    await self._log_grade_sync(
                        db, platform_id, assignment_id, student_id,
                        score, max_score, "", "failed", str(e)
                    )
            except:
                pass
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Grade sync failed: {str(e)}"
            )
    
    async def bulk_sync_grades(self, platform_id: str, context_id: str,
                             assignment_id: int) -> Dict[str, Any]:
        """Sync all grades for an assignment to the platform."""
        try:
            async with AsyncSessionLocal() as db:
                # Get all submissions for the assignment
                submissions_query = """
                SELECT s.id, s.student_id, s.score, s.max_score, 
                       u.lti_user_id, a.title, a.lti_line_item_url
                FROM submissions s
                JOIN users u ON s.student_id = u.id
                JOIN assignments a ON s.assignment_id = a.id
                WHERE s.assignment_id = :assignment_id
                AND s.score IS NOT NULL
                AND u.lti_user_id IS NOT NULL
                """
                
                result = await db.execute(text(submissions_query), {"assignment_id": assignment_id})
                submissions = result.fetchall()
                
                if not submissions:
                    return {
                        "success": True,
                        "message": "No submissions found to sync",
                        "synced_count": 0,
                        "failed_count": 0
                    }
                
                # Get line item URL from first submission
                line_item_url = submissions[0].lti_line_item_url
                
                if not line_item_url:
                    # Create line item
                    line_item = LineItem(
                        id="",
                        scoreMaximum=submissions[0].max_score,
                        label=submissions[0].title,
                        resourceId=f"assignment-{assignment_id}"
                    )
                    
                    created_line_item = await self.create_line_item(
                        platform_id, context_id, line_item
                    )
                    line_item_url = created_line_item.id
                    
                    # Update assignment
                    update_query = """
                    UPDATE assignments 
                    SET lti_line_item_url = :line_item_url 
                    WHERE id = :assignment_id
                    """
                    await db.execute(text(update_query), {
                        "line_item_url": line_item_url,
                        "assignment_id": assignment_id
                    })
                    await db.commit()
                
                # Sync each grade
                synced_count = 0
                failed_count = 0
                failed_users = []
                
                for submission in submissions:
                    try:
                        score_obj = Score(
                            userId=submission.lti_user_id,
                            scoreGiven=float(submission.score),
                            scoreMaximum=float(submission.max_score),
                            activityProgress="Completed",
                            gradingProgress="FullyGraded",
                            timestamp=datetime.utcnow().isoformat()
                        )
                        
                        success = await self.submit_score(platform_id, line_item_url, score_obj)
                        
                        if success:
                            synced_count += 1
                            await self._log_grade_sync(
                                db, platform_id, assignment_id, submission.student_id,
                                submission.score, submission.max_score, 
                                line_item_url, "success"
                            )
                        else:
                            failed_count += 1
                            failed_users.append(submission.lti_user_id)
                            
                    except Exception as e:
                        logger.error(f"Failed to sync grade for user {submission.lti_user_id}: {e}")
                        failed_count += 1
                        failed_users.append(submission.lti_user_id)
                        
                        await self._log_grade_sync(
                            db, platform_id, assignment_id, submission.student_id,
                            submission.score, submission.max_score,
                            line_item_url, "failed", str(e)
                        )
                
                await db.commit()
                
                return {
                    "success": True,
                    "message": f"Bulk grade sync completed",
                    "synced_count": synced_count,
                    "failed_count": failed_count,
                    "failed_users": failed_users,
                    "total_submissions": len(submissions)
                }
                
        except Exception as e:
            logger.error(f"Error in bulk grade sync: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk grade sync failed: {str(e)}"
            )
    
    async def _log_grade_sync(self, db: AsyncSession, platform_id: str,
                            assignment_id: int, student_id: int,
                            score: float, max_score: float,
                            line_item_url: str, status: str,
                            error_message: Optional[str] = None):
        """Log grade sync operation."""
        try:
            # Create grade sync logs table if not exists
            await self._create_grade_sync_table(db)
            
            insert_sql = """
            INSERT INTO lti_grade_sync_log (
                sync_id, platform_id, assignment_id, student_id,
                score, max_score, line_item_url, status, error_message,
                synced_at
            ) VALUES (
                :sync_id, :platform_id, :assignment_id, :student_id,
                :score, :max_score, :line_item_url, :status, :error_message,
                :synced_at
            )
            """
            
            await db.execute(text(insert_sql), {
                "sync_id": str(uuid.uuid4()),
                "platform_id": platform_id,
                "assignment_id": assignment_id,
                "student_id": student_id,
                "score": score,
                "max_score": max_score,
                "line_item_url": line_item_url,
                "status": status,
                "error_message": error_message,
                "synced_at": datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error logging grade sync: {e}")
    
    async def _create_grade_sync_table(self, db: AsyncSession):
        """Create grade sync log table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS lti_grade_sync_log (
            sync_id VARCHAR(36) PRIMARY KEY,
            platform_id VARCHAR(255) NOT NULL,
            assignment_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            score DECIMAL(10,2) NOT NULL,
            max_score DECIMAL(10,2) NOT NULL,
            line_item_url TEXT NOT NULL,
            status VARCHAR(20) NOT NULL,
            error_message TEXT,
            synced_at TIMESTAMP WITH TIME ZONE NOT NULL,
            FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_grade_sync_assignment ON lti_grade_sync_log(assignment_id);
        CREATE INDEX IF NOT EXISTS idx_grade_sync_student ON lti_grade_sync_log(student_id);
        CREATE INDEX IF NOT EXISTS idx_grade_sync_status ON lti_grade_sync_log(status);
        CREATE INDEX IF NOT EXISTS idx_grade_sync_synced_at ON lti_grade_sync_log(synced_at);
        """
        
        await db.execute(text(create_table_sql))
    
    async def get_sync_history(self, assignment_id: Optional[int] = None,
                             student_id: Optional[int] = None,
                             days: int = 7) -> List[Dict[str, Any]]:
        """Get grade sync history."""
        try:
            async with AsyncSessionLocal() as db:
                await self._create_grade_sync_table(db)
                
                conditions = ["synced_at >= NOW() - INTERVAL '%s days'" % days]
                params = {}
                
                if assignment_id:
                    conditions.append("assignment_id = :assignment_id")
                    params["assignment_id"] = assignment_id
                
                if student_id:
                    conditions.append("student_id = :student_id")
                    params["student_id"] = student_id
                
                where_clause = " AND ".join(conditions)
                
                query = f"""
                SELECT 
                    gsl.sync_id, gsl.platform_id, gsl.assignment_id, gsl.student_id,
                    gsl.score, gsl.max_score, gsl.status, gsl.error_message, gsl.synced_at,
                    a.title as assignment_title,
                    u.name as student_name
                FROM lti_grade_sync_log gsl
                LEFT JOIN assignments a ON gsl.assignment_id = a.id
                LEFT JOIN users u ON gsl.student_id = u.id
                WHERE {where_clause}
                ORDER BY gsl.synced_at DESC
                LIMIT 1000
                """
                
                result = await db.execute(text(query), params)
                
                return [
                    {
                        "sync_id": row.sync_id,
                        "platform_id": row.platform_id,
                        "assignment_id": row.assignment_id,
                        "assignment_title": row.assignment_title,
                        "student_id": row.student_id,
                        "student_name": row.student_name,
                        "score": float(row.score) if row.score else None,
                        "max_score": float(row.max_score) if row.max_score else None,
                        "status": row.status,
                        "error_message": row.error_message,
                        "synced_at": row.synced_at.isoformat()
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting sync history: {e}")
            return []


# Global AGS service instance (will be initialized with LTI service)
lti_ags_service = None

def get_lti_ags_service():
    """Get the global LTI AGS service instance."""
    global lti_ags_service
    if not lti_ags_service:
        from app.services.lti_service import lti_service
        lti_ags_service = LTIAGSService(lti_service)
    return lti_ags_service
