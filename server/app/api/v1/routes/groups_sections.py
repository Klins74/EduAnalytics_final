"""API routes for course groups and sections management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.group_section_service import section_service, group_service, group_assignment_service

router = APIRouter(prefix="/groups-sections", tags=["Groups & Sections"])


# Pydantic models for requests
class SectionCreateRequest(BaseModel):
    """Request model for creating a course section."""
    name: str
    course_id: int
    section_code: Optional[str] = None
    description: Optional[str] = None
    max_enrollment: Optional[int] = None
    meeting_times: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    instructor_id: Optional[int] = None
    canvas_section_id: Optional[str] = None
    sis_section_id: Optional[str] = None


class SectionEnrollmentRequest(BaseModel):
    """Request model for section enrollment."""
    user_id: int
    role: str = "student"


class GroupCategoryCreateRequest(BaseModel):
    """Request model for creating a group category."""
    name: str
    course_id: int
    description: Optional[str] = None
    auto_leader: bool = False
    group_limit: Optional[int] = None
    enable_self_signup: bool = False
    restrict_self_signup: bool = False
    canvas_group_category_id: Optional[str] = None


class GroupCreateRequest(BaseModel):
    """Request model for creating a course group."""
    name: str
    course_id: int
    section_id: Optional[int] = None
    description: Optional[str] = None
    max_members: int = 6
    is_self_signup: bool = False
    group_category_id: Optional[int] = None
    group_type: str = "study"
    leader_id: Optional[int] = None
    canvas_group_id: Optional[str] = None


class GroupMembershipRequest(BaseModel):
    """Request model for group membership."""
    user_id: int
    role: str = "member"


class GroupSubmissionRequest(BaseModel):
    """Request model for group submission."""
    assignment_id: int
    group_id: int
    submission_text: Optional[str] = None
    submission_url: Optional[str] = None
    file_ids: Optional[List[str]] = None
    canvas_submission_id: Optional[str] = None


class GroupGradeRequest(BaseModel):
    """Request model for grading group submission."""
    score: Optional[int] = None
    grade: Optional[str] = None
    feedback: Optional[str] = None


# Section endpoints
@router.post("/sections", summary="Create course section")
async def create_section(
    request: SectionCreateRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Create a new course section."""
    try:
        section_data = request.dict()
        section = await section_service.create_section(section_data)
        
        return {
            "success": True,
            "message": "Section created successfully",
            "section": {
                "id": section.id,
                "name": section.name,
                "course_id": section.course_id,
                "section_code": section.section_code,
                "description": section.description,
                "max_enrollment": section.max_enrollment,
                "location": section.location,
                "instructor_id": section.instructor_id,
                "is_active": section.is_active,
                "created_at": section.created_at.isoformat()
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
            detail=f"Failed to create section: {str(e)}"
        )


@router.get("/sections/{section_id}", summary="Get section details")
async def get_section(
    section_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get section details with enrollments."""
    try:
        section = await section_service.get_section(section_id)
        
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section {section_id} not found"
            )
        
        return {
            "success": True,
            "section": {
                "id": section.id,
                "name": section.name,
                "course_id": section.course_id,
                "section_code": section.section_code,
                "description": section.description,
                "max_enrollment": section.max_enrollment,
                "location": section.location,
                "instructor": {
                    "id": section.instructor.id,
                    "name": section.instructor.name,
                    "email": section.instructor.email
                } if section.instructor else None,
                "enrolled_users": [
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email
                    }
                    for user in section.enrolled_users
                ],
                "groups_count": len(section.groups),
                "is_active": section.is_active,
                "created_at": section.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get section: {str(e)}"
        )


@router.get("/courses/{course_id}/sections", summary="Get course sections")
async def get_course_sections(
    course_id: int,
    include_inactive: bool = Query(False, description="Include inactive sections"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all sections for a course."""
    try:
        sections = await section_service.get_course_sections(course_id, include_inactive)
        
        return {
            "success": True,
            "course_id": course_id,
            "sections": [
                {
                    "id": section.id,
                    "name": section.name,
                    "section_code": section.section_code,
                    "description": section.description,
                    "max_enrollment": section.max_enrollment,
                    "current_enrollment": len(section.enrolled_users),
                    "location": section.location,
                    "instructor": {
                        "id": section.instructor.id,
                        "name": section.instructor.name
                    } if section.instructor else None,
                    "is_active": section.is_active
                }
                for section in sections
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course sections: {str(e)}"
        )


@router.post("/sections/{section_id}/enroll", summary="Enroll user in section")
async def enroll_in_section(
    section_id: int,
    request: SectionEnrollmentRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Enroll a user in a section."""
    try:
        success = await section_service.enroll_user_in_section(
            section_id, request.user_id, request.role
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to enroll user in section"
            )
        
        return {
            "success": True,
            "message": f"User {request.user_id} enrolled in section {section_id} as {request.role}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll user: {str(e)}"
        )


@router.delete("/sections/{section_id}/users/{user_id}", summary="Unenroll user from section")
async def unenroll_from_section(
    section_id: int,
    user_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Remove a user from a section."""
    try:
        success = await section_service.unenroll_user_from_section(section_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to unenroll user from section"
            )
        
        return {
            "success": True,
            "message": f"User {user_id} unenrolled from section {section_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unenroll user: {str(e)}"
        )


@router.get("/sections/{section_id}/stats", summary="Get section enrollment stats")
async def get_section_stats(
    section_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get enrollment statistics for a section."""
    try:
        stats = await section_service.get_section_enrollment_stats(section_id)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get section stats: {str(e)}"
        )


# Group Category endpoints
@router.post("/group-categories", summary="Create group category")
async def create_group_category(
    request: GroupCategoryCreateRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Create a new group category."""
    try:
        category_data = request.dict()
        category = await group_service.create_group_category(category_data)
        
        return {
            "success": True,
            "message": "Group category created successfully",
            "category": {
                "id": category.id,
                "name": category.name,
                "course_id": category.course_id,
                "description": category.description,
                "auto_leader": category.auto_leader,
                "group_limit": category.group_limit,
                "enable_self_signup": category.enable_self_signup,
                "restrict_self_signup": category.restrict_self_signup,
                "is_active": category.is_active,
                "created_at": category.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create group category: {str(e)}"
        )


# Group endpoints
@router.post("/groups", summary="Create course group")
async def create_group(
    request: GroupCreateRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Create a new course group."""
    try:
        group_data = request.dict()
        group_data["created_by"] = current_user.id
        
        group = await group_service.create_group(group_data)
        
        return {
            "success": True,
            "message": "Group created successfully",
            "group": {
                "id": group.id,
                "name": group.name,
                "course_id": group.course_id,
                "section_id": group.section_id,
                "description": group.description,
                "max_members": group.max_members,
                "is_self_signup": group.is_self_signup,
                "group_type": group.group_type,
                "leader_id": group.leader_id,
                "created_by": group.created_by,
                "is_active": group.is_active,
                "created_at": group.created_at.isoformat()
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
            detail=f"Failed to create group: {str(e)}"
        )


@router.get("/groups/{group_id}", summary="Get group details")
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get group details with members."""
    try:
        group = await group_service.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )
        
        return {
            "success": True,
            "group": {
                "id": group.id,
                "name": group.name,
                "course_id": group.course_id,
                "section": {
                    "id": group.section.id,
                    "name": group.section.name
                } if group.section else None,
                "category": {
                    "id": group.category.id,
                    "name": group.category.name
                } if group.category else None,
                "description": group.description,
                "max_members": group.max_members,
                "current_members": len(group.members),
                "is_self_signup": group.is_self_signup,
                "group_type": group.group_type,
                "leader": {
                    "id": group.leader.id,
                    "name": group.leader.name,
                    "email": group.leader.email
                } if group.leader else None,
                "members": [
                    {
                        "id": member.id,
                        "name": member.name,
                        "email": member.email
                    }
                    for member in group.members
                ],
                "is_active": group.is_active,
                "created_at": group.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get group: {str(e)}"
        )


@router.get("/courses/{course_id}/groups", summary="Get course groups")
async def get_course_groups(
    course_id: int,
    section_id: Optional[int] = Query(None, description="Filter by section"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    include_inactive: bool = Query(False, description="Include inactive groups"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all groups for a course."""
    try:
        groups = await group_service.get_course_groups(
            course_id, section_id, category_id, include_inactive
        )
        
        return {
            "success": True,
            "course_id": course_id,
            "groups": [
                {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "max_members": group.max_members,
                    "current_members": len(group.members),
                    "is_full": group.max_members and len(group.members) >= group.max_members,
                    "is_self_signup": group.is_self_signup,
                    "group_type": group.group_type,
                    "leader": {
                        "id": group.leader.id,
                        "name": group.leader.name
                    } if group.leader else None,
                    "category": {
                        "id": group.category.id,
                        "name": group.category.name
                    } if group.category else None,
                    "is_active": group.is_active
                }
                for group in groups
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get course groups: {str(e)}"
        )


@router.post("/groups/{group_id}/members", summary="Add user to group")
async def add_to_group(
    group_id: int,
    request: GroupMembershipRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Add a user to a group."""
    try:
        # Check if user can add members (self-signup or teacher/admin)
        group = await group_service.get_group(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )
        
        # Allow if: self-signup enabled, user is teacher/admin, or user is adding themselves
        can_add = (
            group.is_self_signup or
            current_user.role in [UserRole.teacher, UserRole.admin] or
            (request.user_id == current_user.id and group.is_self_signup)
        )
        
        if not can_add:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add members to this group"
            )
        
        success = await group_service.add_user_to_group(
            group_id, request.user_id, request.role
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add user to group"
            )
        
        return {
            "success": True,
            "message": f"User {request.user_id} added to group {group_id} as {request.role}"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add user to group: {str(e)}"
        )


@router.delete("/groups/{group_id}/members/{user_id}", summary="Remove user from group")
async def remove_from_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Remove a user from a group."""
    try:
        # Check permissions (teacher/admin or user removing themselves)
        if current_user.role not in [UserRole.teacher, UserRole.admin] and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this user from the group"
            )
        
        success = await group_service.remove_user_from_group(group_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove user from group"
            )
        
        return {
            "success": True,
            "message": f"User {user_id} removed from group {group_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove user from group: {str(e)}"
        )


@router.put("/groups/{group_id}/leader", summary="Update group leader")
async def update_group_leader(
    group_id: int,
    new_leader_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Update the leader of a group."""
    try:
        success = await group_service.update_group_leader(group_id, new_leader_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update group leader"
            )
        
        return {
            "success": True,
            "message": f"Group {group_id} leader updated to user {new_leader_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update group leader: {str(e)}"
        )


@router.get("/users/{user_id}/groups", summary="Get user's groups")
async def get_user_groups(
    user_id: int,
    course_id: Optional[int] = Query(None, description="Filter by course"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all groups a user belongs to."""
    try:
        # Check permissions (user can see their own groups, teachers/admins can see any)
        if current_user.id != user_id and current_user.role not in [UserRole.teacher, UserRole.admin]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user's groups"
            )
        
        groups = await group_service.get_user_groups(user_id, course_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "groups": [
                {
                    "id": group.id,
                    "name": group.name,
                    "course": {
                        "id": group.course.id,
                        "name": group.course.name
                    },
                    "group_type": group.group_type,
                    "is_leader": group.leader_id == user_id,
                    "member_count": len(group.members),
                    "max_members": group.max_members
                }
                for group in groups
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user groups: {str(e)}"
        )


@router.get("/groups/{group_id}/stats", summary="Get group statistics")
async def get_group_stats(
    group_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get statistics for a group."""
    try:
        stats = await group_service.get_group_stats(group_id)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get group stats: {str(e)}"
        )


# Group Assignment endpoints
@router.post("/group-submissions", summary="Create group submission")
async def create_group_submission(
    request: GroupSubmissionRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Submit an assignment on behalf of a group."""
    try:
        submission_data = request.dict()
        submission_data["submitted_by"] = current_user.id
        
        submission = await group_assignment_service.create_group_submission(submission_data)
        
        return {
            "success": True,
            "message": "Group submission created successfully",
            "submission": {
                "id": submission.id,
                "assignment_id": submission.assignment_id,
                "group_id": submission.group_id,
                "submitted_by": submission.submitted_by,
                "workflow_state": submission.workflow_state,
                "submitted_at": submission.submitted_at.isoformat(),
                "created_at": submission.created_at.isoformat()
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
            detail=f"Failed to create group submission: {str(e)}"
        )


@router.put("/group-submissions/{submission_id}/grade", summary="Grade group submission")
async def grade_group_submission(
    submission_id: int,
    request: GroupGradeRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Grade a group submission."""
    try:
        grade_data = request.dict()
        grade_data["graded_by"] = current_user.id
        
        submission = await group_assignment_service.grade_group_submission(submission_id, grade_data)
        
        return {
            "success": True,
            "message": "Group submission graded successfully",
            "submission": {
                "id": submission.id,
                "assignment_id": submission.assignment_id,
                "group_id": submission.group_id,
                "score": submission.score,
                "grade": submission.grade,
                "feedback": submission.feedback,
                "graded_by": submission.graded_by,
                "graded_at": submission.graded_at.isoformat() if submission.graded_at else None,
                "workflow_state": submission.workflow_state
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
            detail=f"Failed to grade group submission: {str(e)}"
        )


@router.get("/assignments/{assignment_id}/group-submissions", summary="Get group submissions")
async def get_group_submissions(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get all group submissions for an assignment."""
    try:
        submissions = await group_assignment_service.get_group_submissions(assignment_id)
        
        return {
            "success": True,
            "assignment_id": assignment_id,
            "submissions": [
                {
                    "id": submission.id,
                    "group": {
                        "id": submission.group.id,
                        "name": submission.group.name
                    },
                    "submitted_by": {
                        "id": submission.submitter.id,
                        "name": submission.submitter.name
                    } if submission.submitter else None,
                    "submission_text": submission.submission_text,
                    "submission_url": submission.submission_url,
                    "score": submission.score,
                    "grade": submission.grade,
                    "workflow_state": submission.workflow_state,
                    "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
                    "graded_at": submission.graded_at.isoformat() if submission.graded_at else None,
                    "late": submission.late,
                    "missing": submission.missing
                }
                for submission in submissions
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get group submissions: {str(e)}"
        )
