from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models import Service
from repositories.base import BaseRepository

class ServiceRepository(BaseRepository[Service]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Service)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> tuple[list[Service], int]:
        """Get all services with search and sorting"""
        query = select(self.model)
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                Service.name.ilike(search_filter) |
                Service.description.ilike(search_filter)
            )
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        if sort_by == "price":
            sort_column = self.model.price
        elif sort_by == "duration":
            sort_column = self.model.duration
        else:
            sort_column = self.model.name  # default
        
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_service_analytics(self) -> list[dict]:
        """Aggregate analytics for services: counts, revenue, and duration"""
        from models import AppointmentService
        from sqlalchemy import desc

        stmt = (
            select(
                self.model.name,
                func.count(AppointmentService.id).label("count"),
                func.sum(self.model.price).label("revenue"),
                self.model.duration.label("duration")
            )
            .join(AppointmentService, self.model.id == AppointmentService.service_id)
            .group_by(self.model.id, self.model.name, self.model.duration)
            .order_by(desc("count"))
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        return [
            {
                "name": row.name,
                "count": row.count,
                "revenue": row.revenue,
                "duration": row.duration,
                "revenue_per_minute": round((row.revenue / row.count) / row.duration, 2) if row.duration > 0 else 0
            }
            for row in rows
        ]
