from __future__ import annotations

from core.schemas.tool_plan_models import ToolCall, ToolPlan


class LLMClient:
    def plan_tools(self, prompt: str) -> ToolPlan:
        lower = prompt.lower()
        if "reorder" in lower or "stock" in lower:
            return ToolPlan(
                reasoning_plan="Fetch inventory metrics then compute reorder recommendations.",
                tool_calls=[
                    ToolCall(
                        tool_name="NL2SQL_Tool",
                        input={
                            "query": "sku reorder candidates",
                            "metrics": ["sales", "stock", "stockouts", "lead_time_days"],
                        },
                    ),
                    ToolCall(
                        tool_name="ReorderPlanner",
                        input={"target_service_level": 0.95},
                    ),
                ],
            )
        return ToolPlan(reasoning_plan="No tools required.", tool_calls=[])

    def generate_answer(self, prompt: str) -> str:
        return "### Reorder Recommendation\n\n" + prompt.split("## Tool Outputs\n", 1)[-1]
