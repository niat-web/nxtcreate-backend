"""
Authentication routes for this 
"""

import logging
import os

import requests
from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import get_current_user
from app.models.user_model import CurrentUser, LoginRequest, LoginResponse, UserResponse
from app.services.firebase import FirebaseService
from app.services.user_service import UserService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
firebase = FirebaseService()
user_service = UserService()

# Firebase Web API Key from environment
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(request: LoginRequest) -> LoginResponse:
    """
    Login with email and password using Firebase Authentication

    Args:
        request: Login credentials (email and password)

    Returns:
        LoginResponse with ID token and user info

    Note:
        - Uses Firebase REST API for password verification
        - Returns ID token for subsequent authenticated requests
    """
    try:
        # Get Firebase credentials from environment
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        web_api_key = os.getenv("FIREBASE_WEB_API_KEY")

        if not project_id:
            logger.error("Firebase project ID not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Firebase configuration error",
            )

        # Verify user exists in Firebase Authentication
        user = firebase.get_user_by_email(request.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Get user data from Firestore
        user_data = user_service.get_user(user.uid)
        print(user_data)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database",
            )

        # Generate ID token using Firebase REST API signInWithPassword
        id_token = _generate_id_token_via_rest_api(request.email, request.password, web_api_key)
        
        if not id_token:
            logger.error(f"❌ Could not generate ID token for user {user.uid}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authentication token. Please check your Firebase configuration.",
            )

        return LoginResponse(
            id_token=id_token,
            user_id=user.uid,
            email=user.email,
            name=user_data.get("name", ""),
            role=user_data.get("role", "student"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


def _generate_id_token_via_rest_api(email: str, password: str, web_api_key: str) -> str:
    """
    Generate a unique ID token using Firebase REST API signInWithPassword
    
    This is the standard Firebase authentication flow that generates a fresh,
    unique ID token each time with a current timestamp (iat claim).

    Args:
        email: User email
        password: User password
        web_api_key: Firebase Web API key

    Returns:
        ID token string or empty string if failed
    """
    try:
        if not web_api_key:
            logger.error("❌ FIREBASE_WEB_API_KEY is NOT set in environment!")
            return ""
        
        # Firebase REST API endpoint for password authentication
        url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        params = {"key": web_api_key}
        
        logger.info(f"🔄 Authenticating user via Firebase REST API...")
        logger.info(f"   Email: {email}")
        logger.info(f"   API Key length: {len(web_api_key)} chars")
        logger.info(f"   Endpoint: {url}")
        
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        logger.info(f"📊 Authentication response status: {response.status_code}")
        logger.info(f"📄 Authentication response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            id_token = data.get("idToken", "")
            
            if id_token:
                # Log token metadata for verification
                import json
                import base64
                
                # Decode JWT header + payload (without verification)
                try:
                    parts = id_token.split('.')
                    if len(parts) >= 2:
                        payload_decoded = base64.urlsafe_b64decode(parts[1] + '==')
                        token_payload = json.loads(payload_decoded)
                        logger.info(f"✅ Generated unique ID token")
                        logger.info(f"   Token iat (issued at): {token_payload.get('iat', 'N/A')}")
                        logger.info(f"   Token exp (expiration): {token_payload.get('exp', 'N/A')}")
                        logger.info(f"   Token email: {token_payload.get('email', 'N/A')}")
                except Exception as decode_err:
                    logger.warning(f"Could not decode token metadata: {decode_err}")
                    logger.info(f"✅ Generated unique ID token")
                
                return id_token
            else:
                logger.error(f"❌ No idToken in response: {data}")
                return ""
        else:
            logger.error(f"❌ Password authentication failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return ""
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error during authentication: {str(e)}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return ""
    except Exception as e:
        logger.error(f"❌ Error generating ID token: {str(e)}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return ""


def _generate_id_token(user_id: str, web_api_key: str, project_id: str) -> str:
    """
    DEPRECATED: Use _generate_id_token_via_rest_api instead.
    
    This function is kept for backwards compatibility but should not be used
    for new implementations as it doesn't generate unique tokens each time.
    """
    try:
        from firebase_admin import auth
        
        # Create a custom token (claims token signed with service account)
        custom_token = auth.create_custom_token(user_id)
        
        # Decode if it's bytes
        if isinstance(custom_token, bytes):
            custom_token = custom_token.decode('utf-8')
        
        logger.info(f"✅ Created custom token for user {user_id}")
        
        # Exchange custom token for ID token using Firebase REST API
        if not web_api_key:
            logger.error("❌ FIREBASE_WEB_API_KEY is NOT set in environment!")
            logger.error("   This will cause token verification to fail on protected endpoints")
            return ""
        
        logger.debug(f"🔑 FIREBASE_WEB_API_KEY is set ({len(web_api_key)} chars)")
        id_token = _exchange_token_for_id_token(custom_token, web_api_key)
        
        if id_token:
            return id_token
        else:
            logger.error(f"❌ Failed to exchange custom token for user {user_id}")
            return ""
            
    except Exception as e:
        logger.error(f"Error generating ID token: {str(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return ""


def _exchange_token_for_id_token(custom_token: str, web_api_key: str) -> str:
    """
    Exchange custom token for ID token using Firebase REST API

    Args:
        custom_token: Custom token from service account
        web_api_key: Firebase Web API key

    Returns:
        ID token or empty string if failed
    """
    try:
        # Firebase REST API endpoint to exchange token
        url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
        
        payload = {
            "token": custom_token,
            "returnSecureToken": True
        }
        
        params = {"key": web_api_key}
        
        # Debug logging
        logger.info(f"🔄 Attempting token exchange...")
        logger.info(f"   API Key present: {bool(web_api_key)}")
        logger.info(f"   API Key length: {len(web_api_key) if web_api_key else 0}")
        logger.info(f"   Custom token length: {len(custom_token)}")
        logger.info(f"   Endpoint: {url}")
        
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        logger.info(f"📊 Exchange response status: {response.status_code}")
        logger.info(f"📄 Exchange response body: {response.text}")  # Full response
        
        if response.status_code == 200:
            data = response.json()
            id_token = data.get("idToken", "")
            if id_token:
                logger.info("✅ Successfully exchanged custom token for ID token")
                return id_token
            else:
                logger.error(f"❌ No idToken in response: {data}")
                return ""
        else:
            logger.error(f"❌ Failed to exchange token: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return ""
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error exchanging token: {str(e)}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return ""
    except Exception as e:
        logger.error(f"❌ Error exchanging token: {str(e)}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return ""


@router.get("/me", response_model=UserResponse, status_code=200)
async def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user profile

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse with user details
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
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile",
        )
