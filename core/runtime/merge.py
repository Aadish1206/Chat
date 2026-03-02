from __future__ import annotations

import copy
from typing import Any


def _merge_defaults(*values: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        merged.update(value)
    return merged


def _merge_constraints(*values: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        for key, v in value.items():
            if key not in merged:
                merged[key] = copy.deepcopy(v)
                continue

            existing = merged[key]
            if isinstance(v, (int, float)) and isinstance(existing, (int, float)):
                merged[key] = min(existing, v)
            elif isinstance(v, list) and isinstance(existing, list):
                merged[key] = [item for item in existing if item in v]
            else:
                merged[key] = v
    return merged


def merge_effective_tool_bindings(
    domain_bindings: dict[str, Any],
    org_bindings: dict[str, Any],
    usecase_bindings: dict[str, Any],
) -> dict[str, Any]:
    domain_tools = set(domain_bindings.get("allowed_tools", []))
    org_tools = set(org_bindings.get("allowed_tools", []))
    usecase_tools = set(usecase_bindings.get("allowed_tools", []))
    effective_tools = sorted(domain_tools & org_tools & usecase_tools)

    result: dict[str, Any] = {
        "allowed_tools": effective_tools,
        "bindings": {},
        "binding_refs": {
            "domain": domain_bindings.get("id"),
            "org": org_bindings.get("id"),
            "usecase": usecase_bindings.get("id"),
        },
    }

    for tool in effective_tools:
        d = domain_bindings.get("bindings", {}).get(tool, {})
        o = org_bindings.get("bindings", {}).get(tool, {})
        u = usecase_bindings.get("bindings", {}).get(tool, {})

        result["bindings"][tool] = {
            "defaults": _merge_defaults(d.get("defaults", {}), o.get("defaults", {}), u.get("defaults", {})),
            "constraints": _merge_constraints(
                d.get("constraints", {}), o.get("constraints", {}), u.get("constraints", {})
            ),
            "schema_ref": u.get("schema_ref") or o.get("schema_ref") or d.get("schema_ref"),
        }
        if o.get("data_context"):
            result["bindings"][tool]["data_context"] = o["data_context"]
    return result
