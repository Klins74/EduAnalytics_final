from pydantic import BaseModel

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: str | None = None

class GroupRead(GroupBase):
    id: int

    class Config:
        orm_mode = True