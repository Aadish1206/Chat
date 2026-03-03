from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactRegistry:
    def __init__(self, root: str = "data") -> None:
        self.root = Path(root)

    def _normalize(self, raw: dict[str, Any], source: str) -> dict[str, Any]:
        if "artifacts" not in raw or not isinstance(raw["artifacts"], list):
            raise ValueError(f"Invalid artifact envelope in {source}")
        return raw

    def load_layer(self, scope: str, key: str) -> dict[str, Any]:
        path = self.root / scope / key / "artifacts.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing artifacts file: {path}")
        raw = json.loads(path.read_text())
        return self._normalize(raw, str(path))

    def list_keys(self, scope: str) -> list[str]:
        base = self.root / scope
        if not base.exists():
            return []
        return sorted([p.name for p in base.iterdir() if p.is_dir()])
