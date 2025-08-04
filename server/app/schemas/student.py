from pydantic import BaseModel, EmailStr
from app.schemas.group import GroupRead

class StudentBase(BaseModel):
    full_name: str
    email: EmailStr
    group_id: int | None = None

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    group_id: int | None = None

class StudentRead(StudentBase):
    id: int
    group: GroupRead | None = None

    class Config:
        orm_mode = True