from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from repositories.analytics import AnalyticsRepository
from services.analytics import AnalyticsService
from api.analytics_schema import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["Analytics"])

def get_analytics_repository(session: AsyncSession = Depends(get_db)) -> AnalyticsRepository:
    return AnalyticsRepository(session)

def get_analytics_service(repository: AnalyticsRepository = Depends(get_analytics_repository)) -> AnalyticsService:
    return AnalyticsService(repository)

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(service: AnalyticsService = Depends(get_analytics_service)):
    return await service.get_summary()
