"""
Group and Section Management Service.

Provides comprehensive management of course sections, groups, and group assignments
with Canvas integration support.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_, or_, func
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.course_section import (
    CourseSection, CourseGroup, GroupCategory, GroupSubmission, GroupDiscussion,
    group_memberships, section_enrollments
)
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment

logger = logging.getLogger(__name__)


class SectionService:
    """Service for managing course sections."""
    
    async def create_section(self, section_data: Dict[str, Any]) -> CourseSection:
        """Create a new course section."""
        try:
            async with AsyncSessionLocal() as db:
                # Validate course exists
                course = await db.execute(
                    select(Course).where(Course.id == section_data["course_id"])
                )
                if not course.scalar_one_or_none():
                    raise ValueError(f"Course {section_data['course_id']} not found")
                
                # Check for duplicate section code within course
                if section_data.get("section_code"):
                    existing = await db.execute(
                        select(CourseSection).where(
                            and_(
                                CourseSection.course_id == section_data["course_id"],
                                CourseSection.section_code == section_data["section_code"]
                            )
                        )
                    )
                    if existing.scalar_one_or_none():
                        raise ValueError(f"Section code '{section_data['section_code']}' already exists in this course")
                
                # Create section
                section = CourseSection(
                    name=section_data["name"],
                    course_id=section_data["course_id"],
                    section_code=section_data.get("section_code"),
                    description=section_data.get("description"),
                    max_enrollment=section_data.get("max_enrollment"),
                    meeting_times=json.dumps(section_data.get("meeting_times", {})),
                    location=section_data.get("location"),
                    instructor_id=section_data.get("instructor_id"),
                    canvas_section_id=section_data.get("canvas_section_id"),
                    sis_section_id=section_data.get("sis_section_id"),
                    is_active=section_data.get("is_active", True)
                )
                
                db.add(section)
                await db.commit()
                await db.refresh(section)
                
                logger.info(f"Created section: {section.name} (ID: {section.id})")
                return section
                
        except Exception as e:
            logger.error(f"Error creating section: {e}")
            raise
    
    async def get_section(self, section_id: int) -> Optional[CourseSection]:
        """Get section by ID with relationships."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(CourseSection)
                    .options(
                        selectinload(CourseSection.course),
                        selectinload(CourseSection.instructor),
                        selectinload(CourseSection.enrolled_users),
                        selectinload(CourseSection.groups)
                    )
                    .where(CourseSection.id == section_id)
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Error getting section: {e}")
            return None
    
    async def get_course_sections(self, course_id: int, include_inactive: bool = False) -> List[CourseSection]:
        """Get all sections for a course."""
        try:
            async with AsyncSessionLocal() as db:
                query = select(CourseSection).where(CourseSection.course_id == course_id)
                
                if not include_inactive:
                    query = query.where(CourseSection.is_active == True)
                
                query = query.options(
                    selectinload(CourseSection.instructor),
                    selectinload(CourseSection.enrolled_users)
                ).order_by(CourseSection.section_code, CourseSection.name)
                
                result = await db.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Error getting course sections: {e}")
            return []
    
    async def enroll_user_in_section(self, section_id: int, user_id: int, role: str = "student") -> bool:
        """Enroll a user in a section."""
        try:
            async with AsyncSessionLocal() as db:
                # Check if user is already enrolled
                existing = await db.execute(
                    select(section_enrollments).where(
                        and_(
                            section_enrollments.c.section_id == section_id,
                            section_enrollments.c.user_id == user_id
                        )
                    )
                )
                
                if existing.fetchone():
                    logger.info(f"User {user_id} already enrolled in section {section_id}")
                    return True
                
                # Add enrollment
                await db.execute(
                    insert(section_enrollments).values(
                        section_id=section_id,
                        user_id=user_id,
                        role=role
                    )
                )
                await db.commit()
                
                logger.info(f"Enrolled user {user_id} in section {section_id} as {role}")
                return True
                
        except Exception as e:
            logger.error(f"Error enrolling user in section: {e}")
            return False
    
    async def unenroll_user_from_section(self, section_id: int, user_id: int) -> bool:
        """Remove a user from a section."""
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    delete(section_enrollments).where(
                        and_(
                            section_enrollments.c.section_id == section_id,
                            section_enrollments.c.user_id == user_id
                        )
                    )
                )
                await db.commit()
                
                logger.info(f"Unenrolled user {user_id} from section {section_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error unenrolling user from section: {e}")
            return False
    
    async def get_section_enrollment_stats(self, section_id: int) -> Dict[str, Any]:
        """Get enrollment statistics for a section."""
        try:
            async with AsyncSessionLocal() as db:
                # Get section info
                section = await db.execute(
                    select(CourseSection).where(CourseSection.id == section_id)
                )
                section_obj = section.scalar_one_or_none()
                
                if not section_obj:
                    raise ValueError(f"Section {section_id} not found")
                
                # Get enrollment counts by role
                enrollment_stats = await db.execute(
                    select(
                        section_enrollments.c.role,
                        func.count(section_enrollments.c.user_id).label('count')
                    )
                    .where(section_enrollments.c.section_id == section_id)
                    .group_by(section_enrollments.c.role)
                )
                
                role_counts = {row.role: row.count for row in enrollment_stats.fetchall()}
                total_enrolled = sum(role_counts.values())
                
                return {
                    "section_id": section_id,
                    "section_name": section_obj.name,
                    "max_enrollment": section_obj.max_enrollment,
                    "total_enrolled": total_enrolled,
                    "available_spots": (section_obj.max_enrollment - total_enrolled) if section_obj.max_enrollment else None,
                    "role_breakdown": role_counts,
                    "enrollment_rate": (total_enrolled / section_obj.max_enrollment * 100) if section_obj.max_enrollment else None
                }
                
        except Exception as e:
            logger.error(f"Error getting section enrollment stats: {e}")
            raise


class GroupService:
    """Service for managing course groups."""
    
    async def create_group_category(self, category_data: Dict[str, Any]) -> GroupCategory:
        """Create a new group category."""
        try:
            async with AsyncSessionLocal() as db:
                category = GroupCategory(
                    name=category_data["name"],
                    course_id=category_data["course_id"],
                    description=category_data.get("description"),
                    auto_leader=category_data.get("auto_leader", False),
                    group_limit=category_data.get("group_limit"),
                    enable_self_signup=category_data.get("enable_self_signup", False),
                    restrict_self_signup=category_data.get("restrict_self_signup", False),
                    canvas_group_category_id=category_data.get("canvas_group_category_id")
                )
                
                db.add(category)
                await db.commit()
                await db.refresh(category)
                
                logger.info(f"Created group category: {category.name} (ID: {category.id})")
                return category
                
        except Exception as e:
            logger.error(f"Error creating group category: {e}")
            raise
    
    async def create_group(self, group_data: Dict[str, Any]) -> CourseGroup:
        """Create a new course group."""
        try:
            async with AsyncSessionLocal() as db:
                # Validate course exists
                course = await db.execute(
                    select(Course).where(Course.id == group_data["course_id"])
                )
                if not course.scalar_one_or_none():
                    raise ValueError(f"Course {group_data['course_id']} not found")
                
                # Create group
                group = CourseGroup(
                    name=group_data["name"],
                    course_id=group_data["course_id"],
                    section_id=group_data.get("section_id"),
                    description=group_data.get("description"),
                    max_members=group_data.get("max_members", 6),
                    is_self_signup=group_data.get("is_self_signup", False),
                    group_category_id=group_data.get("group_category_id"),
                    group_type=group_data.get("group_type", "study"),
                    leader_id=group_data.get("leader_id"),
                    created_by=group_data["created_by"],
                    canvas_group_id=group_data.get("canvas_group_id")
                )
                
                db.add(group)
                await db.commit()
                await db.refresh(group)
                
                # Add creator as first member if not already leader
                if group.leader_id != group.created_by:
                    await self.add_user_to_group(group.id, group.created_by, "member")
                
                logger.info(f"Created group: {group.name} (ID: {group.id})")
                return group
                
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            raise
    
    async def get_group(self, group_id: int) -> Optional[CourseGroup]:
        """Get group by ID with relationships."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(CourseGroup)
                    .options(
                        selectinload(CourseGroup.course),
                        selectinload(CourseGroup.section),
                        selectinload(CourseGroup.category),
                        selectinload(CourseGroup.leader),
                        selectinload(CourseGroup.creator),
                        selectinload(CourseGroup.members)
                    )
                    .where(CourseGroup.id == group_id)
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Error getting group: {e}")
            return None
    
    async def get_course_groups(self, course_id: int, section_id: Optional[int] = None,
                              category_id: Optional[int] = None, include_inactive: bool = False) -> List[CourseGroup]:
        """Get groups for a course with optional filtering."""
        try:
            async with AsyncSessionLocal() as db:
                query = select(CourseGroup).where(CourseGroup.course_id == course_id)
                
                if section_id:
                    query = query.where(CourseGroup.section_id == section_id)
                
                if category_id:
                    query = query.where(CourseGroup.group_category_id == category_id)
                
                if not include_inactive:
                    query = query.where(CourseGroup.is_active == True)
                
                query = query.options(
                    selectinload(CourseGroup.leader),
                    selectinload(CourseGroup.members),
                    selectinload(CourseGroup.category)
                ).order_by(CourseGroup.name)
                
                result = await db.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Error getting course groups: {e}")
            return []
    
    async def add_user_to_group(self, group_id: int, user_id: int, role: str = "member") -> bool:
        """Add a user to a group."""
        try:
            async with AsyncSessionLocal() as db:
                # Check if user is already in group
                existing = await db.execute(
                    select(group_memberships).where(
                        and_(
                            group_memberships.c.group_id == group_id,
                            group_memberships.c.user_id == user_id
                        )
                    )
                )
                
                if existing.fetchone():
                    logger.info(f"User {user_id} already in group {group_id}")
                    return True
                
                # Check group capacity
                group = await db.execute(
                    select(CourseGroup).where(CourseGroup.id == group_id)
                )
                group_obj = group.scalar_one_or_none()
                
                if not group_obj:
                    raise ValueError(f"Group {group_id} not found")
                
                # Count current members
                member_count = await db.execute(
                    select(func.count(group_memberships.c.user_id))
                    .where(group_memberships.c.group_id == group_id)
                )
                current_count = member_count.scalar()
                
                if group_obj.max_members and current_count >= group_obj.max_members:
                    raise ValueError(f"Group {group_id} is at maximum capacity ({group_obj.max_members})")
                
                # Add membership
                await db.execute(
                    insert(group_memberships).values(
                        group_id=group_id,
                        user_id=user_id,
                        role=role
                    )
                )
                await db.commit()
                
                logger.info(f"Added user {user_id} to group {group_id} as {role}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding user to group: {e}")
            return False
    
    async def remove_user_from_group(self, group_id: int, user_id: int) -> bool:
        """Remove a user from a group."""
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(
                    delete(group_memberships).where(
                        and_(
                            group_memberships.c.group_id == group_id,
                            group_memberships.c.user_id == user_id
                        )
                    )
                )
                await db.commit()
                
                logger.info(f"Removed user {user_id} from group {group_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing user from group: {e}")
            return False
    
    async def update_group_leader(self, group_id: int, new_leader_id: int) -> bool:
        """Update group leader."""
        try:
            async with AsyncSessionLocal() as db:
                # Check if new leader is in the group
                membership = await db.execute(
                    select(group_memberships).where(
                        and_(
                            group_memberships.c.group_id == group_id,
                            group_memberships.c.user_id == new_leader_id
                        )
                    )
                )
                
                if not membership.fetchone():
                    # Add new leader to group if not already a member
                    await self.add_user_to_group(group_id, new_leader_id, "leader")
                else:
                    # Update existing member's role to leader
                    await db.execute(
                        update(group_memberships)
                        .where(
                            and_(
                                group_memberships.c.group_id == group_id,
                                group_memberships.c.user_id == new_leader_id
                            )
                        )
                        .values(role="leader")
                    )
                
                # Update group leader
                await db.execute(
                    update(CourseGroup)
                    .where(CourseGroup.id == group_id)
                    .values(leader_id=new_leader_id)
                )
                
                await db.commit()
                
                logger.info(f"Updated group {group_id} leader to user {new_leader_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating group leader: {e}")
            return False
    
    async def get_user_groups(self, user_id: int, course_id: Optional[int] = None) -> List[CourseGroup]:
        """Get all groups a user belongs to."""
        try:
            async with AsyncSessionLocal() as db:
                query = (
                    select(CourseGroup)
                    .join(group_memberships, CourseGroup.id == group_memberships.c.group_id)
                    .where(group_memberships.c.user_id == user_id)
                )
                
                if course_id:
                    query = query.where(CourseGroup.course_id == course_id)
                
                query = query.options(
                    selectinload(CourseGroup.course),
                    selectinload(CourseGroup.leader),
                    selectinload(CourseGroup.members)
                ).order_by(CourseGroup.name)
                
                result = await db.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Error getting user groups: {e}")
            return []
    
    async def get_group_stats(self, group_id: int) -> Dict[str, Any]:
        """Get statistics for a group."""
        try:
            async with AsyncSessionLocal() as db:
                # Get group info
                group = await db.execute(
                    select(CourseGroup).where(CourseGroup.id == group_id)
                )
                group_obj = group.scalar_one_or_none()
                
                if not group_obj:
                    raise ValueError(f"Group {group_id} not found")
                
                # Get member count by role
                member_stats = await db.execute(
                    select(
                        group_memberships.c.role,
                        func.count(group_memberships.c.user_id).label('count')
                    )
                    .where(group_memberships.c.group_id == group_id)
                    .group_by(group_memberships.c.role)
                )
                
                role_counts = {row.role: row.count for row in member_stats.fetchall()}
                total_members = sum(role_counts.values())
                
                # Get assignment count (if assignments table has group_id)
                assignment_count = 0
                try:
                    assignments = await db.execute(
                        select(func.count(Assignment.id))
                        .where(Assignment.group_id == group_id)
                    )
                    assignment_count = assignments.scalar() or 0
                except Exception:
                    pass  # Table might not have group_id column yet
                
                return {
                    "group_id": group_id,
                    "group_name": group_obj.name,
                    "max_members": group_obj.max_members,
                    "total_members": total_members,
                    "available_spots": (group_obj.max_members - total_members) if group_obj.max_members else None,
                    "role_breakdown": role_counts,
                    "assignment_count": assignment_count,
                    "is_full": group_obj.max_members and total_members >= group_obj.max_members,
                    "leader_id": group_obj.leader_id
                }
                
        except Exception as e:
            logger.error(f"Error getting group stats: {e}")
            raise


class GroupAssignmentService:
    """Service for managing group assignments and submissions."""
    
    async def create_group_submission(self, submission_data: Dict[str, Any]) -> GroupSubmission:
        """Create a group submission."""
        try:
            async with AsyncSessionLocal() as db:
                # Validate assignment and group
                assignment = await db.execute(
                    select(Assignment).where(Assignment.id == submission_data["assignment_id"])
                )
                if not assignment.scalar_one_or_none():
                    raise ValueError(f"Assignment {submission_data['assignment_id']} not found")
                
                group = await db.execute(
                    select(CourseGroup).where(CourseGroup.id == submission_data["group_id"])
                )
                if not group.scalar_one_or_none():
                    raise ValueError(f"Group {submission_data['group_id']} not found")
                
                # Check if submission already exists
                existing = await db.execute(
                    select(GroupSubmission).where(
                        and_(
                            GroupSubmission.assignment_id == submission_data["assignment_id"],
                            GroupSubmission.group_id == submission_data["group_id"]
                        )
                    )
                )
                
                if existing.scalar_one_or_none():
                    raise ValueError("Group submission already exists for this assignment")
                
                # Create submission
                submission = GroupSubmission(
                    assignment_id=submission_data["assignment_id"],
                    group_id=submission_data["group_id"],
                    submitted_by=submission_data["submitted_by"],
                    submission_text=submission_data.get("submission_text"),
                    submission_url=submission_data.get("submission_url"),
                    file_ids=json.dumps(submission_data.get("file_ids", [])),
                    workflow_state="submitted",
                    submitted_at=datetime.utcnow(),
                    canvas_submission_id=submission_data.get("canvas_submission_id")
                )
                
                db.add(submission)
                await db.commit()
                await db.refresh(submission)
                
                logger.info(f"Created group submission: assignment={submission.assignment_id}, group={submission.group_id}")
                return submission
                
        except Exception as e:
            logger.error(f"Error creating group submission: {e}")
            raise
    
    async def grade_group_submission(self, submission_id: int, grade_data: Dict[str, Any]) -> GroupSubmission:
        """Grade a group submission."""
        try:
            async with AsyncSessionLocal() as db:
                submission = await db.execute(
                    select(GroupSubmission).where(GroupSubmission.id == submission_id)
                )
                submission_obj = submission.scalar_one_or_none()
                
                if not submission_obj:
                    raise ValueError(f"Group submission {submission_id} not found")
                
                # Update submission with grade
                await db.execute(
                    update(GroupSubmission)
                    .where(GroupSubmission.id == submission_id)
                    .values(
                        score=grade_data.get("score"),
                        grade=grade_data.get("grade"),
                        feedback=grade_data.get("feedback"),
                        graded_by=grade_data["graded_by"],
                        graded_at=datetime.utcnow(),
                        workflow_state="graded"
                    )
                )
                
                await db.commit()
                await db.refresh(submission_obj)
                
                logger.info(f"Graded group submission {submission_id}")
                return submission_obj
                
        except Exception as e:
            logger.error(f"Error grading group submission: {e}")
            raise
    
    async def get_group_submissions(self, assignment_id: int) -> List[GroupSubmission]:
        """Get all group submissions for an assignment."""
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(GroupSubmission)
                    .options(
                        selectinload(GroupSubmission.group),
                        selectinload(GroupSubmission.submitter),
                        selectinload(GroupSubmission.grader)
                    )
                    .where(GroupSubmission.assignment_id == assignment_id)
                    .order_by(GroupSubmission.submitted_at.desc())
                )
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Error getting group submissions: {e}")
            return []


# Global service instances
section_service = SectionService()
group_service = GroupService()
group_assignment_service = GroupAssignmentService()
