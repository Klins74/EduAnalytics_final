"""
Permission-aware search service for RAG system.

Ensures users can only access content they have permissions to view.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.user import User, UserRole
from app.models.enrollment import Enrollment, EnrollmentRole
from app.models.course import Course
from app.models.assignment import Assignment
from app.services.rag_indexer import rag_indexer

logger = logging.getLogger(__name__)


class PermissionAwareSearchService:
    """Service for permission-aware content search using RAG."""
    
    def __init__(self):
        self.rag_indexer = rag_indexer
    
    async def search_with_permissions(
        self,
        query: str,
        user_id: int,
        db: AsyncSession,
        top_k: int = 5,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search content with permission filtering.
        
        Args:
            query: Search query
            user_id: User ID requesting the search
            db: Database session
            top_k: Maximum number of results
            content_types: Filter by content types
            
        Returns:
            List of search results user has permission to access
        """
        try:
            # Get user and their permissions
            user_permissions = await self._get_user_permissions(user_id, db)
            if not user_permissions:
                return []
            
            # Perform initial RAG search
            all_results = []
            
            # If user has access to specific courses, search within those
            if user_permissions['accessible_course_ids']:
                for course_id in user_permissions['accessible_course_ids']:
                    course_results = self.rag_indexer.search(
                        query=query,
                        top_k=top_k * 2,  # Get more to allow for filtering
                        course_id=course_id,
                        content_type=None  # Will filter by type later
                    )
                    all_results.extend(course_results)
            
            # If user is admin/teacher, also search global content
            if user_permissions['is_admin'] or user_permissions['is_global_teacher']:
                global_results = self.rag_indexer.search(
                    query=query,
                    top_k=top_k * 2
                )
                all_results.extend(global_results)
            
            # Filter results by permissions
            filtered_results = []
            seen_doc_ids = set()
            
            for result in all_results:
                doc_id = result['doc_id']
                if doc_id in seen_doc_ids:
                    continue
                seen_doc_ids.add(doc_id)
                
                # Check if user has permission to access this content
                if await self._can_access_content(result, user_permissions, db):
                    # Filter by content type if specified
                    if content_types:
                        content_type = result['metadata'].get('type')
                        if content_type not in content_types:
                            continue
                    
                    filtered_results.append(result)
                    
                    if len(filtered_results) >= top_k:
                        break
            
            # Sort by relevance score
            filtered_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Add permission context to results
            for result in filtered_results:
                result['access_level'] = await self._get_content_access_level(
                    result, user_permissions, db
                )
            
            logger.info(f"Permission-aware search for user {user_id}: {len(filtered_results)} results")
            return filtered_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in permission-aware search: {e}")
            return []
    
    async def _get_user_permissions(
        self, 
        user_id: int, 
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get user's permissions and accessible content."""
        try:
            # Get user
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return None
            
            permissions = {
                'user_id': user_id,
                'user_role': user.role,
                'is_admin': user.role == UserRole.admin,
                'is_global_teacher': user.role == UserRole.teacher,
                'accessible_course_ids': set(),
                'course_roles': {},  # course_id -> role
                'owned_course_ids': set()
            }
            
            # If admin, has access to everything
            if user.role == UserRole.admin:
                # Get all course IDs
                courses_result = await db.execute(select(Course.id))
                all_course_ids = [row[0] for row in courses_result.fetchall()]
                permissions['accessible_course_ids'] = set(all_course_ids)
                permissions['course_roles'] = {cid: 'admin' for cid in all_course_ids}
                return permissions
            
            # Get enrollments for student/teacher
            enrollments_result = await db.execute(
                select(Enrollment).where(
                    and_(
                        Enrollment.user_id == user_id,
                        Enrollment.status == 'active'
                    )
                )
            )
            enrollments = enrollments_result.scalars().all()
            
            for enrollment in enrollments:
                course_id = enrollment.course_id
                permissions['accessible_course_ids'].add(course_id)
                permissions['course_roles'][course_id] = enrollment.role
                
                # If user is teacher in this course, they "own" it
                if enrollment.role in ['teacher', 'ta']:
                    permissions['owned_course_ids'].add(course_id)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return None
    
    async def _can_access_content(
        self,
        search_result: Dict[str, Any],
        user_permissions: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """Check if user can access specific content."""
        try:
            metadata = search_result['metadata']
            content_type = metadata.get('type')
            course_id = metadata.get('course_id')
            
            # Admin can access everything
            if user_permissions['is_admin']:
                return True
            
            # Check course-level access
            if course_id:
                if course_id not in user_permissions['accessible_course_ids']:
                    return False
                
                user_role_in_course = user_permissions['course_roles'].get(course_id)
                
                # Additional permission checks based on content type
                if content_type == 'assignment':
                    # Check if assignment is published
                    assignment_id = metadata.get('assignment_id')
                    if assignment_id:
                        return await self._is_assignment_accessible(
                            assignment_id, user_role_in_course, db
                        )
                
                elif content_type == 'quiz':
                    # Check if quiz is available
                    quiz_id = metadata.get('quiz_id')
                    if quiz_id:
                        return await self._is_quiz_accessible(
                            quiz_id, user_role_in_course, db
                        )
                
                elif content_type == 'discussion':
                    # Most discussions are accessible to enrolled users
                    return True
                
                elif content_type == 'page':
                    # Check if page is published
                    page_id = metadata.get('page_id')
                    if page_id:
                        return await self._is_page_accessible(
                            page_id, user_role_in_course, db
                        )
                
                # Default: allow access if enrolled in course
                return True
            
            # Global content (no course_id)
            # Only teachers and admins can see global content
            return user_permissions['is_global_teacher'] or user_permissions['is_admin']
            
        except Exception as e:
            logger.error(f"Error checking content access: {e}")
            return False
    
    async def _is_assignment_accessible(
        self,
        assignment_id: int,
        user_role: str,
        db: AsyncSession
    ) -> bool:
        """Check if assignment is accessible to user."""
        try:
            assignment_result = await db.execute(
                select(Assignment).where(Assignment.id == assignment_id)
            )
            assignment = assignment_result.scalar_one_or_none()
            
            if not assignment:
                return False
            
            # Teachers can always access
            if user_role in ['teacher', 'ta']:
                return True
            
            # Students can access if published and not hidden
            if hasattr(assignment, 'published') and not assignment.published:
                return False
            
            if hasattr(assignment, 'hidden') and assignment.hidden:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking assignment access: {e}")
            return False
    
    async def _is_quiz_accessible(
        self,
        quiz_id: int,
        user_role: str,
        db: AsyncSession
    ) -> bool:
        """Check if quiz is accessible to user."""
        try:
            from app.models.quiz import Quiz
            
            quiz_result = await db.execute(
                select(Quiz).where(Quiz.id == quiz_id)
            )
            quiz = quiz_result.scalar_one_or_none()
            
            if not quiz:
                return False
            
            # Teachers can always access
            if user_role in ['teacher', 'ta']:
                return True
            
            # Students can access if published and available
            if hasattr(quiz, 'published') and not quiz.published:
                return False
            
            # Check availability dates
            from datetime import datetime
            now = datetime.utcnow()
            
            if hasattr(quiz, 'available_from') and quiz.available_from:
                if now < quiz.available_from:
                    return False
            
            if hasattr(quiz, 'available_until') and quiz.available_until:
                if now > quiz.available_until:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking quiz access: {e}")
            return False
    
    async def _is_page_accessible(
        self,
        page_id: int,
        user_role: str,
        db: AsyncSession
    ) -> bool:
        """Check if page is accessible to user."""
        try:
            from app.models.page import Page
            
            page_result = await db.execute(
                select(Page).where(Page.id == page_id)
            )
            page = page_result.scalar_one_or_none()
            
            if not page:
                return False
            
            # Teachers can always access
            if user_role in ['teacher', 'ta']:
                return True
            
            # Students can access if published
            if hasattr(page, 'published') and not page.published:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking page access: {e}")
            return False
    
    async def _get_content_access_level(
        self,
        search_result: Dict[str, Any],
        user_permissions: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """Get user's access level for content."""
        try:
            metadata = search_result['metadata']
            course_id = metadata.get('course_id')
            
            if user_permissions['is_admin']:
                return 'admin'
            
            if course_id:
                user_role = user_permissions['course_roles'].get(course_id)
                if user_role in ['teacher', 'ta']:
                    return 'instructor'
                elif user_role == 'student':
                    return 'student'
            
            if user_permissions['is_global_teacher']:
                return 'teacher'
            
            return 'viewer'
            
        except Exception as e:
            logger.error(f"Error getting access level: {e}")
            return 'viewer'
    
    async def search_similar_content(
        self,
        content_id: str,
        content_type: str,
        user_id: int,
        db: AsyncSession,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar content to a given piece of content."""
        try:
            # Get the original content
            original_result = self.rag_indexer.vector_store.get_document(content_id)
            if not original_result:
                return []
            
            # Use the content as query for similarity search
            query = original_result.content[:500]  # Use first 500 chars as query
            
            # Search with permissions
            results = await self.search_with_permissions(
                query=query,
                user_id=user_id,
                db=db,
                top_k=top_k + 1,  # +1 to account for original content
                content_types=[content_type] if content_type else None
            )
            
            # Remove the original content from results
            filtered_results = [
                result for result in results 
                if result['doc_id'] != content_id
            ]
            
            return filtered_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar content: {e}")
            return []
    
    async def get_user_accessible_content_stats(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get statistics about content accessible to user."""
        try:
            user_permissions = await self._get_user_permissions(user_id, db)
            if not user_permissions:
                return {}
            
            stats = {
                'accessible_courses': len(user_permissions['accessible_course_ids']),
                'course_roles': dict(user_permissions['course_roles']),
                'content_access': {},
                'total_accessible_documents': 0
            }
            
            # Count accessible documents by type
            for doc_id, document in self.rag_indexer.vector_store.documents.items():
                # Create a mock search result for permission checking
                mock_result = {
                    'doc_id': doc_id,
                    'metadata': document.metadata,
                    'content': document.content,
                    'score': 1.0
                }
                
                if await self._can_access_content(mock_result, user_permissions, db):
                    content_type = document.metadata.get('type', 'unknown')
                    stats['content_access'][content_type] = stats['content_access'].get(content_type, 0) + 1
                    stats['total_accessible_documents'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting content stats: {e}")
            return {}


# Global permission-aware search service
permission_search_service = PermissionAwareSearchService()
