"""
User data models and schemas
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user creation"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    batch: str = Field(..., pattern=r"^BATCH-\d+$")
    category: Literal["ABOVE_AVERAGE", "AVERAGE", "GOOD", "POOR"]


class UserUpdate(BaseModel):
    """Schema for user updates"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    batch: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[Literal["ABOVE_AVERAGE", "AVERAGE", "GOOD", "POOR"]] = None


class UserResponse(BaseModel):
    """Schema for user response"""

    id: str
    name: str
    email: str
    role: str
    batch: str
    category: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    """Schema for user in database"""

    id: str
    name: str
    email: str
    role: str
    batch: str
    category: str
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Schema for login request"""

    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Schema for login response"""

    id_token: str
    user_id: str
    email: str
    name: str
    role: str


class CurrentUser(BaseModel):
    """Schema for current authenticated user"""

    user_id: str
    email: str
    role: str
    name: str
