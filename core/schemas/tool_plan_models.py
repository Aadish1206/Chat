from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)


class ToolPlan(BaseModel):
    reasoning_plan: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
