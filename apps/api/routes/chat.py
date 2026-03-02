from __future__ import annotations

from fastapi import APIRouter, Depends

from core.registry.file_registry import FileRegistry
from core.runtime.llm_client import LLMClient
from core.runtime.orchestrator import ChatOrchestrator
from core.schemas.api_models import ChatRequest, ChatResponse
from core.tools.router import ToolRouter

router = APIRouter(tags=["chat"])


def get_orchestrator() -> ChatOrchestrator:
    return ChatOrchestrator(registry=FileRegistry(), llm_client=LLMClient(), router=ToolRouter())


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, orchestrator: ChatOrchestrator = Depends(get_orchestrator)) -> ChatResponse:
    return orchestrator.handle_chat(req)
