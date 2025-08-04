from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: str | None = None
    role: str | None = None

class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True