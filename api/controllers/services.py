from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

"""
Controller for Services.
Manages service catalog, price lookups, and service popularity analytics.
"""

from database import get_db
from repositories.service import ServiceRepository
from services.service import ServiceService
from schemas import Service as ServiceSchema, PaginatedServicesResponse, ServiceAnalytics

router = APIRouter(prefix="/services", tags=["Services"])

def get_service_repository(session: AsyncSession = Depends(get_db)) -> ServiceRepository:
    return ServiceRepository(session)

def get_service_service(repository: ServiceRepository = Depends(get_service_repository)) -> ServiceService:
    return ServiceService(repository)

@router.get("/", response_model=PaginatedServicesResponse)
async def read_services(
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    service: ServiceService = Depends(get_service_service)
):
    return await service.get_services(
        skip=skip, 
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/analytics", response_model=List[ServiceAnalytics])
async def read_service_analytics(
    service: ServiceService = Depends(get_service_service)
):
    """
    Get analytics for services to identify top-performing treatments.
    """
    return await service.get_service_analytics()
