from __future__ import annotations

import logging

from core.registry.file_registry import FileRegistry
from core.runtime.llm_client import LLMClient
from core.runtime.merge import merge_effective_tool_bindings
from core.runtime.planner import ToolPlanner
from core.runtime.prompt_composer import compose_final_prompt
from core.schemas.api_models import ChatRequest, ChatResponse, ToolTraceEntry
from core.tools.router import ToolRouter

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    def __init__(self, registry: FileRegistry, llm_client: LLMClient, router: ToolRouter) -> None:
        self.registry = registry
        self.planner = ToolPlanner(llm_client)
        self.llm_client = llm_client
        self.router = router

    def handle_chat(self, req: ChatRequest) -> ChatResponse:
        logger.info("Fetching binding artifacts for domain=%s org=%s usecase=%s", req.domain, req.org, req.usecase)
        domain_bindings = self.registry.load_tool_bindings("domain", req.domain)
        org_bindings = self.registry.load_tool_bindings("org", req.org)
        usecase_bindings = self.registry.load_tool_bindings("usecase", req.usecase)

        effective = merge_effective_tool_bindings(domain_bindings, org_bindings, usecase_bindings)
        logger.info("Merged effective bindings for tools=%s", effective["allowed_tools"])

        plan = self.planner.create_plan(req.message, effective)
        logger.info("Planner returned %d tool calls", len(plan.tool_calls))

        tool_outputs = []
        tool_trace: list[ToolTraceEntry] = []
        citations = [
            f"artifact:domain/{req.domain}/tool_bindings.json",
            f"artifact:org/{req.org}/tool_bindings.json",
            f"artifact:usecase/{req.usecase}/tool_bindings.json",
        ]

        context_payload: dict = {}
        for call in plan.tool_calls:
            conf = effective["bindings"][call.tool_name]
            payload = {**conf.get("defaults", {}), **call.input, **context_payload}
            schema = self.registry.load_schema(conf["schema_ref"])
            output, trace = self.router.execute(call.tool_name, payload, schema, conf.get("constraints", {}))
            tool_outputs.append(output)
            tool_trace.append(ToolTraceEntry(**trace))
            context_payload = output
            citations.append(f"tool:{call.tool_name}:{output.get('source', 'unknown')}")

        base_prompt = self.registry.load_domain_prompt(req.domain)
        usecase_prompt = self.registry.load_usecase_prompt(req.usecase)
        final_prompt = compose_final_prompt(base_prompt, usecase_prompt, tool_outputs, citations, req.message)
        answer = self.llm_client.generate_answer(final_prompt)

        return ChatResponse(
            answer=answer,
            citations=citations,
            tool_trace=tool_trace,
            resolved_context={
                "session_id": req.session_id,
                "effective_binding_refs": effective["binding_refs"],
                "allowed_tools": effective["allowed_tools"],
            },
        )
