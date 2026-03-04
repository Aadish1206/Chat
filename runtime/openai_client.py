from __future__ import annotations

import json
import os
from typing import Any


def pick_tool_calls(user_query: str, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    q = user_query.lower()
    chosen = []
    data_intent_tokens = {
        "sql",
        "data",
        "reorder",
        "plan",
        "sku",
        "claim",
        "denial",
        "authorization",
        "auth",
        "fraud",
        "transaction",
        "spike",
        "trend",
        "monitor",
        "analysis",
        "triage",
        "risk",
    }
    risk_intent_tokens = {
        "risk",
        "fraud",
        "spike",
        "anomaly",
        "denial",
        "delay",
        "watch",
        "alert",
    }

    for t in tools:
        name = t.get("name", "")
        lower = name.lower()
        if "nl2sql" in lower and any(token in q for token in data_intent_tokens):
            chosen.append({"name": name, "input": {**t.get("input", {}), "question": user_query}})
        if ("reorder_planner" in lower or lower == "reorderplanner") and not any(token in q for token in risk_intent_tokens):
            chosen.append({"name": name, "input": {**t.get("input", {}), "format": "markdown"}})
        if any(token in q for token in risk_intent_tokens) and "risk" in lower:
            chosen.append({"name": name, "input": {**t.get("input", {})}})
    return chosen


def call_openai_for_tool_plan(user_query: str, composed_prompt: str, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Kept deterministic and local-safe. If key exists, we still avoid hard dependency on openai package.
    if not os.getenv("OPENAI_API_KEY"):
        return pick_tool_calls(user_query, tools)
    # Minimal placeholder: in environments with openai SDK integrated by caller, swap this function.
    # For PoC reliability we use deterministic planner even when key exists.
    return pick_tool_calls(user_query, tools)


def synthesize_final_answer(base_answer: str, tool_outputs: list[dict[str, Any]]) -> str:
    snippets = []
    for out in tool_outputs:
        snippets.append(out.get("text", json.dumps(out)[:120]))
    return base_answer + "\n\n" + "\n".join([f"- {s}" for s in snippets])
