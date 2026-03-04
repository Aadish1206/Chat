from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from cogentiq.knowledge import Knowledge
from core.schemas.api_models import CatalogItem, CatalogResponse

router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_knowledge() -> Knowledge:
    return Knowledge("data")


@router.get("/domains", response_model=CatalogResponse)
def list_domains(knowledge: Knowledge = Depends(get_knowledge)) -> CatalogResponse:
    items = [CatalogItem(id=name, name=name) for name in knowledge.domains()]
    return CatalogResponse(items=items)


@router.get("/orgs", response_model=CatalogResponse)
def list_orgs(domain: str = Query(...), knowledge: Knowledge = Depends(get_knowledge)) -> CatalogResponse:
    items = [CatalogItem(id=name, name=name) for name in knowledge.orgs(domain=domain)]
    return CatalogResponse(items=items)


@router.get("/usecases", response_model=CatalogResponse)
def list_usecases(
    domain: str = Query(...), org: str = Query(...), knowledge: Knowledge = Depends(get_knowledge)
) -> CatalogResponse:
    items = [CatalogItem(id=name, name=name) for name in knowledge.usecases(domain=domain, org=org)]
    return CatalogResponse(items=items)
