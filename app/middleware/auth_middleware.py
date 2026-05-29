"""
Authentication middleware for protecting routes
"""

import logging
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.user_model import CurrentUser
from app.services.firebase import FirebaseService
from app.services.user_service import UserService


logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Dependency for getting current authenticated user

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        CurrentUser with user_id, email, role, and name
    """
    try:
        firebase = FirebaseService()
        user_service = UserService()

        # Verify token
        token = credentials.credentials
        
        # Log token verification attempt (first 50 chars for security)
        logger.debug(f"🔍 Verifying token: {token[:50]}...")
        
        try:
            decoded_token = firebase.verify_id_token(token)
        except ValueError as token_error:
            logger.warning(f"❌ Invalid ID token: {str(token_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid ID token: {str(token_error)}",
            )
        
        user_id = decoded_token.get("uid") or decoded_token.get("user_id")

        if not user_id:
            logger.warning("❌ Token missing user ID (uid claim)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        logger.debug(f"✅ Token verified for user: {user_id}")

        # Get user from Firestore
        user_data = user_service.get_user(user_id)

        if not user_data:
            logger.warning(f"❌ User {user_id} not found in Firestore")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database",
            )

        logger.debug(f"✅ User found: {user_data.get('email')} (role: {user_data.get('role')})")

        return CurrentUser(
            user_id=user_id,
            email=user_data.get("email", ""),
            role=user_data.get("role", "student"),
            name=user_data.get("name", ""),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"❌ Authentication validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"❌ Unexpected authentication error: {str(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


def get_admin_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Dependency for admin-only routes

    Args:
        current_user: Current authenticated user

    Returns:
        CurrentUser if user is admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        logger.warning(f"Unauthorized admin access attempt: {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def get_student_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Dependency for student-only routes

    Args:
        current_user: Current authenticated user

    Returns:
        CurrentUser if user is student

    Raises:
        HTTPException: If user is not student
    """
    if current_user.role != "student":
        logger.warning(f"Unauthorized student access attempt: {current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user
