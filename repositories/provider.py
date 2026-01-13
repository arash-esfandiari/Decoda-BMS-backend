from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import Provider
from repositories.base import BaseRepository

class ProviderRepository(BaseRepository[Provider]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Provider)
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        sort_by: str = "first_name",
        sort_order: str = "asc"
    ) -> tuple[list[Provider], int]:
        """Get all providers with search and sorting"""
        query = select(self.model)
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (self.model.first_name + " " + self.model.last_name).ilike(search_filter) |
                self.model.email.ilike(search_filter)
            )
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        if sort_by == "last_name":
            sort_column = self.model.last_name
        elif sort_by == "email":
            sort_column = self.model.email
        elif sort_by == "created_date":
            sort_column = self.model.created_date
        else:
            sort_column = self.model.first_name  # default
        
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_analytics(self) -> list[dict]:
        """Aggregate analytics for providers"""
        from models import AppointmentService, Service, Appointment
        from sqlalchemy import desc, distinct

        stmt = (
            select(
                self.model.first_name,
                self.model.last_name,
                func.count(AppointmentService.id).label("total_services"),
                func.sum(Service.price).label("total_revenue"),
                func.count(distinct(Appointment.patient_id)).label("unique_patients")
            )
            .join(AppointmentService, self.model.id == AppointmentService.provider_id)
            .join(Service, AppointmentService.service_id == Service.id)
            .join(Appointment, AppointmentService.appointment_id == Appointment.id)
            .group_by(self.model.id, self.model.first_name, self.model.last_name)
            .order_by(desc("total_revenue"))
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        return [
            {
                "provider_name": f"{row.first_name} {row.last_name}",
                "total_services": row.total_services,
                "total_revenue": row.total_revenue or 0,
                "unique_patients": row.unique_patients,
                "average_ticket": round((row.total_revenue or 0) / row.total_services, 2) if row.total_services > 0 else 0
            }
            for row in rows
        ]

    async def get_details(self, provider_id: str) -> dict:
        """Get detailed provider info including stats and services"""
        from models import AppointmentService, Service, Appointment
        from sqlalchemy import distinct, cast, Date

        # Get Provider
        provider = await self.get_by_id(provider_id)
        if not provider:
            return None

        # Get Services
        services_stmt = (
            select(Service)
            .join(AppointmentService, Service.id == AppointmentService.service_id)
            .where(AppointmentService.provider_id == provider_id)
            .distinct()
        )
        services_result = await self.session.execute(services_stmt)
        services = services_result.scalars().all()

        # Get Average Patients Per Day
        # We group by the date of service start
        subq = (
            select(
                func.count(distinct(Appointment.patient_id)).label("daily_patients")
            )
            .join(AppointmentService, Appointment.id == AppointmentService.appointment_id)
            .where(AppointmentService.provider_id == provider_id)
            .group_by(func.date(AppointmentService.start))
            .subquery()
        )

        avg_stmt = select(func.avg(subq.c.daily_patients))
        avg_result = await self.session.execute(avg_stmt)
        average = avg_result.scalar() or 0.0

        # Construct response dict merging provider fields and new stats
        return {
            "id": provider.id,
            "first_name": provider.first_name,
            "last_name": provider.last_name,
            "email": provider.email,
            "phone": provider.phone,
            "created_date": provider.created_date,
            "average_patients_per_day": round(average, 1),
            "services": services
        }
