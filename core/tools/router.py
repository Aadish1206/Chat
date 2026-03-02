from __future__ import annotations

import logging
import time
from typing import Any

from jsonschema import validate

from core.tools.stubs.nl2sql import run_nl2sql
from core.tools.stubs.reorder_planner import run_reorder_planner

logger = logging.getLogger(__name__)


class ToolRouter:
    def __init__(self) -> None:
        self._tool_map = {
            "NL2SQL_Tool": run_nl2sql,
            "ReorderPlanner": run_reorder_planner,
        }

    def execute(
        self,
        tool_name: str,
        payload: dict[str, Any],
        schema: dict[str, Any],
        constraints: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        logger.info("Validating input for tool=%s", tool_name)
        validate(instance=payload, schema=schema)
        start = time.time()
        logger.info("Executing tool=%s", tool_name)
        output = self._tool_map[tool_name](payload)

        max_rows = constraints.get("max_rows")
        if max_rows and isinstance(output.get("rows"), list):
            output["rows"] = output["rows"][:max_rows]
        latency_ms = int((time.time() - start) * 1000)
        trace = {
            "tool_name": tool_name,
            "input": payload,
            "output_summary": f"keys={list(output.keys())}",
            "latency_ms": latency_ms,
        }
        return output, trace
