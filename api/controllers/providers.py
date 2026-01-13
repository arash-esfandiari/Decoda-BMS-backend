from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List
from database import get_db
from repositories.provider import ProviderRepository
from services.provider import ProviderService
from schemas import PaginatedProvidersResponse, ProviderAnalytics, ProviderDetails

router = APIRouter(prefix="/providers", tags=["Providers"])

def get_provider_repository(session: AsyncSession = Depends(get_db)) -> ProviderRepository:
    return ProviderRepository(session)

def get_provider_service(repository: ProviderRepository = Depends(get_provider_repository)) -> ProviderService:
    return ProviderService(repository)

@router.get("/analytics", response_model=List[ProviderAnalytics])
async def read_provider_analytics(
    service: ProviderService = Depends(get_provider_service)
):
    return await service.get_provider_analytics()

@router.get("/", response_model=PaginatedProvidersResponse)
async def read_providers(
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    sort_by: str = "first_name",
    sort_order: str = "asc",
    service: ProviderService = Depends(get_provider_service)
):
    return await service.get_providers(
        skip=skip, 
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/{provider_id}", response_model=ProviderDetails)
async def read_provider_details(
    provider_id: str,
    service: ProviderService = Depends(get_provider_service)
):
    details = await service.get_provider_details(provider_id)
    if not details:
        raise HTTPException(status_code=404, detail="Provider not found")
    return details
