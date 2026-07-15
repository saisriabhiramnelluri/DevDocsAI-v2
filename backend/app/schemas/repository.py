"""
DevDocsAI — Pydantic Schemas (Repository)
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


# ── Request ──────────────────────────────────────────────────────────────────

class RepositoryAnalyzeRequest(BaseModel):
    repo_url: str

    @field_validator("repo_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if not v.startswith(("https://github.com/", "http://github.com/")):
            raise ValueError("Only GitHub URLs are supported (https://github.com/...)")
        return v


# ── Response ─────────────────────────────────────────────────────────────────

class RepositoryMetadataOut(BaseModel):
    summary: Optional[str] = None
    framework: Optional[str] = None
    architecture_type: Optional[str] = None
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_lines: int = 0
    languages_detected: Optional[str] = None

    model_config = {"from_attributes": True}


class RepositoryOut(BaseModel):
    id: str
    repo_url: str
    repo_name: Optional[str] = None
    owner: Optional[str] = None
    status: str
    progress: int
    current_stage: Optional[str] = None
    primary_language: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    metadata_: Optional[RepositoryMetadataOut] = None

    model_config = {"from_attributes": True}


class RepositoryStatusOut(BaseModel):
    repo_id: str
    status: str
    progress: int
    current_stage: Optional[str] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class RepositoryAnalyzeResponse(BaseModel):
    repo_id: str
    status: str
    message: str


class RepositoryListOut(BaseModel):
    repositories: list[RepositoryOut]
    total: int
