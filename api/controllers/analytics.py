from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

"""
Controller for Analytics.
Provides high-level analytics summaries and business intelligence data
aggregated from various services.
"""

from database import get_db
from repositories.analytics import AnalyticsRepository
from services.analytics import AnalyticsService
from schemas import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Provide repository instance per request.
def get_analytics_repository(session: AsyncSession = Depends(get_db)) -> AnalyticsRepository:
    return AnalyticsRepository(session)

# Provide service instance per request.
def get_analytics_service(repository: AnalyticsRepository = Depends(get_analytics_repository)) -> AnalyticsService:
    """Dependency injection for AnalyticsService"""
    return AnalyticsService(repository)

# Return the aggregated analytics summary for the dashboard.
@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(service: AnalyticsService = Depends(get_analytics_service)):
    return await service.get_summary()
