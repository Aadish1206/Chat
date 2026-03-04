from __future__ import annotations

import asyncio
import json
import os
import re
from copy import deepcopy
from typing import Any

from cogentiq.knowledge import Knowledge


class DomainLayer:
    def __init__(self, root: str = "data") -> None:
        self.knowledge = Knowledge(root)

    def _extract_by_type(self, envelope: dict[str, Any], artifact_type: str) -> list[dict[str, Any]]:
        return [a for a in envelope.get("artifacts", []) if a.get("type") == artifact_type]

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(base)
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k] = self._deep_merge(merged[k], v)
            else:
                merged[k] = deepcopy(v)
        return merged

    def _merge_layered(self, domain_env: dict[str, Any], org_env: dict[str, Any], usecase_env: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {
            "glossary": {},
            "ontology": [],
            "data_bindings": {},
            "tool_bindings": [],
            "prompt_assets": {"composed_prompt": "", "reasoning_plan": [], "vector_contexts": []},
        }

        # glossary overwrite by precedence
        for env in [domain_env, org_env, usecase_env]:
            for a in self._extract_by_type(env, "glossary"):
                merged["glossary"].update(a.get("content", {}))

        # ontology union dedup
        seen = set()
        for env in [domain_env, org_env, usecase_env]:
            for a in self._extract_by_type(env, "ontology"):
                for rel in a.get("content", {}).get("relationships", []):
                    key = str(rel)
                    if key not in seen:
                        seen.add(key)
                        merged["ontology"].append(rel)

        # data bindings overlay, filters override by precedence
        db = {}
        for env in [domain_env, org_env, usecase_env]:
            for a in self._extract_by_type(env, "data_bindings"):
                db = self._deep_merge(db, a.get("content", {}))
        merged["data_bindings"] = db

        # prompt assets
        for env in [domain_env, org_env, usecase_env]:
            for a in self._extract_by_type(env, "prompt_assets"):
                c = a.get("content", {})
                if c.get("composed_prompt"):
                    merged["prompt_assets"]["composed_prompt"] = c["composed_prompt"]
                merged["prompt_assets"]["reasoning_plan"].extend(c.get("reasoning_plan", []))
                merged["prompt_assets"]["vector_contexts"].extend(c.get("vector_contexts", []))
        merged["prompt_assets"]["reasoning_plan"] = list(dict.fromkeys(merged["prompt_assets"]["reasoning_plan"]))
        merged["prompt_assets"]["vector_contexts"] = list(dict.fromkeys(merged["prompt_assets"]["vector_contexts"]))

        # tools by name deep merge precedence
        tools: dict[str, dict[str, Any]] = {}
        for env in [domain_env, org_env, usecase_env]:
            for a in self._extract_by_type(env, "tool_bindings"):
                for tool in a.get("content", {}).get("tools", []):
                    name = tool.get("name")
                    if not name:
                        continue
                    tools[name] = self._deep_merge(tools.get(name, {}), tool)
        merged["tool_bindings"] = list(tools.values())
        return merged

    def _search(self, user_query: str, merged: dict[str, Any], top_n: int) -> list[dict[str, Any]]:
        q = user_query.lower()
        hits = []
        for term, definition in merged.get("glossary", {}).items():
            score = 1 if term.lower() in q else 0
            if score:
                hits.append({"term": term, "definition": definition, "score": score})
        return sorted(hits, key=lambda x: x["score"], reverse=True)[:top_n]

    def _artifact_score(self, query: str, artifact: dict[str, Any]) -> float:
        q_tokens = set(query.lower().split())
        text = " ".join(
            [
                str(artifact.get("name", "")),
                str(artifact.get("snippet", "")),
                json.dumps(artifact.get("content", {}), sort_keys=True),
            ]
        ).lower()
        if not q_tokens:
            return 0.0
        matched = sum(1 for token in q_tokens if token in text)
        return round(matched / len(q_tokens), 2)

    def _extract_requested_filters(self, query: str) -> dict[str, str]:
        q = query.lower()
        requested: dict[str, str] = {}

        months = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
        for month in months:
            if month in q:
                if "service month" in q:
                    requested["service_month"] = month.capitalize()
                else:
                    requested["month"] = month.capitalize()
                break

        # Simple region extraction from common labels.
        region_match = re.search(r"\b(eu|us|apac|emea|na|east|west|north|south)\b", q)
        if region_match:
            requested["region"] = region_match.group(1).upper()

        return requested

    def _detect_intent_mode(self, query: str) -> str:
        q = query.lower()
        risk_only_signals = [
            "only risk",
            "risk analysis only",
            "no reorder",
            "skip reorder",
            "without reorder",
        ]
        if any(signal in q for signal in risk_only_signals):
            return "risk_only"
        if any(token in q for token in ["reorder", "plan", "recommendation"]):
            return "reorder"
        return "general"

    def _collect_artifacts(
        self,
        domain: str,
        org: str | None,
        usecase: str | None,
        include: list[str],
        exclude: list[str],
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for scope, key in [("domain", domain), ("org", org), ("usecase", usecase)]:
            if not key:
                continue
            envelope = self.knowledge.list(scope, key, include=include, exclude=exclude)
            for artifact in envelope.get("artifacts", []):
                entries.append({"scope": scope, **artifact})
        return entries

    async def query_orchestrate_async(
        self,
        query: str,
        domain: str,
        org: str,
        usecase: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        top_n: int = 5,
    ) -> dict[str, Any]:
        include = include or []
        exclude = exclude or []
        d = self.knowledge.list("domain", domain, include=include, exclude=exclude)
        o = self.knowledge.list("org", org, include=include, exclude=exclude)
        u = self.knowledge.list("usecase", usecase, include=include, exclude=exclude)

        merged = self._merge_layered(d, o, u)
        citations = [f"domain/{domain}/artifacts.json", f"org/{org}/artifacts.json", f"usecase/{usecase}/artifacts.json"]
        search_hits = self._search(query, merged, top_n)
        requested_filters = self._extract_requested_filters(query)
        intent_mode = self._detect_intent_mode(query)

        composed_prompt = merged["prompt_assets"]["composed_prompt"] or "Answer as supply-chain analyst."
        if intent_mode == "risk_only":
            composed_prompt += (
                "\n\nIntent override: The user asked for risk-only analysis. "
                "Do not provide reorder quantity recommendations in the final response."
            )
        elif intent_mode == "reorder":
            composed_prompt += (
                "\n\nIntent override: Provide reorder recommendations with concise rationale."
            )
        composed_prompt += f"\n\nUser Query: {query}\n"
        if search_hits:
            composed_prompt += "\nGlossary hits:\n" + "\n".join([f"- {h['term']}: {h['definition']}" for h in search_hits])

        # inject data context into NL2SQL-like tools
        tables = merged.get("data_bindings", {}).get("tables", [])
        default_filters = merged.get("data_bindings", {}).get("filters", {})
        effective_filters = dict(default_filters)
        precedence_changes = []

        # Managed precedence: user-specified filters override org/usecase defaults.
        # Hard policy constraints can be added later as a separate enforcement step.
        for key, requested in requested_filters.items():
            previous = effective_filters.get(key)
            effective_filters[key] = requested
            if previous is not None and str(previous).lower() != str(requested).lower():
                precedence_changes.append(
                    {
                        "field": key,
                        "default": previous,
                        "effective": requested,
                        "reason": "user request overrides default",
                    }
                )

        conflicts_applied = []
        for key, requested in requested_filters.items():
            effective = effective_filters.get(key)
            if effective is not None and str(requested).lower() != str(effective).lower():
                conflicts_applied.append(
                    {
                        "field": key,
                        "requested": requested,
                        "effective": effective,
                        "reason": "hard policy override",
                    }
                )
        tools = []
        for t in merged.get("tool_bindings", []):
            t2 = deepcopy(t)
            if t2.get("name", "").lower() in {"nl2sql", "nl2sql_tool"}:
                t2.setdefault("input", {})["data_context"] = {"tables": tables, "filters": effective_filters}
            tools.append(t2)

        return {
            "input": {"query": query, "domain": domain, "org": org, "usecase": usecase},
            "reasoning_plan": merged["prompt_assets"]["reasoning_plan"],
            "composed_prompt": composed_prompt,
            "tools": tools,
            "citations": {
                "artifact_refs": citations,
                "vector_contexts": merged["prompt_assets"]["vector_contexts"],
            },
            "trace": {
                "top_n": top_n,
                "openai_enabled": bool(os.getenv("OPENAI_API_KEY")),
                "search_hits": len(search_hits),
                "domain": domain,
                "org": org,
                "usecase": usecase,
                "requested_filters": requested_filters,
                "default_filters": default_filters,
                "effective_filters": effective_filters,
                "precedence_changes": precedence_changes,
                "conflicts_applied": conflicts_applied,
                "intent_mode": intent_mode,
            },
        }

    def search(
        self,
        query: str,
        domain: str,
        org: str,
        usecase: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        top_n: int = 5,
        for_each: bool = False,
    ) -> dict[str, Any]:
        include = include or []
        exclude = exclude or []
        artifacts = self._collect_artifacts(domain, org, usecase, include, exclude)

        results = []
        for artifact in artifacts:
            results.append(
                {
                    "type": artifact.get("type", "unknown"),
                    "name": artifact.get("name", "unnamed"),
                    "match_score": self._artifact_score(query, artifact),
                    "snippet": artifact.get("snippet", ""),
                    "source": artifact.get("source", ""),
                    "scope": artifact.get("scope", ""),
                }
            )
        results = sorted(results, key=lambda x: x["match_score"], reverse=True)[:top_n]

        payload: dict[str, Any] = {
            "input": {
                "query": query,
                "domain": domain,
                "org": org,
                "usecase": usecase,
                "top_n": top_n,
                "for_each": for_each,
            },
            "results": results,
            "retrieved_from": ["Domain Artifact Registry"],
        }
        if for_each:
            grouped: dict[str, list[dict[str, Any]]] = {"domain": [], "org": [], "usecase": []}
            for item in results:
                grouped[item.get("scope", "")] = grouped.get(item.get("scope", ""), []) + [item]
            payload["results_by_scope"] = grouped
        return payload

    def list(
        self,
        domain: str,
        org: str | None = None,
        usecase: str | None = None,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        limit: int = 10,
        for_each: bool = False,
    ) -> dict[str, Any]:
        include = include or []
        exclude = exclude or []
        artifacts = self._collect_artifacts(domain, org, usecase, include, exclude)

        results = [
            {
                "type": a.get("type", "unknown"),
                "name": a.get("name", "unnamed"),
                "snippet": a.get("snippet", ""),
                "source": a.get("source", ""),
                "scope": a.get("scope", ""),
            }
            for a in artifacts[:limit]
        ]
        payload: dict[str, Any] = {
            "input": {
                "domain": domain,
                "org": org,
                "usecase": usecase,
                "limit": limit,
                "for_each": for_each,
            },
            "results": results,
            "retrieved_from": ["Domain Artifact Registry"],
        }
        if for_each:
            grouped: dict[str, list[dict[str, Any]]] = {"domain": [], "org": [], "usecase": []}
            for item in results:
                grouped[item.get("scope", "")] = grouped.get(item.get("scope", ""), []) + [item]
            payload["results_by_scope"] = grouped
        return payload

    def query_orchestrate(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return asyncio.run(self.query_orchestrate_async(*args, **kwargs))
