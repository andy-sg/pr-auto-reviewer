"""Git operations for committing and pushing changes."""
import git
from typing import List, Optional


class GitOperations:
    """Handles Git operations."""

    def __init__(self, repo_path: str):
        """
        Initialize Git operations.

        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def get_current_branch(self) -> str:
        """Get the current branch name."""
        return self.repo.active_branch.name

    def stage_files(self, file_paths: List[str]) -> None:
        """
        Stage files for commit.

        Args:
            file_paths: List of file paths to stage (relative to repo root)
        """
        self.repo.index.add(file_paths)

    def commit(self, message: str, author_name: Optional[str] = None,
               author_email: Optional[str] = None) -> str:
        """
        Create a commit.

        Args:
            message: Commit message
            author_name: Optional author name
            author_email: Optional author email

        Returns:
            Commit SHA
        """
        if author_name and author_email:
            author = git.Actor(author_name, author_email)
            commit = self.repo.index.commit(message, author=author)
        else:
            commit = self.repo.index.commit(message)

        return commit.hexsha

    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> None:
        """
        Push commits to remote.

        Args:
            remote: Remote name (default: 'origin')
            branch: Branch name (default: current branch)
        """
        if branch is None:
            branch = self.get_current_branch()

        origin = self.repo.remote(remote)
        origin.push(branch)

    def has_changes(self) -> bool:
        """Check if there are any uncommitted changes."""
        return (
            len(self.repo.index.diff(None)) > 0 or  # Modified files
            len(self.repo.index.diff("HEAD")) > 0 or  # Staged files
            len(self.repo.untracked_files) > 0  # Untracked files
        )

    def get_changed_files(self) -> List[str]:
        """Get list of changed files."""
        changed = []

        # Modified files
        for item in self.repo.index.diff(None):
            changed.append(item.a_path)

        # Staged files
        for item in self.repo.index.diff("HEAD"):
            changed.append(item.a_path)

        return list(set(changed))

    def commit_and_push(
        self,
        file_paths: List[str],
        commit_message: str,
        remote: str = 'origin'
    ) -> str:
        """
        Stage, commit, and push changes.

        Args:
            file_paths: List of file paths to commit
            commit_message: Commit message
            remote: Remote name

        Returns:
            Commit SHA
        """
        # Stage files
        self.stage_files(file_paths)

        # Commit
        commit_sha = self.commit(commit_message)

        # Push
        self.push(remote=remote)

        return commit_sha
