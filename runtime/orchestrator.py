from __future__ import annotations

import logging
import os
from typing import Any

from domain_layer import DomainLayer
from runtime.openai_client import call_openai_for_tool_plan
from runtime.tools import ToolExecutor

logger = logging.getLogger(__name__)


class ChatbotRuntime:
    def __init__(self, data_root: str = "data") -> None:
        self.layer = DomainLayer(data_root)
        self.executor = ToolExecutor()

    async def answer_async(self, domain: str, org: str, usecase: str, user_query: str, top_n: int = 5) -> dict[str, Any]:
        logger.info("Resolving context via DomainLayer for %s/%s/%s", domain, org, usecase)
        response = await self.layer.query_orchestrate_async(
            query=user_query,
            domain=domain,
            org=org,
            usecase=usecase,
            exclude=["knowledgebase", "evaluation-assets"],
            top_n=top_n,
        )

        allowed_tools = response.get("tools", [])
        calls = call_openai_for_tool_plan(user_query, response.get("composed_prompt", ""), allowed_tools)

        tool_outputs: list[dict[str, Any]] = []
        traces: list[dict[str, Any]] = []
        allowed_names = {t.get("name") for t in allowed_tools}
        for call in calls:
            if call.get("name") not in allowed_names:
                continue
            tool_def = next((t for t in allowed_tools if t.get("name") == call.get("name")), None)
            if not tool_def:
                continue
            out, trace = self.executor.execute(tool_def, call.get("input", {}))
            tool_outputs.append({"tool": call.get("name"), **out})
            traces.append(trace)

        if not os.getenv("OPENAI_API_KEY"):
            if any(t.get("name", "").lower() in {"nl2sql", "nl2sql_tool"} for t in allowed_tools):
                main = "Used deterministic fallback planning. Generated NL2SQL-style analysis with mock execution output."
            else:
                main = "No LLM API key configured; returning deterministic fallback summary with composed prompt and candidate tools."
                tool_outputs.append({"tool": "planner", "text": response.get("composed_prompt", ""), "candidate_tools": list(allowed_names)})
        else:
            main = "Completed orchestration and tool execution."

        tools_used = [f"{t['tool_name']}: {t['output_preview']}" for t in traces]
        answer = main
        if tool_outputs:
            answer += "\n\nTool output summary:"
            for item in tool_outputs:
                answer += f"\n- {item.get('tool')}: {item.get('text', '')}"

        return {
            "answer": answer,
            "sources": response.get("citations", []),
            "tool_traces": traces,
            "trace": response.get("trace", {}),
            "tools_used": tools_used,
            "composed_prompt": response.get("composed_prompt", ""),
        }

    def answer(self, domain: str, org: str, usecase: str, user_query: str, top_n: int = 5) -> dict[str, Any]:
        import asyncio

        return asyncio.run(self.answer_async(domain, org, usecase, user_query, top_n))
