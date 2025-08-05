from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter()

# Dummy user for demonstration
fake_user = {
    "username": "admin@example.com",
    "password": "admin"
}

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != fake_user["username"] or form_data.password != fake_user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # In a real app, generate a JWT here
    return {"access_token": "fake-jwt-token", "token_type": "bearer"}