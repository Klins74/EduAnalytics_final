from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    role: str | None = None

class UserRead(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)