"""
Student service for managing student-specific operations
"""

import logging
from datetime import datetime
from typing import Any, Optional

from app.services.firebase import FirebaseService


logger = logging.getLogger(__name__)


class StudentService:
    """
    Service for student-related operations
    """

    def __init__(self):
        """Initialize student service"""
        self.firebase = FirebaseService()

    def initialize_student_data(self, user_id: str) -> bool:
        """
        Initialize student data structures

        Args:
            user_id: Student user ID

        Returns:
            True if successful
        """
        try:
            # Initialize student_categories
            self.firebase.set_document(
                "student_categories",
                user_id,
                {"category": "", "data": {}},
            )

            # Initialize company_scores
            self.firebase.set_document(
                "company_scores",
                user_id,
                {"companies": {}},
            )

            logger.info(f"Student data initialized: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error initializing student data: {str(e)}")
            raise

    def get_category(self, user_id: str) -> Optional[dict[str, Any]]:
        """
        Get student category and data

        Args:
            user_id: Student user ID

        Returns:
            Category data or None
        """
        try:
            return self.firebase.get_document("student_categories", user_id)
        except Exception as e:
            logger.error(f"Error getting category: {str(e)}")
            return None

    def update_category_data(
        self, user_id: str, category_data: dict[str, Any]
    ) -> bool:
        """
        Update student category data

        Args:
            user_id: Student user ID
            category_data: Category data to update

        Returns:
            True if successful
        """
        try:
            self.firebase.update_document(
                "student_categories",
                user_id,
                {"data": category_data},
            )
            logger.info(f"Category data updated: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating category data: {str(e)}")
            raise

    def get_company_scores(self, user_id: str) -> Optional[dict[str, Any]]:
        """
        Get student company scores

        Args:
            user_id: Student user ID

        Returns:
            Company scores or None
        """
        try:
            return self.firebase.get_document("company_scores", user_id)
        except Exception as e:
            logger.error(f"Error getting company scores: {str(e)}")
            return None

    def add_company_score(
        self, user_id: str, company: str, scores: dict[str, float]
    ) -> bool:
        """
        Add or update company score

        Args:
            user_id: Student user ID
            company: Company name
            scores: Company scores

        Returns:
            True if successful
        """
        try:
            current = self.firebase.get_document("company_scores", user_id)
            if current is None:
                companies = {}
            else:
                companies = current.get("companies", {})

            companies[company] = scores
            self.firebase.update_document(
                "company_scores",
                user_id,
                {"companies": companies},
            )
            logger.info(f"Company score added: {user_id}/{company}")
            return True
        except Exception as e:
            logger.error(f"Error adding company score: {str(e)}")
            raise

    def update_company_score(
        self, user_id: str, company: str, scores: dict[str, float]
    ) -> bool:
        """
        Update existing company score

        Args:
            user_id: Student user ID
            company: Company name
            scores: Updated scores

        Returns:
            True if successful
        """
        return self.add_company_score(user_id, company, scores)

    def add_exam_score(
        self, user_id: str, total_score: float
    ) -> tuple[bool, Optional[str]]:
        """
        Add exam score for student

        Args:
            user_id: Student user ID
            total_score: Total exam score

        Returns:
            Tuple of (success, exam_id or error_message)
        """
        try:
            exam_data = {
                "user_id": user_id,
                "total_score": total_score,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Create document with auto-generated ID
            doc_ref = self.firebase._db.collection("fortnight_exams").document()
            doc_ref.set(exam_data)

            logger.info(f"Exam score added: {user_id}/{doc_ref.id}")
            return True, doc_ref.id
        except Exception as e:
            logger.error(f"Error adding exam score: {str(e)}")
            return False, str(e)

    def get_exams(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all exams for a student

        Args:
            user_id: Student user ID

        Returns:
            List of exams
        """
        try:
            exams = self.firebase.query_collection(
                "fortnight_exams", "user_id", "==", user_id
            )
            return exams
        except Exception as e:
            logger.error(f"Error getting exams: {str(e)}")
            return []
