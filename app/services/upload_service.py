"""
Upload service for handling file uploads and bulk operations
"""

import logging
import os
import tempfile
from typing import Any, Optional

from app.services.firebase import FirebaseService
from app.services.user_service import UserService
from app.services.student_service import StudentService
from app.utils.excel_parser import ExcelParser
from app.utils.validators import (
    validate_batch,
    validate_category,
    validate_email,
    validate_name,
    validate_password,
)


logger = logging.getLogger(__name__)


class UploadService:
    """
    Service for handling file uploads and bulk operations
    """

    def __init__(self):
        """Initialize upload service"""
        self.firebase = FirebaseService()
        self.user_service = UserService()
        self.student_service = StudentService()

    async def process_excel_upload(
        self, file_content: bytes, filename: str
    ) -> tuple[int, int, list[str]]:
        """
        Process Excel file for bulk student uploads

        Args:
            file_content: File content bytes
            filename: Original filename

        Returns:
            Tuple of (successful_uploads, failed_uploads, errors)
        """
        errors = []
        successful = 0
        failed = 0

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".xlsx", dir=tempfile.gettempdir()
        ) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            # Parse Excel file
            data, parse_errors = ExcelParser.parse_file(tmp_path)

            if parse_errors:
                errors.extend(parse_errors)

            if not data:
                return 0, 0, errors

            # Process each row
            for row_idx, row in enumerate(data, 2):
                try:
                    # Validate data
                    name = str(row.get("name", "")).strip()
                    email = str(row.get("email", "")).strip()
                    batch = str(row.get("batch", "")).strip()
                    password = str(row.get("password", "")).strip()
                    category = str(row.get("category", "")).strip().upper()

                    # Validate each field
                    is_valid, msg = validate_name(name)
                    if not is_valid:
                        errors.append(f"Row {row_idx}: {msg}")
                        failed += 1
                        continue

                    if not validate_email(email):
                        errors.append(f"Row {row_idx}: Invalid email format")
                        failed += 1
                        continue

                    is_valid, msg = validate_batch(batch)
                    if not is_valid:
                        errors.append(f"Row {row_idx}: {msg}")
                        failed += 1
                        continue

                    is_valid, msg = validate_password(password)
                    if not is_valid:
                        errors.append(f"Row {row_idx}: {msg}")
                        failed += 1
                        continue

                    is_valid, msg = validate_category(category)
                    if not is_valid:
                        errors.append(f"Row {row_idx}: {msg}")
                        failed += 1
                        continue

                    # Check email uniqueness
                    if self.user_service.user_exists(email):
                        errors.append(f"Row {row_idx}: Email {email} already exists")
                        failed += 1
                        continue

                    # Create user
                    result = self._create_student(name, email, password, batch, category)

                    if result[0]:
                        successful += 1
                    else:
                        errors.append(f"Row {row_idx}: {result[1]}")
                        failed += 1

                except Exception as e:
                    logger.error(f"Error processing row {row_idx}: {str(e)}")
                    errors.append(f"Row {row_idx}: {str(e)}")
                    failed += 1

        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.error(f"Error cleaning up temp file: {str(e)}")

        return successful, failed, errors

    def _create_student(
        self, name: str, email: str, password: str, batch: str, category: str
    ) -> tuple[bool, Optional[str]]:
        """
        Create a student user

        Args:
            name: Student name
            email: Student email
            password: Student password
            batch: Student batch
            category: Student category

        Returns:
            Tuple of (success, error_message or user_id)
        """
        try:
            # Create Firebase Auth user
            firebase_result = self.firebase.create_user(
                email=email, password=password, display_name=name
            )
            user_id = firebase_result["user_id"]

            # Create user in Firestore
            self.user_service.create_user_with_firestore(
                user_id=user_id,
                name=name,
                email=email,
                batch=batch,
                category=category,
                role="student",
            )

            # Initialize student data
            self.student_service.initialize_student_data(user_id)

            logger.info(f"Student created: {user_id} ({email})")
            return True, user_id

        except ValueError as e:
            logger.error(f"Validation error creating student {email}: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error creating student {email}: {str(e)}")
            # Try to clean up Firebase user if Firestore creation failed
            try:
                if "user_id" in locals():
                    self.firebase.delete_user(user_id)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up user: {str(cleanup_error)}")
            return False, str(e)
