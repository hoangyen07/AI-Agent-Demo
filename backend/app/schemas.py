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


class ProjectDoc(BaseModel):
    filename: str
    source: str
    chunks: int


class ProjectInfo(BaseModel):
    project_id: str
    project_name: str
    documents: list[ProjectDoc] = []
    total_chunks: int = 0
