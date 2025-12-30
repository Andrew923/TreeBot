import json
from typing import Any
from github import Github


class GitHubStorage:
    """Abstraction layer for GitHub-based JSON storage."""

    def __init__(self, github: Github, repo_name: str = 'TreeBot'):
        """
        Initialize GitHub storage.

        Args:
            github: Authenticated PyGithub instance
            repo_name: Name of the repository to use for storage
        """
        self.github = github
        self.repo = github.get_user().get_repo(repo_name)
        self._cache: dict[str, Any] = {}

    def read(self, filename: str) -> dict[str, Any]:
        """
        Read JSON data from GitHub repo.

        Args:
            filename: Name of the file to read

        Returns:
            Parsed dictionary from the file
        """
        file = self.repo.get_contents(filename)
        content = file.decoded_content.decode()

        # Try JSON first (preferred format)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fall back to eval for legacy Python dict format
            # This handles datetime objects and other Python literals
            return eval(content)

    def write(
        self,
        filename: str,
        data: dict[str, Any],
        message: str = 'updated from python'
    ) -> None:
        """
        Write data to GitHub repo.

        Args:
            filename: Name of the file to write
            data: Dictionary to write (will be converted to string)
            message: Commit message
        """
        contents = self.repo.get_contents(filename)
        # Use str() to preserve Python objects like datetime
        # This maintains backwards compatibility with existing data format
        self.repo.update_file(contents.path, message, str(data), contents.sha)
        # Invalidate cache for this file
        self._cache.pop(filename, None)

    def get_cached(self, filename: str) -> dict[str, Any]:
        """
        Get data with caching (useful for frequently accessed files).

        Args:
            filename: Name of the file to read

        Returns:
            Parsed dictionary from the file (cached)
        """
        if filename not in self._cache:
            self._cache[filename] = self.read(filename)
        return self._cache[filename]

    def invalidate_cache(self, filename: str | None = None) -> None:
        """
        Clear cache for a file or all files.

        Args:
            filename: Specific file to invalidate, or None for all
        """
        if filename:
            self._cache.pop(filename, None)
        else:
            self._cache.clear()
