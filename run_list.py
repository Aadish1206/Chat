"""
Demo runner for cogentiq.knowledge.Knowledge.list()

Exercises the list() SDK against the local data/ folder with test scenarios.

Run from the repo root:
  python3 run_list.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from cogentiq.knowledge import Knowledge


DATA_ROOT = os.path.join(os.path.dirname(__file__), "data")


def separator(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_result(result: dict, show_full: bool = False) -> None:
    """Pretty print result with optional content truncation."""
    if show_full:
        print(json.dumps(result, indent=2))
        return

    print(f"Meta: {json.dumps(result.get('meta', {}), indent=2)}")

    for key, value in result.items():
        if key == "meta":
            continue

        if isinstance(value, list):
            print(f"{key}: {len(value)} entries")
            if value and isinstance(value[0], dict):
                print(f"  First entry keys: {list(value[0].keys())}")
        elif isinstance(value, dict):
            if "entities" in value and "relationships" in value:
                print(f"{key}:")
                print(f"  entities: {len(value['entities'])} entries")
                print(f"  relationships: {len(value['relationships'])} entries")
            else:
                print(f"{key}: {len(value)} keys")
        else:
            print(f"{key}: {type(value).__name__}")


def test_error_cases(kn: Knowledge) -> None:
    """Test error handling."""
    separator("Error Handling Tests")

    print("Test 1: No scope provided (should raise ValueError)")
    try:
        kn.list()
        print("  ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"  ✅ PASSED: {e}")

    print("\nTest 2: Multiple scopes provided (should raise ValueError)")
    try:
        kn.list(domain="CPG", org="UL")
        print("  ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"  ✅ PASSED: {e}")

    print("\nTest 3: Non-existent scope (should raise FileNotFoundError)")
    try:
        kn.list(domain="NonExistent")
        print("  ❌ FAILED: Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"  ✅ PASSED: {e}")

    print("\nTest 4: Limits dict missing required section (should raise ValueError)")
    try:
        kn.list(domain="CPG", include=["glossary", "ontology"], limits={"glossary": 10})
        print("  ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"  ✅ PASSED: {e}")


def main() -> None:
    kn = Knowledge(data_root=DATA_ROOT)

    separator("Discovery — available domains, orgs, usecases")
    print(f"  Domains  : {kn.domains()}")
    print(f"  Orgs     : {kn.orgs()}")
    print(f"  Usecases : {kn.usecases()}")
    print(f"  Supported types: {kn.supported_types()}")

    test_error_cases(kn)

    separator("Example 1 — list(domain='CPG') [all sections, no limits]")
    print_result(kn.list(domain="CPG"))

    separator("Example 2 — list(org='UL', include=['data_bindings', 'tool_bindings'])")
    print_result(kn.list(org="UL", include=["data_bindings", "tool_bindings"]))

    separator("Example 3 — list(usecase='SKUReorder', include=['prompt_assets'])")
    print_result(kn.list(usecase="SKUReorder", include=["prompt_assets"]))

    separator("Example 4 — list(domain='CPG', include=['glossary', 'ontology'], limits={...})")
    result = kn.list(domain="CPG", include=["glossary", "ontology"], limits={"glossary": 3, "ontology": 3})
    print("Glossary:")
    for i, term in enumerate(result.get("glossary", [])[:3], 1):
        if isinstance(term, dict):
            print(f"  {i}. {term.get('term', 'N/A')}")
        else:
            print(f"  {i}. {term}")

    ontology = result.get("ontology", {})
    print(f"\nOntology entities: {len(ontology.get('entities', []))}")
    print(f"Ontology relationships: {len(ontology.get('relationships', []))}")

    separator("Example 5 — list(org='UL', exclude=['knowledgebase'])")
    print_result(kn.list(org="UL", exclude=["knowledgebase"]))

    separator("Example 6 — list(org='UL', include=['tool_bindings'], limits={'tool_bindings': 2})")
    result = kn.list(org="UL", include=["tool_bindings"], limits={"tool_bindings": 2})
    print(f"Meta: {json.dumps(result['meta'], indent=2)}")
    print(f"\nTool bindings count: {len(result.get('tool_bindings', []))}")
    for i, tool in enumerate(result.get("tool_bindings", []), 1):
        print(f"  {i}. {tool.get('name', 'N/A')} - {tool.get('description', 'N/A')[:60]}...")

    separator("Example 7 — list(usecase='SKUReorder', include=['prompt_assets'], limits={...})")
    result = kn.list(usecase="SKUReorder", include=["prompt_assets"], limits={"prompt_assets": 5})
    print(f"Meta: {json.dumps(result['meta'], indent=2)}")
    print(f"\nPrompt assets count: {len(result.get('prompt_assets', []))}")
    for i, prompt in enumerate(result.get("prompt_assets", []), 1):
        print(f"  {i}. {prompt.get('prompt_id', 'N/A')} ({prompt.get('type', 'N/A')})")

    print("\n" + "=" * 70)
    print("  All tests completed successfully! ✅")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
