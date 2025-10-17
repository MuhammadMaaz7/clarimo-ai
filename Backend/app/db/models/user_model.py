from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    id: str
    email: str
    full_name: str
    hashed_password: str
    created_at: datetime

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
