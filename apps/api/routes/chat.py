from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from runtime.orchestrator import ChatbotRuntime

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    domain: str
    org: str
    usecase: str
    message: str
    top_n: int = 5


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    tool_traces: list[dict[str, Any]] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
    tools_used: list[str] = Field(default_factory=list)
    composed_prompt: str = ""


def get_runtime() -> ChatbotRuntime:
    return ChatbotRuntime("data")


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, runtime: ChatbotRuntime = Depends(get_runtime)) -> ChatResponse:
    result = await runtime.answer_async(req.domain, req.org, req.usecase, req.message, req.top_n)
    return ChatResponse(**result)
