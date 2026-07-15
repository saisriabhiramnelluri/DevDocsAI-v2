"""
DevDocsAI — SQLAlchemy ORM Models
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import relationship

from app.database.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    plan = Column(String(20), default="free")  # free | team | enterprise
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    repositories = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    repo_url = Column(String(500), nullable=False)
    repo_name = Column(String(255), nullable=True)
    owner = Column(String(255), nullable=True)
    status = Column(
        String(20),
        default="pending",
    )  # pending | cloning | parsing | embedding | graph | summarizing | ready | failed
    progress = Column(Integer, default=0)  # 0–100
    current_stage = Column(String(100), nullable=True)
    primary_language = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="repositories")
    metadata_ = relationship(
        "RepositoryMetadata",
        back_populates="repository",
        uselist=False,
        cascade="all, delete-orphan",
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository id={self.id} url={self.repo_url} status={self.status}>"


class RepositoryMetadata(Base):
    __tablename__ = "repository_metadata"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    repo_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    summary = Column(Text, nullable=True)
    framework = Column(String(100), nullable=True)
    architecture_type = Column(String(100), nullable=True)
    total_files = Column(Integer, default=0)
    total_functions = Column(Integer, default=0)
    total_classes = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    languages_detected = Column(Text, nullable=True)  # JSON string
    readme_content = Column(Text, nullable=True)
    api_doc_content = Column(Text, nullable=True)
    onboarding_content = Column(Text, nullable=True)
    architecture_summary = Column(Text, nullable=True)
    mermaid_diagram = Column(Text, nullable=True)

    repository = relationship("Repository", back_populates="metadata_")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    repo_id = Column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    repository = relationship("Repository", back_populates="chat_sessions")
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} repo_id={self.repo_id}>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    session_id = Column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string of source files
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role}>"
