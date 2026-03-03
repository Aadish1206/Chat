from __future__ import annotations

import logging

from core.runtime.llm_client import LLMClient
from core.schemas.tool_plan_models import ToolPlan

logger = logging.getLogger(__name__)


class ToolPlanner:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def create_plan(self, message: str, effective_bindings: dict) -> ToolPlan:
        logger.info("Creating tool plan with allowed tools: %s", effective_bindings["allowed_tools"])
        prompt = (
            "You may only call tools from this list: "
            f"{effective_bindings['allowed_tools']}.\n"
            f"User request: {message}"
        )
        plan = self.llm_client.plan_tools(prompt)
        plan.tool_calls = [c for c in plan.tool_calls if c.tool_name in effective_bindings["allowed_tools"]]
        return plan
