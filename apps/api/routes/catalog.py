from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from core.registry.file_registry import FileRegistry
from core.schemas.api_models import CatalogItem, CatalogResponse

router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_registry() -> FileRegistry:
    return FileRegistry()


@router.get("/domains", response_model=CatalogResponse)
def list_domains(registry: FileRegistry = Depends(get_registry)) -> CatalogResponse:
    items = [CatalogItem(**item) for item in registry.list_domains()]
    return CatalogResponse(items=items)


@router.get("/orgs", response_model=CatalogResponse)
def list_orgs(domain: str = Query(...), registry: FileRegistry = Depends(get_registry)) -> CatalogResponse:
    items = [CatalogItem(**item) for item in registry.list_orgs(domain)]
    return CatalogResponse(items=items)


@router.get("/usecases", response_model=CatalogResponse)
def list_usecases(
    domain: str = Query(...), org: str = Query(...), registry: FileRegistry = Depends(get_registry)
) -> CatalogResponse:
    items = [CatalogItem(**item) for item in registry.list_usecases(domain, org)]
    return CatalogResponse(items=items)
