from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.discussion import DiscussionTopic, DiscussionEntry
from app.schemas.discussion import DiscussionTopicCreate, DiscussionEntryCreate


async def list_topics(db: AsyncSession, course_id: int) -> List[DiscussionTopic]:
    result = await db.execute(
        select(DiscussionTopic).options(selectinload(DiscussionTopic.entries)).where(DiscussionTopic.course_id == course_id).order_by(DiscussionTopic.id)
    )
    return result.scalars().all()


async def create_topic(db: AsyncSession, topic_in: DiscussionTopicCreate, author_id: int) -> DiscussionTopic:
    topic = DiscussionTopic(
        course_id=topic_in.course_id,
        title=topic_in.title,
        body=topic_in.body,
        published=topic_in.published,
        locked=topic_in.locked,
        author_id=author_id,
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


async def create_entry(db: AsyncSession, entry_in: DiscussionEntryCreate, user_id: int) -> DiscussionEntry:
    entry = DiscussionEntry(
        topic_id=entry_in.topic_id,
        user_id=user_id,
        parent_id=entry_in.parent_id,
        message=entry_in.message,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry




