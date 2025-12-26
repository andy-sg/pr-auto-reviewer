"""Code modification logic."""
import os
from typing import Dict, Any
from models.base import BaseModel


class CodeModifier:
    """Handles code modifications based on review comments."""

    def __init__(self, model: BaseModel, repo_path: str):
        """
        Initialize code modifier.

        Args:
            model: AI model instance
            repo_path: Path to the local repository
        """
        self.model = model
        self.repo_path = repo_path

    def apply_fix(
        self,
        file_path: str,
        review_comment: str,
        pr_context: Dict[str, Any],
        line_number: int = None
    ) -> Dict[str, Any]:
        """
        Apply a fix based on review comment.

        Args:
            file_path: Relative path to the file in the repo
            review_comment: Review comment text
            pr_context: PR context information
            line_number: Optional line number

        Returns:
            Dict with results:
                - success: bool
                - file_path: str
                - changes_made: str
                - error: str (if failed)
        """
        full_path = os.path.join(self.repo_path, file_path)

        # Check if file exists
        if not os.path.exists(full_path):
            return {
                "success": False,
                "file_path": file_path,
                "changes_made": "",
                "error": f"File not found: {file_path}"
            }

        # Read current file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "changes_made": "",
                "error": f"Failed to read file: {str(e)}"
            }

        # Analyze what needs to be done
        analysis = self.model.analyze_review(
            file_content=current_content,
            file_path=file_path,
            review_comment=review_comment,
            pr_context=pr_context
        )

        if analysis['action'] == 'no_action':
            return {
                "success": True,
                "file_path": file_path,
                "changes_made": "No changes needed",
                "reasoning": analysis['reasoning']
            }

        # Generate fixed code
        try:
            fixed_content = self.model.generate_code_fix(
                file_content=current_content,
                file_path=file_path,
                review_comment=review_comment,
                line_number=line_number
            )

            # Write fixed content back to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

            changes_summary = f"Applied fix: {analysis['reasoning']}"
            if analysis['changes']:
                changes_summary += "\n- " + "\n- ".join(analysis['changes'])

            return {
                "success": True,
                "file_path": file_path,
                "changes_made": changes_summary,
                "reasoning": analysis['reasoning']
            }

        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "changes_made": "",
                "error": f"Failed to apply fix: {str(e)}"
            }

    def get_file_content(self, file_path: str) -> str:
        """
        Get content of a file in the repository.

        Args:
            file_path: Relative path to the file

        Returns:
            File content as string
        """
        full_path = os.path.join(self.repo_path, file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
