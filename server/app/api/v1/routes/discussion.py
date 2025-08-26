from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.discussion import (
    DiscussionTopicCreate,
    DiscussionTopicRead,
    DiscussionEntryCreate,
    DiscussionEntryRead,
)
from app.crud import discussion as crud_discussion


router = APIRouter(prefix="/discussions", tags=["Discussions"])


@router.get("/course/{course_id}", response_model=List[DiscussionTopicRead])
async def list_topics(course_id: int, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_discussion.list_topics(db, course_id)


@router.post("/", response_model=DiscussionTopicRead, status_code=status.HTTP_201_CREATED)
async def create_topic(topic: DiscussionTopicCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    return await crud_discussion.create_topic(db, topic, author_id=current_user.id)


@router.post("/{topic_id}/entries", response_model=DiscussionEntryRead, status_code=status.HTTP_201_CREATED)
async def create_entry(topic_id: int, entry: DiscussionEntryCreate, db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    if entry.topic_id != topic_id:
        raise HTTPException(status_code=400, detail="topic_id mismatch")
    return await crud_discussion.create_entry(db, entry, user_id=current_user.id)




