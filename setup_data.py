from __future__ import annotations

import json
from pathlib import Path


def write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2))


def main() -> None:
    write(
        "data/domain/CPG/artifacts.json",
        {
            "artifacts": [
                {"type": "glossary", "name": "cpg_glossary", "version": "1.0", "snippet": "Core terms", "source": "domain/CPG", "content": {"safety_stock": "buffer inventory to absorb demand variance"}},
                {"type": "prompt_assets", "name": "base_prompt", "version": "1.0", "snippet": "domain base", "source": "domain/CPG", "content": {"composed_prompt": "You are a CPG supply chain assistant.", "reasoning_plan": ["Identify SKUs at risk"], "vector_contexts": ["CPG demand patterns"]}},
            ]
        },
    )
    write(
        "data/org/UL/artifacts.json",
        {
            "artifacts": [
                {"type": "data_bindings", "name": "ul_data", "version": "1.0", "snippet": "UL warehouse", "source": "org/UL", "content": {"tables": [{"name": "sku_daily", "columns": ["sku", "month", "region", "sales", "stock", "lead_time_days"]}], "filters": {"region": "EU"}}},
                {"type": "tool_bindings", "name": "ul_tools", "version": "1.0", "snippet": "Org tools", "source": "org/UL", "content": {"tools": [{"name": "nl2sql", "type": "function", "input_schema": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}, "input": {}}, {"name": "reorder_planner", "type": "function", "input_schema": {"type": "object", "properties": {"format": {"type": "string"}}}}]}},
            ]
        },
    )
    write(
        "data/usecase/SKUReorder/artifacts.json",
        {
            "artifacts": [
                {"type": "prompt_assets", "name": "reorder_prompt", "version": "1.0", "snippet": "Usecase formatting", "source": "usecase/SKUReorder", "content": {"composed_prompt": "Focus on monthly SKU reorder recommendations with markdown tables.", "reasoning_plan": ["Use inventory and lead time"], "vector_contexts": ["SKU reorder best practices"]}},
                {"type": "data_bindings", "name": "reorder_filters", "version": "1.0", "snippet": "January scope", "source": "usecase/SKUReorder", "content": {"filters": {"month": "January"}}},
                {"type": "tool_bindings", "name": "reorder_tools", "version": "1.0", "snippet": "Usecase tools", "source": "usecase/SKUReorder", "content": {"tools": [{"name": "reorder_risk_simulator", "type": "function", "input_schema": {"type": "object", "properties": {}, "additionalProperties": True}}]}},
            ]
        },
    )


if __name__ == "__main__":
    main()
