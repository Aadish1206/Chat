from __future__ import annotations

from typing import Any

from .registry import ArtifactRegistry


class Knowledge:
    """Single-scope inspection only. No cross-layer merge in list()."""

    def __init__(self, root: str = "data") -> None:
        self.registry = ArtifactRegistry(root)

    def domains(self) -> list[str]:
        return self.registry.list_keys("domain")

    def orgs(self) -> list[str]:
        return self.registry.list_keys("org")

    def usecases(self) -> list[str]:
        return self.registry.list_keys("usecase")

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
