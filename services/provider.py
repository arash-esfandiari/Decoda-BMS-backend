from repositories.provider import ProviderRepository
from models import Provider

class ProviderService:
    def __init__(self, repository: ProviderRepository):
        self.repository = repository
        
    async def get_providers(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        sort_by: str = "first_name",
        sort_order: str = "asc"
    ) -> dict:
        providers, total = await self.repository.get_all(
            skip=skip, 
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return {
            "data": providers,
            "total": total,
            "page": (skip // limit) + 1,
            "limit": limit
        }

    async def get_provider_analytics(self) -> list[dict]:
        return await self.repository.get_analytics()

    async def get_provider_details(self, provider_id: str) -> dict:
        return await self.repository.get_details(provider_id)
