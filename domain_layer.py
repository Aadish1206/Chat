from __future__ import annotations

import asyncio
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from typing import Any


class DomainLayer:
    TYPE_ALIASES = {
        "data-bindings": "data_bindings",
        "data bindings": "data_bindings",
        "prompt-assets": "prompt_assets",
        "prompt assets": "prompt_assets",
        "tool-bindings": "tool_bindings",
        "tool bindings": "tool_bindings",
    }

    DEFAULT_TYPES = ["glossary", "ontology", "data_bindings", "prompt_assets", "tool_bindings"]

    def __init__(self, root: str = "data") -> None:
        self.root = root
        self.domain_dir = os.path.join(self.root, "domain")
        self.org_dir = os.path.join(self.root, "org")
        self.usecase_dir = os.path.join(self.root, "usecase")

    @classmethod
    def _normalize_types(cls, types: list[str] | None) -> set[str] | None:
        if not types:
            return None
        normalized: set[str] = set()
        for item in types:
            if not item:
                continue
            key = item.strip().lower()
            key = cls.TYPE_ALIASES.get(key, key)
            normalized.add(key)
        return normalized

    @staticmethod
    def _load_registry(path: str) -> list[dict[str, Any]]:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("artifacts", [])

    @classmethod
    def _load_layer_dir(cls, layer_dir: str) -> list[dict[str, Any]]:
        if not os.path.isdir(layer_dir):
            return []
        artifacts: list[dict[str, Any]] = []
        for filename in sorted(os.listdir(layer_dir)):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(layer_dir, filename)
            artifacts.extend(cls._load_registry(filepath))
        return artifacts

    def _load_layer_artifacts(self, domain: str, org: str, usecase: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        domain_artifacts = self._load_layer_dir(os.path.join(self.domain_dir, domain))
        org_artifacts = self._load_layer_dir(os.path.join(self.org_dir, org))
        usecase_artifacts = self._load_layer_dir(os.path.join(self.usecase_dir, usecase))

        if not domain_artifacts and not org_artifacts and not usecase_artifacts:
            raise FileNotFoundError("No artifact registries found. Run setup_data.py to initialize the PoC.")

        return domain_artifacts, org_artifacts, usecase_artifacts

    @staticmethod
    def _collect_by_type(artifacts: list[dict[str, Any]], artifact_type: str) -> list[dict[str, Any]]:
        return [artifact for artifact in artifacts if artifact.get("type") == artifact_type]

    @staticmethod
    def _first_or_none(items: list[dict[str, Any]]) -> dict[str, Any] | None:
        return items[0] if items else None

    @classmethod
    def _pick_source(cls, *artifacts: dict[str, Any] | None) -> str | None:
        for artifact in artifacts:
            if artifact:
                return artifact.get("source")
        return None

    @staticmethod
    def _merge_lists(base: list[Any], overlay: list[Any]) -> list[Any]:
        seen = set()
        merged = []
        for value in base + overlay:
            key = json.dumps(value, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            merged.append(value)
        return merged

    @staticmethod
    def _deep_merge(base: Any, overlay: Any) -> Any:
        if isinstance(base, dict) and isinstance(overlay, dict):
            merged = dict(base)
            for key, value in overlay.items():
                if key in merged:
                    merged[key] = DomainLayer._deep_merge(merged[key], value)
                else:
                    merged[key] = value
            return merged
        return overlay

    @staticmethod
    def _merge_glossary(domain_items: list[dict[str, Any]], org_items: list[dict[str, Any]], usecase_items: list[dict[str, Any]]) -> dict[str, Any]:
        merged: dict[str, dict[str, Any]] = {}

        def apply(items: list[dict[str, Any]]) -> None:
            for item in items:
                content = item.get("content", {})
                for term in content.get("terms", []):
                    if isinstance(term, dict) and term.get("term"):
                        merged[term["term"]] = term

        apply(domain_items)
        apply(org_items)
        apply(usecase_items)

        return {"terms": list(merged.values())}

    @staticmethod
    def _merge_ontology(domain_items: list[dict[str, Any]], org_items: list[dict[str, Any]], usecase_items: list[dict[str, Any]]) -> dict[str, Any]:
        entities = []
        relationships = []

        for item in domain_items + org_items + usecase_items:
            content = item.get("content", {})
            entities = DomainLayer._merge_lists(entities, content.get("entities", []))
            relationships = DomainLayer._merge_lists(relationships, content.get("relationships", []))

        return {"entities": entities, "relationships": relationships}

    @staticmethod
    def _merge_data_bindings(domain_items: list[dict[str, Any]], org_items: list[dict[str, Any]], usecase_items: list[dict[str, Any]]) -> dict[str, Any]:
        tables = []
        columns = []
        filters: dict[str, Any] = {}

        for item in domain_items + org_items + usecase_items:
            content = item.get("content", {})
            tables = DomainLayer._merge_lists(tables, content.get("tables", []))
            columns = DomainLayer._merge_lists(columns, content.get("columns", []))
            filters.update(content.get("filters", {}))

        return {"tables": tables, "columns": columns, "filters": filters}

    @staticmethod
    def _merge_prompt_assets(domain_items: list[dict[str, Any]], org_items: list[dict[str, Any]], usecase_items: list[dict[str, Any]]) -> dict[str, Any]:
        reasoning_plan = []
        vector_contexts = []
        composed_prompt = ""

        for item in domain_items + org_items + usecase_items:
            content = item.get("content", {})
            reasoning_plan = DomainLayer._merge_lists(reasoning_plan, content.get("reasoning_plan", []))
            vector_contexts = DomainLayer._merge_lists(vector_contexts, content.get("vector_contexts", []))
            if content.get("composed_prompt"):
                composed_prompt = content["composed_prompt"]

        return {"reasoning_plan": reasoning_plan, "composed_prompt": composed_prompt, "vector_contexts": vector_contexts}

    @classmethod
    def _merge_tool_contents(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tools = []
        by_name: dict[str, dict[str, Any]] = {}
        for item in items:
            for tool in item.get("content", {}).get("tools", []):
                name = tool.get("name")
                if not name:
                    continue
                if name in by_name:
                    by_name[name] = cls._deep_merge(by_name[name], tool)
                else:
                    by_name[name] = tool
                    tools.append(name)
        return [by_name[name] for name in tools]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]

    @staticmethod
    def _score_text(text: str, tokens: set[str]) -> int:
        if not text:
            return 0
        haystack = text.lower()
        return sum(1 for token in tokens if token in haystack)

    @staticmethod
    def _flatten_artifact_text(artifact: dict[str, Any]) -> str:
        parts = [
            artifact.get("name", ""),
            artifact.get("snippet", ""),
            artifact.get("source", ""),
            json.dumps(artifact.get("content", {}), ensure_ascii=True),
        ]
        return " ".join(parts)

    @classmethod
    def _expand_query_terms(
        cls,
        query: str,
        glossary_terms: list[dict[str, Any]],
        ontology_entities: list[str],
        relationships: list[dict[str, Any]],
    ) -> set[str]:
        tokens = set(cls._tokenize(query))
        expanded = set(tokens)

        synonym_map = {}
        for term in glossary_terms:
            canonical = term.get("term", "")
            for synonym in term.get("synonyms", []):
                synonym_map[str(synonym).lower()] = canonical

        for synonym, canonical in synonym_map.items():
            if synonym in query.lower():
                expanded.update(cls._tokenize(canonical))

        for entity in ontology_entities:
            entity_tokens = cls._tokenize(str(entity))
            if any(token in tokens for token in entity_tokens):
                expanded.update(entity_tokens)

        related = set()
        for relation in relationships:
            from_entity = relation.get("from", "")
            to_entity = relation.get("to", "")
            from_tokens = cls._tokenize(str(from_entity))
            to_tokens = cls._tokenize(str(to_entity))
            if from_tokens and any(token in expanded for token in from_tokens):
                related.update(to_tokens)
            if to_tokens and any(token in expanded for token in to_tokens):
                related.update(from_tokens)

        expanded.update(related)
        return expanded

    @classmethod
    def _search_artifacts(cls, artifacts: list[dict[str, Any]], tokens: set[str], top_n: int = 5) -> list[dict[str, Any]]:
        scored = []
        for artifact in artifacts:
            text = cls._flatten_artifact_text(artifact)
            score = cls._score_text(text, tokens)
            if score <= 0:
                continue
            scored.append((score, artifact))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, artifact in scored[:top_n]:
            results.append(
                {
                    "type": artifact.get("type"),
                    "name": artifact.get("name"),
                    "match_score": round(min(1.0, score / 10.0), 3),
                    "snippet": artifact.get("snippet", ""),
                    "source": artifact.get("source", ""),
                    "content": artifact.get("content", {}),
                }
            )
        return results

    @staticmethod
    def _build_llm_prompt(query: str, domain: str, org: str, usecase: str, results: dict[str, Any]) -> str:
        schema_example = {
            "input": {"query": "", "domain": "", "org": "", "usecase": ""},
            "reasoning_plan": ["Step 1: ...", "Step 2: ..."],
            "composed_prompt": "",
            "tools": [],
            "citations": {
                "glossary": "",
                "ontology": "",
                "data_bindings": "",
                "prompt_assets": "",
                "tool_bindings": "",
                "vector_contexts": [],
            },
            "trace": {"domain": "", "org": "", "usecase": "", "generated_at": ""},
        }
        return (
            "You are a domain orchestrator. Use the artifacts below to produce a JSON payload that matches this exact schema shape. "
            "Respond with JSON only.\n\n"
            f"Schema example:\n{json.dumps(schema_example, indent=2)}\n\n"
            f"Query: {query}\nDomain: {domain}\nOrg: {org}\nUsecase: {usecase}\n\n"
            f"Artifacts (top matches by type):\n{json.dumps(results, indent=2)}"
        )

    @staticmethod
    def _is_valid_response(payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        required_keys = {"input", "reasoning_plan", "composed_prompt", "tools", "citations", "trace"}
        if not required_keys.issubset(payload.keys()):
            return False
        if not isinstance(payload.get("input"), dict):
            return False
        input_payload = payload.get("input", {})
        for key in ("query", "domain", "org", "usecase"):
            if key not in input_payload:
                return False
        if not isinstance(payload.get("reasoning_plan"), list):
            return False
        if not all(isinstance(item, str) for item in payload.get("reasoning_plan", [])):
            return False
        if not isinstance(payload.get("composed_prompt"), str):
            return False
        if not isinstance(payload.get("tools"), list):
            return False
        for tool in payload.get("tools", []):
            if not isinstance(tool, dict) or "name" not in tool:
                return False
        if not isinstance(payload.get("citations"), dict):
            return False
        citations = payload.get("citations", {})
        for key in ("glossary", "ontology", "data_bindings", "prompt_assets", "tool_bindings"):
            if key not in citations:
                return False
        if "vector_contexts" in citations and not isinstance(citations["vector_contexts"], list):
            return False
        if not isinstance(payload.get("trace"), dict):
            return False
        trace = payload.get("trace", {})
        for key in ("domain", "org", "usecase", "generated_at"):
            if key not in trace:
                return False
        return True

    @staticmethod
    def _call_openai(api_key: str, prompt: str) -> dict[str, Any] | None:
        url = "https://api.openai.com/v1/responses"
        payload = {"model": "gpt-4.1-mini", "input": prompt, "temperature": 0.2}
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        request.add_header("Authorization", f"Bearer {api_key}")
        request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
        payload = json.loads(body)
        text_parts = []
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text_parts.append(content.get("text", ""))
        if not text_parts:
            return None
        raw_text = "".join(text_parts).strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.replace("json", "", 1).strip()
        if "{" in raw_text and "}" in raw_text:
            raw_text = raw_text[raw_text.find("{") : raw_text.rfind("}") + 1]
        return json.loads(raw_text)

    async def query_orchestrate_async(
        self,
        query: str,
        domain: str,
        org: str,
        usecase: str,
        exclude: list[str] | None = None,
        include: list[str] | None = None,
        top_n: int = 5,
    ) -> dict[str, Any]:
        include_set = self._normalize_types(include)
        exclude_set = self._normalize_types(exclude) or set()

        requested_types = list(self.DEFAULT_TYPES) if include_set is None else [t for t in self.DEFAULT_TYPES if t in include_set]
        requested_types = [t for t in requested_types if t not in exclude_set]

        domain_artifacts, org_artifacts, usecase_artifacts = await asyncio.to_thread(self._load_layer_artifacts, domain, org, usecase)

        all_artifacts = domain_artifacts + org_artifacts + usecase_artifacts
        merged_glossary = self._merge_glossary(
            self._collect_by_type(domain_artifacts, "glossary"),
            self._collect_by_type(org_artifacts, "glossary"),
            self._collect_by_type(usecase_artifacts, "glossary"),
        )
        merged_ontology = self._merge_ontology(
            self._collect_by_type(domain_artifacts, "ontology"),
            self._collect_by_type(org_artifacts, "ontology"),
            self._collect_by_type(usecase_artifacts, "ontology"),
        )

        expanded_tokens = self._expand_query_terms(
            query,
            merged_glossary.get("terms", []),
            merged_ontology.get("entities", []),
            merged_ontology.get("relationships", []),
        )

        tasks = {}
        for artifact_type in requested_types:
            items = self._collect_by_type(all_artifacts, artifact_type)
            tasks[artifact_type] = asyncio.to_thread(self._search_artifacts, items, expanded_tokens, top_n)

        results = {}
        if tasks:
            finished = await asyncio.gather(*tasks.values())
            results = dict(zip(tasks.keys(), finished))

        prompt_assets = results.get("prompt_assets", [])
        data_bindings = results.get("data_bindings", [])
        all_tool_bindings = self._collect_by_type(all_artifacts, "tool_bindings")
        tools = self._merge_tool_contents(all_tool_bindings)

        if data_bindings:
            merged_bindings = self._merge_data_bindings(
                self._collect_by_type(domain_artifacts, "data_bindings"),
                self._collect_by_type(org_artifacts, "data_bindings"),
                self._collect_by_type(usecase_artifacts, "data_bindings"),
            )
            for tool in tools:
                if tool.get("name") != "NL2SQL_Tool":
                    continue
                tool.setdefault("input", {})
                tool_input = tool.get("input", {})
                data_context = tool_input.get("data_context", {})
                data_context.setdefault("tables", merged_bindings.get("tables", []))
                data_context.setdefault("columns", merged_bindings.get("columns", []))
                data_context.setdefault("filters", merged_bindings.get("filters", {}))
                tool_input["data_context"] = data_context
                tool["input"] = tool_input

        reasoning_plan: list[str] = []
        composed_prompt = ""
        vector_contexts: list[str] = []
        if prompt_assets:
            content = prompt_assets[0].get("content", {})
            reasoning_plan = content.get("reasoning_plan", [])
            composed_prompt = content.get("composed_prompt", "")
            vector_contexts = content.get("vector_contexts", [])
            if not reasoning_plan and content.get("prompt_content"):
                prompt_content = content["prompt_content"]
                for segment in prompt_content.split("Step "):
                    segment = segment.strip()
                    if segment and segment[0].isdigit():
                        reasoning_plan.append(f"Step {segment}")

        citations: dict[str, Any] = {}
        for artifact_type, items in results.items():
            if not items:
                continue
            sources = [item.get("source") for item in items if item.get("source")]
            if sources:
                citations[artifact_type] = ", ".join(dict.fromkeys(sources))
        citations["vector_contexts"] = vector_contexts

        response = {
            "input": {"query": query, "domain": domain, "org": org, "usecase": usecase},
            "reasoning_plan": reasoning_plan,
            "composed_prompt": composed_prompt,
            "tools": tools,
            "citations": citations,
            "trace": {
                "domain": domain,
                "org": org,
                "usecase": usecase,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
        }

        try:
            from dotenv import load_dotenv

            load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
        except Exception:
            pass

        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            prompt = self._build_llm_prompt(query, domain, org, usecase, results)
            try:
                llm_response = await asyncio.to_thread(self._call_openai, api_key, prompt)
                if self._is_valid_response(llm_response):
                    return llm_response
            except Exception:
                return response

        return response

    def query_orchestrate(
        self,
        query: str,
        domain: str,
        org: str,
        usecase: str,
        exclude: list[str] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        return asyncio.run(
            self.query_orchestrate_async(
                query=query,
                domain=domain,
                org=org,
                usecase=usecase,
                exclude=exclude,
                include=include,
            )
        )

    def _collect_artifacts(
        self,
        domain: str,
        org: str | None,
        usecase: str | None,
        include: list[str],
        exclude: list[str],
    ) -> list[dict[str, Any]]:
        include_set = self._normalize_types(include)
        exclude_set = self._normalize_types(exclude) or set()
        if include_set is None:
            requested_types = list(self.DEFAULT_TYPES)
        else:
            requested_types = [t for t in self.DEFAULT_TYPES if t in include_set]
        requested_types = [t for t in requested_types if t not in exclude_set]

        entries: list[dict[str, Any]] = []
        for scope, key in [("domain", domain), ("org", org), ("usecase", usecase)]:
            if not key:
                continue
            scope_dir = {"domain": self.domain_dir, "org": self.org_dir, "usecase": self.usecase_dir}[scope]
            artifacts = self._load_layer_dir(os.path.join(scope_dir, key))
            for artifact in artifacts:
                if artifact.get("type") in requested_types:
                    entries.append({"scope": scope, **artifact})
        return entries

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
        artifacts = self._collect_artifacts(domain, org, usecase, include or [], exclude or [])
        tokens = set(self._tokenize(query))
        scored = []
        for artifact in artifacts:
            score = self._score_text(self._flatten_artifact_text(artifact), tokens)
            scored.append(
                {
                    "type": artifact.get("type", "unknown"),
                    "name": artifact.get("name", "unnamed"),
                    "match_score": round(min(1.0, score / 10.0), 3),
                    "snippet": artifact.get("snippet", ""),
                    "source": artifact.get("source", ""),
                    "scope": artifact.get("scope", ""),
                }
            )
        results = sorted(scored, key=lambda x: x["match_score"], reverse=True)[:top_n]

        payload: dict[str, Any] = {
            "input": {"query": query, "domain": domain, "org": org, "usecase": usecase, "top_n": top_n, "for_each": for_each},
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
        artifacts = self._collect_artifacts(domain, org, usecase, include or [], exclude or [])
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
            "input": {"domain": domain, "org": org, "usecase": usecase, "limit": limit, "for_each": for_each},
            "results": results,
            "retrieved_from": ["Domain Artifact Registry"],
        }
        if for_each:
            grouped: dict[str, list[dict[str, Any]]] = {"domain": [], "org": [], "usecase": []}
            for item in results:
                grouped[item.get("scope", "")] = grouped.get(item.get("scope", ""), []) + [item]
            payload["results_by_scope"] = grouped
        return payload
