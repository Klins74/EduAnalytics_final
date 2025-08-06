from pydantic import BaseModel, ConfigDict

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: str | None = None

class GroupRead(GroupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)