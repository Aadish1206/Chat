from __future__ import annotations

import csv
import time
from datetime import datetime
from typing import Any

from runtime.schemas import validate_input
from runtime.utils import ensure_results_dir


class ToolExecutor:
    def __init__(self) -> None:
        self.handlers = {
            "nl2sql": self._nl2sql,
            "nl2sql_tool": self._nl2sql,
            "reorderplanner": self._reorder_planner,
            "reorder_planner": self._reorder_planner,
            "reorder_risk_simulator": self._risk_sim,
        }

    def execute(self, tool: dict[str, Any], payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        name = tool.get("name", "").lower()
        start = time.time()
        schema = tool.get("input_schema", {"type": "object"})
        ok, err = validate_input(payload, schema)
        if not ok:
            out = {"text": f"Input validation failed: {err}"}
        else:
            handler = self.handlers.get(name)
            out = handler(payload) if handler else {"text": f"No local executor for tool '{tool.get('name')}'"}
        trace = {
            "tool_name": tool.get("name"),
            "latency_ms": int((time.time() - start) * 1000),
            "output_preview": out.get("text", str(out))[:160],
        }
        return out, trace

    def _nl2sql(self, payload: dict[str, Any]) -> dict[str, Any]:
        question = payload.get("question", "")
        context = payload.get("data_context", {})
        tables = context.get("tables", [{"name": "sales_orders", "columns": ["sku", "qty", "region", "month"]}])
        filters = context.get("filters", {})
        table = tables[0]["name"] if tables else "sales_orders"
        cols = ", ".join(tables[0].get("columns", ["sku", "qty"]))
        where = " AND ".join([f"{k}='{v}'" for k, v in filters.items()]) or "1=1"
        sql = f"SELECT {cols} FROM {table} WHERE {where} LIMIT 100;"

        out_dir = ensure_results_dir()
        file_path = out_dir / f"nl2sql_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        with file_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["sku", "recommended_qty", "region", "month"])
            writer.writerow(["SKU-101", 120, filters.get("region", "EU"), filters.get("month", "January")])
            writer.writerow(["SKU-205", 90, filters.get("region", "EU"), filters.get("month", "January")])

        return {
            "text": f"Would run SQL for: '{question}'. Generated pseudo SQL: {sql}",
            "sql": sql,
            "csv_file_path": str(file_path),
        }

    def _reorder_planner(self, payload: dict[str, Any]) -> dict[str, Any]:
        markdown = "| SKU | Suggested Reorder | Rationale |\n|---|---:|---|\n| SKU-101 | 120 | Demand trend + safety stock |\n| SKU-205 | 90 | Lead-time buffer |"
        return {"text": "Generated reorder plan.", "markdown": markdown}

    def _risk_sim(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"text": "Risk simulation complete.", "scores": [{"sku": "SKU-101", "risk": 0.32}, {"sku": "SKU-205", "risk": 0.27}]}
