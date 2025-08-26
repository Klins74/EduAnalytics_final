from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DiscussionTopicBase(BaseModel):
    title: str
    body: Optional[str] = None
    published: bool = True
    locked: bool = False


class DiscussionTopicCreate(DiscussionTopicBase):
    course_id: int


class DiscussionTopicRead(DiscussionTopicBase):
    id: int
    course_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DiscussionEntryBase(BaseModel):
    message: str
    parent_id: Optional[int] = None


class DiscussionEntryCreate(DiscussionEntryBase):
    topic_id: int


class DiscussionEntryRead(DiscussionEntryBase):
    id: int
    topic_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)




