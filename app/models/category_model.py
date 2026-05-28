"""
Category and dynamic data models
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class CategoryDataUpdate(BaseModel):
    """Schema for updating category data"""

    data: dict[str, Any] = Field(default_factory=dict)


class StudentCategoryResponse(BaseModel):
    """Schema for student category response"""

    category: Literal["ABOVE_AVERAGE", "AVERAGE", "GOOD", "POOR"]
    data: dict[str, Any]


class CompanyScoresRequest(BaseModel):
    """Schema for adding company scores"""

    company: str = Field(..., min_length=1)
    scores: dict[str, float] = Field(default_factory=dict)


class CompanyScoresResponse(BaseModel):
    """Schema for company scores response"""

    companies: dict[str, dict[str, float]]


class ExamScore(BaseModel):
    """Schema for exam score"""

    total_score: float = Field(..., ge=0, le=100)


class ExamResponse(BaseModel):
    """Schema for exam response"""

    id: str
    user_id: str
    total_score: float
    created_at: str
