from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ModuleItemBase(BaseModel):
    title: str
    type: str = Field(..., description="assignment|quiz|page|file|discussion|external_url")
    content_id: Optional[int] = None
    position: int = 0
    indent: int = 0
    published: bool = False


class ModuleItemCreate(ModuleItemBase):
    pass


class ModuleItemRead(ModuleItemBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ModuleBase(BaseModel):
    name: str
    position: int = 0
    published: bool = False
    unlock_at: Optional[datetime] = None


class ModuleCreate(ModuleBase):
    course_id: int
    items: Optional[List[ModuleItemCreate]] = None


class ModuleRead(ModuleBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
    items: List[ModuleItemRead] = []
    model_config = ConfigDict(from_attributes=True)




