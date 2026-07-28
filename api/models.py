"""Request and response schemas for the coaching API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A document to put in front of the coach for this message only.

    Documents are inlined into the user turn, exactly as the run_session_*
    scripts do. They are context for one message — the coach decides what,
    if anything, is worth writing to the client's memory store.
    """

    name: str = Field(..., examples=["physio-update-2026-07-22.md"])
    content: str


class CreateClientRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, examples=["Marco Ferreira"])


class Client(BaseModel):
    client_id: str
    name: str
    memory_store_id: str
    created_at: datetime


class MessageRequest(BaseModel):
    text: str = Field(..., min_length=1, examples=["Give me my workout for tomorrow."])
    documents: list[Document] = Field(default_factory=list)


class Memory(BaseModel):
    memory_id: str
    path: str
    size_bytes: int
    content: str | None = None


class MemoryList(BaseModel):
    memory_store_id: str
    memories: list[Memory]


# --- SSE payloads -----------------------------------------------------------
# Documented here so the shape is discoverable, even though the streaming
# endpoint returns text/event-stream rather than a modelled JSON body.


class StatusEvent(BaseModel):
    type: Literal["status"] = "status"
    session_id: str
    state: str


class ToolUseEvent(BaseModel):
    type: Literal["tool_use"] = "tool_use"
    tool: str
    target: str | None = None
    is_memory: bool = False


class MessageEvent(BaseModel):
    type: Literal["message"] = "message"
    text: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    session_id: str
    answer: str
    memory_writes: list[str]


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    detail: str
