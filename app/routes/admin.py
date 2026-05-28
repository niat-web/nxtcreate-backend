"""
Admin routes for managing students and data
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import get_admin_user
from app.models.category_model import (
    CategoryDataUpdate,
    CompanyScoresRequest,
    CompanyScoresResponse,
    ExamResponse,
    ExamScore,
)
from app.models.user_model import CurrentUser, UserResponse, UserUpdate
from app.services.firebase import FirebaseService
from app.services.student_service import StudentService
from app.services.user_service import UserService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

firebase = FirebaseService()
user_service = UserService()
student_service = StudentService()


@router.get("/students", status_code=200)
async def get_students(
    admin: CurrentUser = Depends(get_admin_user),
) -> list[UserResponse]:
    """
    Get all students

    Args:
        admin: Admin user

    Returns:
        List of students
    """
    try:
        students = user_service.get_all_students()

        return [
            UserResponse(
                id=student.get("id"),
                name=student.get("name", ""),
                email=student.get("email", ""),
                role=student.get("role", "user"),
                created_at=student.get("created_at"),
                updated_at=student.get("updated_at"),
            )
            for student in students
        ]

    except Exception as e:
        logger.error(f"Error getting students: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving students",
        )


@router.get("/student/{user_id}", status_code=200)
async def get_student(
    user_id: str,
    admin: CurrentUser = Depends(get_admin_user),
) -> UserResponse:
    """
    Get specific student details

    Args:
        user_id: Student user ID
        admin: Admin user

    Returns:
        Student details
    """
    try:
        user_data = user_service.get_user(user_id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        return UserResponse(
            id=user_id,
            name=user_data.get("name", ""),
            email=user_data.get("email", ""),
            role=user_data.get("role", "user"),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving student",
        )


@router.patch("/student/{user_id}", status_code=200)
async def update_student(
    user_id: str,
    data: UserUpdate,
    admin: CurrentUser = Depends(get_admin_user),
) -> UserResponse:
    """
    Update student profile

    Args:
        user_id: Student user ID
        data: Updated student data
        admin: Admin user

    Returns:
        Updated student details
    """
    try:
        user_data = user_service.get_user(user_id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # Update only provided fields
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name

        if update_data:
            user_service.update_user(user_id, update_data)

        # Refresh user data
        updated_user = user_service.get_user(user_id)

        return UserResponse(
            id=user_id,
            name=updated_user.get("name", ""),
            email=updated_user.get("email", ""),
            role=updated_user.get("role", "student"),
            batch=updated_user.get("batch", ""),
            category=updated_user.get("category", ""),
            created_at=updated_user.get("created_at"),
            updated_at=updated_user.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating student: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating student",
        )


@router.patch("/student/{user_id}/category-data", status_code=200)
async def update_category_data(
    user_id: str,
    data: CategoryDataUpdate,
    admin: CurrentUser = Depends(get_admin_user),
) -> dict[str, Any]:
    """
    Update student category data

    Args:
        user_id: Student user ID
        data: Category data to update
        admin: Admin user

    Returns:
        Updated category data
    """
    try:
        student_service.update_category_data(user_id, data.data)

        category = student_service.get_category(user_id)

        return {
            "user_id": user_id,
            "category": category.get("category") if category else "",
            "data": category.get("data", {}) if category else {},
        }

    except Exception as e:
        logger.error(f"Error updating category data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating category data",
        )


@router.post("/student/{user_id}/company-scores", status_code=201)
async def add_company_score(
    user_id: str,
    request: CompanyScoresRequest,
    admin: CurrentUser = Depends(get_admin_user),
) -> CompanyScoresResponse:
    """
    Add company score for student

    Args:
        user_id: Student user ID
        request: Company scores request
        admin: Admin user

    Returns:
        Updated company scores
    """
    try:
        student_service.add_company_score(user_id, request.company, request.scores)

        scores = student_service.get_company_scores(user_id)

        return CompanyScoresResponse(
            companies=scores.get("companies", {}) if scores else {}
        )

    except Exception as e:
        logger.error(f"Error adding company score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding company score",
        )


@router.patch("/student/{user_id}/company-scores/{company}", status_code=200)
async def update_company_score(
    user_id: str,
    company: str,
    request: CompanyScoresRequest,
    admin: CurrentUser = Depends(get_admin_user),
) -> CompanyScoresResponse:
    """
    Update company scores for student

    Args:
        user_id: Student user ID
        company: Company name
        request: Company scores request
        admin: Admin user

    Returns:
        Updated company scores
    """
    try:
        student_service.update_company_score(user_id, company, request.scores)

        scores = student_service.get_company_scores(user_id)

        return CompanyScoresResponse(
            companies=scores.get("companies", {}) if scores else {}
        )

    except Exception as e:
        logger.error(f"Error updating company score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company score",
        )


@router.post("/student/{user_id}/exams", status_code=201)
async def add_exam_score(
    user_id: str,
    request: ExamScore,
    admin: CurrentUser = Depends(get_admin_user),
) -> dict[str, Any]:
    """
    Add exam score for student

    Args:
        user_id: Student user ID
        request: Exam score
        admin: Admin user

    Returns:
        Created exam with ID
    """
    try:
        success, exam_id = student_service.add_exam_score(user_id, request.total_score)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error adding exam: {exam_id}",
            )

        return {
            "id": exam_id,
            "user_id": user_id,
            "total_score": request.total_score,
            "status": "created",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding exam score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding exam score",
        )
