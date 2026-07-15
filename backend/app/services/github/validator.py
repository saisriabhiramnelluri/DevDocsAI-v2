"""
DevDocsAI — GitHub Repository Validator
Checks that a GitHub URL is valid and the repository is accessible
"""
import re
from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# GitHub URL pattern: https://github.com/{owner}/{repo}
GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[a-zA-Z0-9_.-]+)/(?P<repo>[a-zA-Z0-9_.-]+)/?$"
)


@dataclass
class RepoInfo:
    owner: str
    repo_name: str
    default_branch: str
    language: Optional[str]
    size_kb: int
    is_accessible: bool
    clone_url: str
    description: Optional[str]


class GitHubValidator:
    def __init__(self) -> None:
        self.headers: dict = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token}"

    def parse_github_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Returns (owner, repo_name, error_message)."""
        url = url.strip().rstrip("/")
        match = GITHUB_URL_PATTERN.match(url)
        if not match:
            return None, None, "Invalid GitHub URL format. Expected: https://github.com/owner/repo"
        owner = match.group("owner")
        repo = match.group("repo")
        # Strip .git suffix if present
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo, None

    async def validate_and_fetch_info(self, repo_url: str) -> Tuple[Optional[RepoInfo], Optional[str]]:
        """
        Validates the repo URL and fetches metadata from GitHub API.
        Returns (RepoInfo, None) on success or (None, error_message) on failure.
        """
        owner, repo_name, parse_error = self.parse_github_url(repo_url)
        if parse_error:
            return None, parse_error

        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(api_url, headers=self.headers)
        except httpx.TimeoutException:
            return None, "GitHub API request timed out. Please try again."
        except httpx.RequestError as e:
            return None, f"Network error reaching GitHub: {str(e)}"

        if response.status_code == 404:
            return None, f"Repository not found: {repo_url}. Check if it is public."
        if response.status_code == 403:
            return None, "GitHub API rate limit exceeded. Please add a GitHub token."
        if response.status_code != 200:
            return None, f"GitHub API returned {response.status_code}. Please try again."

        data = response.json()

        # Check repo size
        size_kb = data.get("size", 0)
        max_size_kb = settings.max_repo_size_mb * 1024
        if size_kb > max_size_kb:
            return None, (
                f"Repository is too large ({size_kb // 1024} MB). "
                f"Maximum allowed is {settings.max_repo_size_mb} MB."
            )

        if data.get("private", False):
            return None, "Private repositories are not supported yet. Please use a public repository."

        repo_info = RepoInfo(
            owner=owner,
            repo_name=repo_name,
            default_branch=data.get("default_branch", "main"),
            language=data.get("language"),
            size_kb=size_kb,
            is_accessible=True,
            clone_url=data.get("clone_url", f"https://github.com/{owner}/{repo_name}.git"),
            description=data.get("description"),
        )

        logger.info(
            "Repository validated",
            owner=owner,
            repo=repo_name,
            language=repo_info.language,
            size_kb=size_kb,
        )
        return repo_info, None
