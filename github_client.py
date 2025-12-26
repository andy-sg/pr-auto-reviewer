"""GitHub API client for fetching PR and review information."""
from github import Github
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview
from typing import List, Dict, Any, Tuple, Set
import re
from config import Config


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self):
        self.github = Github(Config.GITHUB_TOKEN)

    def parse_pr_url(self, pr_url: str) -> Tuple[str, str, int]:
        """
        Parse PR URL to extract owner, repo, and PR number.

        Args:
            pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)

        Returns:
            Tuple of (owner, repo, pr_number)
        """
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, pr_url)

        if not match:
            raise ValueError(f"Invalid PR URL: {pr_url}")

        owner, repo, pr_number = match.groups()
        return owner, repo, int(pr_number)

    def get_pull_request(self, pr_url: str) -> PullRequest:
        """
        Get pull request object from URL.

        Args:
            pr_url: GitHub PR URL

        Returns:
            PullRequest object
        """
        owner, repo, pr_number = self.parse_pr_url(pr_url)
        repository = self.github.get_repo(f"{owner}/{repo}")
        return repository.get_pull(pr_number)

    def get_pr_context(self, pr: PullRequest) -> Dict[str, Any]:
        """
        Get PR context information.

        Args:
            pr: PullRequest object

        Returns:
            Dict with PR context
        """
        return {
            "title": pr.title,
            "description": pr.body or "",
            "number": pr.number,
            "base_branch": pr.base.ref,
            "head_branch": pr.head.ref,
            "state": pr.state,
            "author": pr.user.login
        }

    def get_reviews(self, pr: PullRequest) -> List[PullRequestReview]:
        """
        Get all reviews for a PR.

        Args:
            pr: PullRequest object

        Returns:
            List of PullRequestReview objects
        """
        return list(pr.get_reviews())

    def get_review_comments(self, pr: PullRequest) -> List[Dict[str, Any]]:
        """
        Get all review comments with file context.

        Args:
            pr: PullRequest object

        Returns:
            List of dicts with review comment information
        """
        comments = []
        for comment in pr.get_review_comments():
            comments.append({
                "id": comment.id,
                "body": comment.body,
                "path": comment.path,
                "position": comment.position,
                "line": comment.line,
                "original_line": comment.original_line,
                "commit_id": comment.commit_id,
                "user": comment.user.login,
                "created_at": comment.created_at,
                "in_reply_to_id": comment.in_reply_to_id
            })
        return comments

    def get_file_content(self, pr: PullRequest, file_path: str) -> str:
        """
        Get the content of a file from the PR's head commit.

        Args:
            pr: PullRequest object
            file_path: Path to the file in the repo

        Returns:
            File content as string
        """
        repo = pr.base.repo
        try:
            file_content = repo.get_contents(file_path, ref=pr.head.sha)
            return file_content.decoded_content.decode('utf-8')
        except Exception as e:
            raise FileNotFoundError(f"Could not fetch file {file_path}: {str(e)}")

    def post_review_comment_reply(
        self,
        pr: PullRequest,
        comment_id: int,
        reply_text: str
    ) -> None:
        """
        Post a reply to a review comment.

        Args:
            pr: PullRequest object
            comment_id: ID of the comment to reply to
            reply_text: Reply text
        """
        # Get the review comment
        comment = pr.get_review_comment(comment_id)
        # Reply to it
        comment.create_reaction("+1")  # Optional: add a reaction
        # Note: PyGithub doesn't have a direct reply method,
        # so we create a new review comment in reply
        pr.create_review_comment_reply(comment_id, reply_text)

    def get_unresolved_comments(self, pr: PullRequest) -> List[Dict[str, Any]]:
        """
        Get unresolved review comments.

        Args:
            pr: PullRequest object

        Returns:
            List of unresolved comment dicts
        """
        comments = self.get_review_comments(pr)
        # Filter for comments that don't have replies yet
        # This is a simple heuristic - you might want to refine this
        unresolved = [c for c in comments if c['in_reply_to_id'] is None]
        return unresolved

    def get_pr_files(self, pr: PullRequest) -> List[Dict[str, Any]]:
        """
        Get all files changed in the PR with their diffs.

        Args:
            pr: PullRequest object

        Returns:
            List of dicts with file information
        """
        files = []
        for file in pr.get_files():
            files.append({
                "filename": file.filename,
                "status": file.status,  # added, modified, removed, renamed
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "patch": file.patch if hasattr(file, 'patch') else None,
                "sha": file.sha
            })
        return files

    @staticmethod
    def parse_patch_lines(patch: str) -> Set[int]:
        """
        Parse a git patch and extract line numbers where comments can be added.

        Args:
            patch: Git diff patch string

        Returns:
            Set of valid line numbers (in the new file) where comments can be added
        """
        valid_lines = set()
        if not patch:
            return valid_lines

        current_line = 0
        for line in patch.split('\n'):
            # Parse hunk headers like @@ -10,5 +10,7 @@
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1))
                continue

            # Lines starting with + are new lines (can comment)
            if line.startswith('+') and not line.startswith('+++'):
                valid_lines.add(current_line)
                current_line += 1
            # Lines starting with space are context lines (can also comment)
            elif line.startswith(' '):
                valid_lines.add(current_line)
                current_line += 1
            # Lines starting with - are deleted lines (increment in old file, not new)
            elif line.startswith('-') and not line.startswith('---'):
                # Don't increment current_line for deletions
                pass

        return valid_lines

    def create_review(
        self,
        pr: PullRequest,
        comments: List[Dict[str, Any]],
        body: str = None,
        event: str = "COMMENT",
        patches: Dict[str, str] = None
    ) -> None:
        """
        Create a review with multiple comments.

        Args:
            pr: PullRequest object
            comments: List of review comments with line, body, path
            body: Overall review body (optional)
            event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)
            patches: Optional dict mapping file paths to their patches for validation
        """
        # Format comments for GitHub API
        review_comments = []
        skipped_comments = []

        for comment in comments:
            file_path = comment.get("path")
            line = comment.get("line")

            # Validate line number if patch is provided
            if patches and file_path in patches:
                valid_lines = self.parse_patch_lines(patches[file_path])
                if line not in valid_lines:
                    skipped_comments.append({
                        "path": file_path,
                        "line": line,
                        "reason": "Line not in diff"
                    })
                    continue

            review_comments.append({
                "path": file_path,
                "line": line,
                "body": comment.get("body"),
                "side": comment.get("side", "RIGHT")
            })

        # Log skipped comments if any
        if skipped_comments:
            import sys
            from rich.console import Console
            console = Console(file=sys.stderr)
            console.print(f"[yellow]Skipped {len(skipped_comments)} comment(s) with invalid line numbers[/yellow]")

        # Create the review
        if review_comments:
            pr.create_review(
                body=body or "Automated code review",
                event=event,
                comments=review_comments
            )
        elif body:
            # Just post a comment if no inline comments
            pr.create_issue_comment(body)
