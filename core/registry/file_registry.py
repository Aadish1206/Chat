from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FileRegistry:
    def __init__(self, artifacts_root: str = "artifacts") -> None:
        self.root = Path(artifacts_root)

    def _load_json(self, path: Path) -> dict[str, Any]:
        logger.info("Loading JSON artifact from %s", path)
        return json.loads(path.read_text())

    def _load_text(self, path: Path) -> str:
        logger.info("Loading text artifact from %s", path)
        return path.read_text()

    def load_tool_bindings(self, layer: str, key: str) -> dict[str, Any]:
        return self._load_json(self.root / layer / key / "tool_bindings.json")

    def load_domain_prompt(self, domain: str) -> str:
        return self._load_text(self.root / "domain" / domain / "prompts" / "base_system.md")

    def load_usecase_prompt(self, usecase: str) -> str:
        return self._load_text(self.root / "usecase" / usecase / "prompts" / "usecase_format.md")

    def load_schema(self, schema_ref: str) -> dict[str, Any]:
        return self._load_json(self.root / schema_ref)

    def list_domains(self) -> list[dict[str, str]]:
        base = self.root / "domain"
        return [{"id": p.name, "name": p.name} for p in base.iterdir() if p.is_dir()]

    def list_orgs(self, domain: str) -> list[dict[str, str]]:
        _ = domain
        base = self.root / "org"
        return [{"id": p.name, "name": p.name} for p in base.iterdir() if p.is_dir()]

    def list_usecases(self, domain: str, org: str) -> list[dict[str, str]]:
        _ = domain, org
        base = self.root / "usecase"
        return [{"id": p.name, "name": p.name} for p in base.iterdir() if p.is_dir()]
