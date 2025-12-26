"""Base model interface for AI providers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseModel(ABC):
    """Abstract base class for AI model implementations."""

    def review_code(
        self,
        file_path: str,
        patch: str,
        file_content: str,
        pr_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Review code changes and generate review comments.

        Args:
            file_path: Path to the file being reviewed
            patch: Git diff patch showing the changes
            file_content: Full file content after changes
            pr_context: Additional context about the PR

        Returns:
            List of review comments, each with:
                - body: Comment text
                - line: Line number to comment on
                - side: 'RIGHT' (for new version of the file)
        """
        # Default implementation - subclasses can override
        return []

    @abstractmethod
    def analyze_review(
        self,
        file_content: str,
        file_path: str,
        review_comment: str,
        pr_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a review comment and determine what changes are needed.

        Args:
            file_content: Current content of the file
            file_path: Path to the file being reviewed
            review_comment: The review comment text
            pr_context: Additional context about the PR (title, description, etc.)

        Returns:
            Dict containing:
                - action: Type of action needed (modify, create, delete, no_action)
                - changes: List of changes to make
                - reasoning: Explanation of the changes
        """
        pass

    @abstractmethod
    def generate_code_fix(
        self,
        file_content: str,
        file_path: str,
        review_comment: str,
        line_number: int = None
    ) -> str:
        """
        Generate fixed code based on review comment.

        Args:
            file_content: Current content of the file
            file_path: Path to the file
            review_comment: The review comment
            line_number: Specific line number if applicable

        Returns:
            Fixed file content as string
        """
        pass

    @abstractmethod
    def generate_reply(
        self,
        review_comment: str,
        changes_made: str
    ) -> str:
        """
        Generate a reply to the review comment.

        Args:
            review_comment: Original review comment
            changes_made: Description of changes made

        Returns:
            Reply text
        """
        pass
