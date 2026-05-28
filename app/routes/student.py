"""
Student routes for read-only access to own data
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import get_current_user
from app.models.category_model import CompanyScoresResponse, ExamResponse
from app.models.user_model import CurrentUser, UserResponse
from app.services.student_service import StudentService
from app.services.user_service import UserService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/student", tags=["student"])

user_service = UserService()
student_service = StudentService()


@router.get("/me", response_model=UserResponse, status_code=200)
async def get_own_profile(
    current_user: CurrentUser = Depends(get_current_user),
) -> UserResponse:
    """
    Get own profile

    Args:
        current_user: Current authenticated user

    Returns:
        Own profile details
    """
    try:
        user_data = user_service.get_user(current_user.user_id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse(
            id=current_user.user_id,
            name=user_data.get("name", ""),
            email=user_data.get("email", ""),
            role=user_data.get("role", "student"),
            batch=user_data.get("batch", ""),
            category=user_data.get("category", ""),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving profile",
        )


@router.get("/category", status_code=200)
async def get_own_category(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get own category and data

    Args:
        current_user: Current authenticated user

    Returns:
        Category and associated data
    """
    try:
        category = student_service.get_category(current_user.user_id)

        if not category:
            return {"category": "", "data": {}}

        return {
            "category": category.get("category", ""),
            "data": category.get("data", {}),
        }

    except Exception as e:
        logger.error(f"Error getting category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving category",
        )


@router.get("/company-scores", response_model=CompanyScoresResponse, status_code=200)
async def get_own_company_scores(
    current_user: CurrentUser = Depends(get_current_user),
) -> CompanyScoresResponse:
    """
    Get own company scores

    Args:
        current_user: Current authenticated user

    Returns:
        Company scores
    """
    try:
        scores = student_service.get_company_scores(current_user.user_id)

        if not scores:
            return CompanyScoresResponse(companies={})

        return CompanyScoresResponse(companies=scores.get("companies", {}))

    except Exception as e:
        logger.error(f"Error getting company scores: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving company scores",
        )


@router.get("/exams", status_code=200)
async def get_own_exams(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """
    Get own exam results

    Args:
        current_user: Current authenticated user

    Returns:
        List of exam results
    """
    try:
        exams = student_service.get_exams(current_user.user_id)

        return [
            {
                "id": exam.get("id"),
                "user_id": exam.get("user_id"),
                "total_score": exam.get("total_score"),
                "created_at": exam.get("created_at"),
            }
            for exam in exams
        ]

    except Exception as e:
        logger.error(f"Error getting exams: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving exams",
        )
