from __future__ import annotations

import json

import pytest

from cogentiq.knowledge import Knowledge


def test_discovery_lists_are_available() -> None:
    kn = Knowledge(data_root="data")
    assert "CPG" in kn.domains()
    assert "UL" in kn.orgs()
    assert "SKUReorder" in kn.usecases()
    assert "ontology" in kn.supported_types()


def test_list_requires_exactly_one_scope() -> None:
    kn = Knowledge(data_root="data")

    with pytest.raises(ValueError, match="Exactly one of domain, org, or usecase must be provided"):
        kn.list()

    with pytest.raises(ValueError, match="DOMAIN, ORG"):
        kn.list(domain="CPG", org="UL")


def test_list_reports_missing_scope_artifacts() -> None:
    kn = Knowledge(data_root="data")

    with pytest.raises(FileNotFoundError, match="No artifacts found for domain='Missing'"):
        kn.list(domain="Missing")


def test_limits_must_cover_all_requested_sections() -> None:
    kn = Knowledge(data_root="data")

    with pytest.raises(ValueError, match="limits dict is missing entries for requested sections: ontology"):
        kn.list(domain="CPG", include=["glossary", "ontology"], limits={"glossary": 1})


def test_list_returns_meta_and_section_content() -> None:
    kn = Knowledge(data_root="data")
    result = kn.list(org="UL", include=["data_bindings", "tool_bindings"], limits={"data_bindings": 1, "tool_bindings": 1})

    assert result["meta"]["layer"] == "ORG"
    assert result["meta"]["identifier"] == "UL"
    assert len(result["data_bindings"]) == 1
    assert len(result["tool_bindings"]) == 1


def test_ontology_limit_applies_to_entities_only(tmp_path) -> None:
    root = tmp_path / "data"
    (root / "domain" / "Demo").mkdir(parents=True)
    payload = {
        "artifacts": [
            {
                "type": "ontology",
                "content": {
                    "entities": [{"name": "A"}, {"name": "B"}],
                    "relationships": [{"from": "A", "to": "B", "type": "rel"}],
                },
            }
        ]
    }
    (root / "domain" / "Demo" / "artifacts.json").write_text(json.dumps(payload))

    kn = Knowledge(data_root=str(root))
    result = kn.list(domain="Demo", include=["ontology"], limits={"ontology": 1})

    ontology = result["ontology"]
    assert len(ontology["entities"]) == 1
    assert len(ontology["relationships"]) == 1
