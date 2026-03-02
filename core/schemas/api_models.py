from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    domain: str
    org: str
    usecase: str
    message: str


class ToolTraceEntry(BaseModel):
    tool_name: str
    input: dict[str, Any]
    output_summary: str
    latency_ms: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    tool_trace: list[ToolTraceEntry] = Field(default_factory=list)
    resolved_context: dict[str, Any] = Field(default_factory=dict)


class CatalogItem(BaseModel):
    id: str
    name: str


class CatalogResponse(BaseModel):
    items: list[CatalogItem]
