from core.runtime.merge import merge_effective_tool_bindings


def test_merge_precedence_and_restrictive_constraints():
    domain = {
        "id": "d1",
        "allowed_tools": ["T1", "T2"],
        "bindings": {
            "T1": {
                "defaults": {"a": 1, "x": "domain"},
                "constraints": {"max_rows": 200, "allow": ["a", "b", "c"]},
                "schema_ref": "d.schema.json",
            }
        },
    }
    org = {
        "id": "o1",
        "allowed_tools": ["T1"],
        "bindings": {
            "T1": {
                "defaults": {"a": 2},
                "constraints": {"max_rows": 100, "allow": ["b", "c"]},
                "schema_ref": "o.schema.json",
                "data_context": {"warehouse": "w"},
            }
        },
    }
    usecase = {
        "id": "u1",
        "allowed_tools": ["T1"],
        "bindings": {
            "T1": {
                "defaults": {"x": "usecase"},
                "constraints": {"max_rows": 50, "allow": ["c"]},
                "schema_ref": "u.schema.json",
            }
        },
    }

    merged = merge_effective_tool_bindings(domain, org, usecase)
    t1 = merged["bindings"]["T1"]

    assert merged["allowed_tools"] == ["T1"]
    assert t1["defaults"] == {"a": 2, "x": "usecase"}
    assert t1["constraints"]["max_rows"] == 50
    assert t1["constraints"]["allow"] == ["c"]
    assert t1["schema_ref"] == "u.schema.json"
    assert t1["data_context"] == {"warehouse": "w"}
