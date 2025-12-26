"""Code review logic for analyzing PRs and generating review comments."""
from typing import List, Dict, Any
from models.base import BaseModel
from github import PullRequest


class CodeReviewer:
    """Handles automatic code review of PRs."""

    def __init__(self, model: BaseModel):
        """
        Initialize code reviewer.

        Args:
            model: AI model instance
        """
        self.model = model

    def analyze_file_changes(
        self,
        file_path: str,
        patch: str,
        file_content: str,
        pr_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze changes in a file and generate review comments.

        Args:
            file_path: Path to the file
            patch: Git diff patch
            file_content: Full file content after changes
            pr_context: PR context information

        Returns:
            List of review comments with:
                - body: Comment text
                - line: Line number to comment on
                - side: 'RIGHT' (new version)
        """
        if not hasattr(self.model, 'review_code'):
            # Fallback to a generic prompt if model doesn't have review_code method
            return self._review_with_generic_prompt(
                file_path, patch, file_content, pr_context
            )

        return self.model.review_code(
            file_path=file_path,
            patch=patch,
            file_content=file_content,
            pr_context=pr_context
        )

    def _review_with_generic_prompt(
        self,
        file_path: str,
        patch: str,
        file_content: str,
        pr_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fallback method to review code using generic AI prompt.

        Args:
            file_path: Path to the file
            patch: Git diff patch
            file_content: Full file content
            pr_context: PR context

        Returns:
            List of review comments
        """
        # For now, return empty list
        # This will be implemented when we add review_code method to models
        return []

    def generate_summary_comment(
        self,
        pr_context: Dict[str, Any],
        all_comments: List[Dict[str, Any]],
        files_reviewed: int
    ) -> str:
        """
        Generate a summary comment for the PR review.

        Args:
            pr_context: PR context information
            all_comments: All individual review comments
            files_reviewed: Number of files reviewed

        Returns:
            Summary comment text
        """
        num_comments = len(all_comments)

        if num_comments == 0:
            return f"""## 🤖 AI Code Review Summary

Reviewed {files_reviewed} file(s). No issues found! ✅

The code looks good to merge.

*Automated review powered by AI*"""

        return f"""## 🤖 AI Code Review Summary

Reviewed {files_reviewed} file(s) and found {num_comments} suggestion(s).

Please review the inline comments for details.

*Automated review powered by AI*"""
