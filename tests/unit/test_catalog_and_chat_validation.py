import asyncio

import pytest
from fastapi import HTTPException

from apps.api.routes.chat import ChatRequest, chat
from cogentiq.knowledge import Knowledge


def test_catalog_respects_domain_org_filters():
    knowledge = Knowledge("data")

    assert set(knowledge.orgs(domain="CPG")) == {"PG", "UL"}
    assert set(knowledge.usecases(domain="CPG", org="UL")) == {"SKUReorder"}
    assert set(knowledge.usecases(domain="CPG", org="PG")) == {"PromoEffectiveness"}


def test_chat_returns_404_for_invalid_combo():
    req = ChatRequest(domain="CPG", org="UL", usecase="FraudWatch", message="help", top_n=5)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(chat(req, runtime=None, knowledge=Knowledge("data")))

    assert exc.value.status_code == 404
    assert "Unknown usecase" in str(exc.value.detail)
