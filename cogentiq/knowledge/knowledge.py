from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import ArtifactRegistry


class Knowledge:
    """Single-scope inspection with optional compatibility filtering."""

    def __init__(self, root: str = "data") -> None:
        self.registry = ArtifactRegistry(root)
        self.root = Path(root)
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

    def list(
        self,
        scope: str,
        key: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        per_section_limits: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        if scope not in {"domain", "org", "usecase"}:
            raise ValueError("scope must be one of: domain, org, usecase")
        include = include or []
        exclude = exclude or []
        per_section_limits = per_section_limits or {}
        for v in per_section_limits.values():
            if v <= 0:
                raise ValueError("per_section_limits values must be > 0")

        envelope = self.registry.load_layer(scope, key)
        artifacts = envelope["artifacts"]
        if include:
            artifacts = [a for a in artifacts if a.get("type") in include]
        if exclude:
            artifacts = [a for a in artifacts if a.get("type") not in exclude]

        for t, lim in per_section_limits.items():
            kept = [a for a in artifacts if a.get("type") == t][:lim]
            artifacts = [a for a in artifacts if a.get("type") != t] + kept

        return {"artifacts": artifacts}
