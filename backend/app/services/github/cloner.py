"""
DevDocsAI — GitHub Repository Cloner
Clones a repository to a local temp directory using GitPython
"""
import os
import stat
import shutil
from pathlib import Path
from typing import Optional

import git
from git import Repo

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepositoryCloner:
    def __init__(self) -> None:
        self.clone_base_dir = Path(settings.repo_clone_dir)
        self.clone_base_dir.mkdir(parents=True, exist_ok=True)

    def get_clone_path(self, repo_id: str) -> Path:
        return self.clone_base_dir / repo_id

    async def clone(
        self,
        clone_url: str,
        repo_id: str,
        branch: Optional[str] = None,
    ) -> Path:
        """
        Clone a repository. Returns the local path where it was cloned.
        Uses shallow clone (depth=1) to minimize disk usage.
        """
        clone_path = self.get_clone_path(repo_id)

        # Remove existing if present
        if clone_path.exists():
            shutil.rmtree(clone_path, onerror=remove_readonly)

        clone_kwargs = {
            "depth": 1,
            "single_branch": True,
        }
        if branch:
            clone_kwargs["branch"] = branch

        logger.info("Cloning repository", url=clone_url, path=str(clone_path))
        try:
            Repo.clone_from(
                clone_url,
                str(clone_path),
                **clone_kwargs,
            )
        except git.GitCommandError as e:
            logger.error("Git clone failed", url=clone_url, error=str(e))
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")

        logger.info("Repository cloned successfully", path=str(clone_path))
        return clone_path

    def cleanup(self, repo_id: str) -> None:
        """Delete the cloned repository from disk."""
        clone_path = self.get_clone_path(repo_id)
        if clone_path.exists():
            shutil.rmtree(clone_path, onerror=remove_readonly)
            logger.info("Cleaned up cloned repository", repo_id=repo_id)

    def get_file_list(self, repo_id: str, extensions: Optional[list] = None) -> list[Path]:
        """
        Walk the cloned repo and return all source files.
        Skips common non-code directories.
        """
        clone_path = self.get_clone_path(repo_id)
        if not clone_path.exists():
            return []

        SKIP_DIRS = {
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            "dist", "build", ".next", "coverage", ".pytest_cache",
            ".mypy_cache", "vendor", "target", "bin", "obj",
        }

        files = []
        for path in clone_path.rglob("*"):
            if path.is_file():
                # Skip hidden and build directories
                if any(part in SKIP_DIRS for part in path.parts):
                    continue
                if any(part.startswith(".") for part in path.parts[len(clone_path.parts):]):
                    continue
                if extensions is None or path.suffix in extensions:
                    files.append(path)

        logger.info("Found source files", count=len(files), repo_id=repo_id)
        return files
