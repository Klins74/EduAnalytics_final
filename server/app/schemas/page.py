from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PageBase(BaseModel):
    title: str
    slug: str
    body: Optional[str] = None
    published: bool = False


class PageCreate(PageBase):
    course_id: int


class PageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    body: Optional[str] = None
    published: Optional[bool] = None


class PageRead(PageBase):
    id: int
    course_id: int
    author_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)




