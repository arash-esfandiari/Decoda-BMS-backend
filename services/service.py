from typing import List
from repositories.service import ServiceRepository
from models import Service

class ServiceService:
    def __init__(self, repository: ServiceRepository):
        self.repository = repository
    
    async def get_services(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> dict:
        services, total = await self.repository.get_all(
            skip=skip, 
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {"data": services, "total": total}

    async def get_service_analytics(self) -> list[dict]:
        return await self.repository.get_service_analytics()
