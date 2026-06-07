from pydantic import BaseModel
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    dev = "dev"
    qc = "qc"


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    project_id: str
    user_role: UserRole
    message: str
    history: list[ChatMessage] = []


class UploadResponse(BaseModel):
    status: str
    message: str
    chunks_added: int
    project_id: str
    version: int = 1
    is_new_version: bool = False


class ProjectDoc(BaseModel):
    filename: str
    source: str
    chunks: int


class ProjectInfo(BaseModel):
    project_id: str
    project_name: str
    documents: list[ProjectDoc] = []
    total_chunks: int = 0


class VersionInfo(BaseModel):
    version: int
    filename: str
    uploaded_at: str
    chunks_count: int
    hash: str


class VersionedDoc(BaseModel):
    filename: str
    total_versions: int
    latest_version: int
    latest_uploaded_at: str
    chunks_count: int


class DiffRequest(BaseModel):
    filename: str
    version_a: int
    version_b: int


class DiffResponse(BaseModel):
    project_id: str
    filename: str
    version_old: int
    version_new: int
    analysis: str
