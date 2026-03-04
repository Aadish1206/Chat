from __future__ import annotations

import json
import os
from urllib import error, request


def pick_tool_calls(user_query: str, tools: list[dict[str, object]]) -> list[dict[str, object]]:
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
        name = str(t.get("name", ""))
        lower = name.lower()
        if "nl2sql" in lower and any(token in q for token in data_intent_tokens):
            chosen.append({"name": name, "input": {**dict(t.get("input", {})), "question": user_query}})
        if ("reorder_planner" in lower or lower == "reorderplanner") and not any(token in q for token in risk_intent_tokens):
            chosen.append({"name": name, "input": {**dict(t.get("input", {})), "format": "markdown"}})
        if any(token in q for token in risk_intent_tokens) and "risk" in lower:
            chosen.append({"name": name, "input": {**dict(t.get("input", {}))}})
    return chosen


def _call_openai_tool_plan(user_query: str, composed_prompt: str, tools: list[dict[str, object]]) -> list[dict[str, object]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []

    prompt = (
        "You are a strict JSON planner. Return JSON object with key 'calls' as list of tool invocations. "
        "Each invocation has keys: name (string), input (object). Only use allowed tools.\n"
        f"Allowed tools: {[t.get('name') for t in tools]}\n"
        f"Composed prompt: {composed_prompt}\n"
        f"User query: {user_query}"
    )
    body = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "input": prompt,
        "temperature": 0,
    }

    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    text = payload.get("output_text", "").strip()
    if not text:
        return []
    parsed = json.loads(text)
    calls = parsed.get("calls", [])
    return calls if isinstance(calls, list) else []


def call_openai_for_tool_plan(user_query: str, composed_prompt: str, tools: list[dict[str, object]]) -> list[dict[str, object]]:
    if not os.getenv("OPENAI_API_KEY"):
        return pick_tool_calls(user_query, tools)

    try:
        calls = _call_openai_tool_plan(user_query, composed_prompt, tools)
        allowed = {str(t.get("name")) for t in tools}
        filtered = [c for c in calls if isinstance(c, dict) and c.get("name") in allowed]
        return filtered or pick_tool_calls(user_query, tools)
    except (error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return pick_tool_calls(user_query, tools)


def synthesize_final_answer(base_answer: str, tool_outputs: list[dict[str, object]]) -> str:
    snippets = []
    for out in tool_outputs:
        snippets.append(str(out.get("text", json.dumps(out)[:120])))
    return base_answer + "\n\n" + "\n".join([f"- {s}" for s in snippets])
