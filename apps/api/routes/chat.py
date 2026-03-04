from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from cogentiq.knowledge import Knowledge
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


def get_knowledge() -> Knowledge:
    return Knowledge("data")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    runtime: ChatbotRuntime = Depends(get_runtime),
    knowledge: Knowledge = Depends(get_knowledge),
) -> ChatResponse:
    if req.domain not in knowledge.domains():
        raise HTTPException(status_code=404, detail=f"Unknown domain '{req.domain}'")
    if req.org not in knowledge.orgs(domain=req.domain):
        raise HTTPException(status_code=404, detail=f"Unknown org '{req.org}' for domain '{req.domain}'")
    if req.usecase not in knowledge.usecases(domain=req.domain, org=req.org):
        raise HTTPException(
            status_code=404,
            detail=f"Unknown usecase '{req.usecase}' for domain '{req.domain}' and org '{req.org}'",
        )

    try:
        result = await runtime.answer_async(req.domain, req.org, req.usecase, req.message, req.top_n)
        return ChatResponse(**result)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
