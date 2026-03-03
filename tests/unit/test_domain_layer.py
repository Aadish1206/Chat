from domain_layer import DomainLayer


def test_query_orchestrate_returns_layered_payload_shape():
    layer = DomainLayer("data")
    out = layer.query_orchestrate(
        query="How should I plan SKU reorder for July in East region?",
        domain="CPG",
        org="UL",
        usecase="SKUReorder",
        exclude=["knowledgebase", "evaluation-assets"],
    )

    assert out["input"]["domain"] == "CPG"
    assert isinstance(out["reasoning_plan"], list)
    assert isinstance(out["tools"], list)
    assert "artifact_refs" in out["citations"]
    assert "vector_contexts" in out["citations"]
    assert out["trace"]["domain"] == "CPG"
    assert out["trace"]["org"] == "UL"
    assert out["trace"]["usecase"] == "SKUReorder"


def test_domain_layer_search_and_list_supported():
    layer = DomainLayer("data")

    search_out = layer.search(
        query="SKU reorder inventory threshold",
        domain="CPG",
        org="UL",
        usecase="SKUReorder",
        top_n=5,
        for_each=True,
    )
    assert "results" in search_out
    assert "results_by_scope" in search_out
    assert search_out["input"]["for_each"] is True

    list_out = layer.list(
        domain="CPG",
        org="UL",
        usecase="SKUReorder",
        limit=5,
        for_each=True,
    )
    assert "results" in list_out
    assert len(list_out["results"]) <= 5
    assert "results_by_scope" in list_out
