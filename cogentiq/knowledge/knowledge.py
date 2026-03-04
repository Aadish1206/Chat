from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .registry import ArtifactRegistry


class Knowledge:
    """Single-scope knowledge explorer backed by local artifact files."""

    _SUPPORTED_TYPES = [
        "glossary",
        "ontology",
        "data_bindings",
        "prompt_assets",
        "tool_bindings",
        "evaluation_assets",
        "knowledgebase",
    ]

    def __init__(self, root: str = "data", data_root: str | None = None) -> None:
        resolved_root = data_root or root
        self.registry = ArtifactRegistry(resolved_root)
        self.root = Path(resolved_root)
        self.compatibility = self._load_compatibility()

    def _load_compatibility(self) -> dict[str, Any]:
        path = self.root / "compatibility.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    def domains(self) -> list[str]:
        configured = sorted((self.compatibility.get("domains") or {}).keys())
        return configured or self.registry.list_keys("domain")

    def orgs(self, domain: str | None = None) -> list[str]:
        if not domain:
            return self.registry.list_keys("org")
        domain_conf = (self.compatibility.get("domains") or {}).get(domain, {})
        if domain_conf.get("orgs"):
            return sorted(domain_conf["orgs"])
        return self.registry.list_keys("org")

    def usecases(self, domain: str | None = None, org: str | None = None) -> list[str]:
        if not domain:
            return self.registry.list_keys("usecase")

        domain_conf = (self.compatibility.get("domains") or {}).get(domain, {})
        if org:
            by_org = domain_conf.get("usecases_by_org", {})
            if by_org.get(org):
                return sorted(by_org[org])
        domain_usecases = domain_conf.get("usecases", [])
        return sorted(domain_usecases) if domain_usecases else self.registry.list_keys("usecase")

    def supported_types(self) -> list[str]:
        return list(self._SUPPORTED_TYPES)

    def _validate_scope(self, domain: str | None, org: str | None, usecase: str | None) -> tuple[str, str, str]:
        selected = [("domain", domain), ("org", org), ("usecase", usecase)]
        provided = [(name, value) for name, value in selected if value]
        if len(provided) != 1:
            labels = ", ".join(name.upper() for name, _ in provided)
            if labels:
                raise ValueError(f"Exactly one of domain, org, or usecase must be provided, but got: {labels}")
            raise ValueError("Exactly one of domain, org, or usecase must be provided")

        scope, identifier = provided[0]
        layer = scope.upper()
        return scope, str(identifier), layer

    def _normalize_requested_sections(
        self,
        include: list[str] | None,
        exclude: list[str] | None,
        limits: dict[str, int] | None,
    ) -> list[str]:
        include = include or []
        exclude = exclude or []
        limits = limits or {}

        unsupported = [s for s in include + exclude + list(limits.keys()) if s not in self._SUPPORTED_TYPES]
        if unsupported:
            names = ", ".join(sorted(set(unsupported)))
            raise ValueError(f"Unsupported section(s): {names}")

        if include:
            sections = list(include)
        else:
            sections = list(self._SUPPORTED_TYPES)

        sections = [s for s in sections if s not in exclude]

        if limits:
            missing = [section for section in sections if section not in limits]
            if missing:
                raise ValueError(f"limits dict is missing entries for requested sections: {', '.join(missing)}")
            invalid_limits = [section for section, lim in limits.items() if not isinstance(lim, int) or lim <= 0]
            if invalid_limits:
                names = ", ".join(invalid_limits)
                raise ValueError(f"limits must be positive integers for sections: {names}")

        return sections

    def _extract_glossary(self, artifact: dict[str, Any]) -> list[dict[str, Any]]:
        content = artifact.get("content", {})
        terms = content.get("terms")
        if isinstance(terms, list):
            return terms

        if isinstance(terms, dict):
            return [{"term": k, **(v if isinstance(v, dict) else {"definition": v})} for k, v in terms.items()]

        if isinstance(content, dict):
            return [
                {"term": key, **(value if isinstance(value, dict) else {"definition": value})}
                for key, value in content.items()
                if key != "terms"
            ]
        return []

    def _extract_ontology(self, artifact: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        content = artifact.get("content", {}) if isinstance(artifact.get("content"), dict) else {}
        entities = content.get("entities") or []
        relationships = content.get("relationships") or []
        if not isinstance(entities, list):
            entities = []
        if not isinstance(relationships, list):
            relationships = []
        return {"entities": entities, "relationships": relationships}

    def _extract_named_list(self, artifact: dict[str, Any], key: str) -> list[dict[str, Any]]:
        content = artifact.get("content", {})
        values = content.get(key) if isinstance(content, dict) else None
        if isinstance(values, list):
            return values
        if isinstance(values, dict):
            return [{"name": k, **(v if isinstance(v, dict) else {"description": v})} for k, v in values.items()]
        return []

    def _extract_prompt_assets(self, artifact: dict[str, Any]) -> list[dict[str, Any]]:
        content = artifact.get("content", {})
        prompts = content.get("prompts") if isinstance(content, dict) else None
        if isinstance(prompts, list):
            return prompts
        if isinstance(content, dict) and content:
            return [content]
        return []

    def _extract_knowledgebase(self, artifact: dict[str, Any]) -> list[dict[str, Any]]:
        content = artifact.get("content", {})
        if not isinstance(content, dict):
            return []
        for key in ("entries", "documents", "items"):
            value = content.get(key)
            if isinstance(value, list):
                return value
        return []

    def _section_content(self, section: str, artifact: dict[str, Any]) -> Any:
        if section == "glossary":
            return self._extract_glossary(artifact)
        if section == "ontology":
            return self._extract_ontology(artifact)
        if section == "data_bindings":
            return self._extract_named_list(artifact, "tables")
        if section == "prompt_assets":
            return self._extract_prompt_assets(artifact)
        if section == "tool_bindings":
            return self._extract_named_list(artifact, "tools")
        if section == "evaluation_assets":
            return self._extract_named_list(artifact, "evaluations")
        if section == "knowledgebase":
            return self._extract_knowledgebase(artifact)
        return []

    def list(
        self,
        domain: str | None = None,
        org: str | None = None,
        usecase: str | None = None,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        limits: dict[str, int] | None = None,
        per_section_limits: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        # Backward compatibility: list(scope, key, ...)
        if domain in {"domain", "org", "usecase"} and org and not usecase:
            scope = domain
            identifier = org
            include = include or []
            exclude = exclude or []
            legacy_limits = per_section_limits or limits or {}
            envelope = self.registry.load_layer(scope, identifier)
            artifacts = envelope.get("artifacts", [])
            if include:
                artifacts = [a for a in artifacts if a.get("type") in include]
            if exclude:
                artifacts = [a for a in artifacts if a.get("type") not in exclude]
            for section, lim in legacy_limits.items():
                if lim <= 0:
                    raise ValueError("per_section_limits values must be > 0")
                capped = [a for a in artifacts if a.get("type") == section][:lim]
                artifacts = [a for a in artifacts if a.get("type") != section] + capped
            return {"artifacts": artifacts}

        scope, identifier, layer = self._validate_scope(domain, org, usecase)
        sections = self._normalize_requested_sections(include, exclude, limits)
        limits = limits or {}

        try:
            envelope = self.registry.load_layer(scope, identifier)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"No artifacts found for {scope}='{identifier}'. Directory may not exist or contains no JSON files."
            ) from exc

        artifacts = envelope.get("artifacts", [])
        if not artifacts:
            raise FileNotFoundError(
                f"No artifacts found for {scope}='{identifier}'. Directory may not exist or contains no JSON files."
            )

        results: dict[str, Any] = {
            "meta": {
                "layer": layer,
                "identifier": identifier,
                "version": "latest",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
        }

        for section in sections:
            matching = [a for a in artifacts if a.get("type") == section]
            if not matching:
                continue

            value = self._section_content(section, matching[0])
            if section == "ontology":
                limit = limits.get(section)
                if limit:
                    value = {**value, "entities": value.get("entities", [])[:limit]}
            else:
                limit = limits.get(section)
                if limit and isinstance(value, list):
                    value = value[:limit]

            results[section] = value

        return results
