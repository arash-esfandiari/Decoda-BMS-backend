from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models import Appointment, AppointmentService, Patient, Service, Provider
from repositories.base import BaseRepository

class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Appointment)

    async def get_all_with_patient(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        sort_by: str = "start_time",
        sort_order: str = "desc",
        date_filter: str = None  # "today", "all"
    ) -> tuple[list[Appointment], int]:
        """Get all appointments with patient information loaded, with search and sorting"""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.patient),
                selectinload(self.model.services)
                .selectinload(AppointmentService.service),
                selectinload(self.model.services)
                .selectinload(AppointmentService.provider),
                selectinload(self.model.payments)
            )
        )
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.join(self.model.patient).where(
                Patient.first_name.ilike(search_filter) |
                Patient.last_name.ilike(search_filter) |
                (Patient.first_name + ' ' + Patient.last_name).ilike(search_filter) |
                self.model.id.ilike(search_filter)
            )
        
        # Apply date filter
        if date_filter == "today":
            from datetime import datetime, timedelta
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Subquery to find appointments with services starting today
            today_appointments_subquery = (
                select(AppointmentService.appointment_id)
                .where(
                    (AppointmentService.start >= today_start) &
                    (AppointmentService.start < today_end)
                )
                .distinct()
                .subquery()
            )
            query = query.where(self.model.id.in_(select(today_appointments_subquery)))
        
        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        if sort_by == "start_time":
            # For start_time, we need to sort by the minimum start time of services
            # Create a subquery to get min start time per appointment
            start_time_subquery = (
                select(
                    AppointmentService.appointment_id,
                    func.min(AppointmentService.start).label('min_start')
                )
                .group_by(AppointmentService.appointment_id)
                .subquery()
            )
            query = query.outerjoin(
                start_time_subquery,
                self.model.id == start_time_subquery.c.appointment_id
            )
            sort_column = start_time_subquery.c.min_start
        elif sort_by == "status":
            sort_column = self.model.status
        elif sort_by == "patient_name":
            sort_column = Patient.last_name
            query = query.join(self.model.patient) if not search else query
        else:
            sort_column = self.model.created_date  # default
        
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id_with_details(self, appointment_id: str):
        """Get appointment with all related data: patient, services, providers"""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.patient),
                selectinload(self.model.services)
                .selectinload(AppointmentService.service),
                selectinload(self.model.services)
                .selectinload(AppointmentService.provider),
                selectinload(self.model.payments)
            )
            .where(self.model.id == appointment_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_analytics(self) -> dict:
        """Get appointment analytics"""
        from datetime import datetime, timedelta
        
        query = select(self.model).options(
            selectinload(self.model.services).selectinload(AppointmentService.service)
        )
        result = await self.session.execute(query)
        appointments = result.scalars().all()
        
        total = len(appointments)
        confirmed = sum(1 for a in appointments if a.status == "confirmed")
        pending = sum(1 for a in appointments if a.status == "pending")
        cancelled = sum(1 for a in appointments if a.status == "cancelled")
        
        # Calculate today's appointments (appointments with start time today)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_count = 0
        today_confirmed = 0
        today_pending = 0
        today_cancelled = 0
        
        for apt in appointments:
            if apt.services:
                starts = [svc.start for svc in apt.services if svc.start]
                if starts:
                    earliest_start = min(starts)
                    if today_start <= earliest_start < today_end:
                        today_count += 1
                        if apt.status == "confirmed":
                            today_confirmed += 1
                        elif apt.status == "pending":
                            today_pending += 1
                        elif apt.status == "cancelled":
                            today_cancelled += 1
        
        total_revenue = 0
        total_duration = 0
        count_with_duration = 0
        # Initialize all days to ensure 0 counts are shown
        day_mapping = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        day_counts = {day: 0 for day in day_mapping.keys()}
        
        for apt in appointments:
            if apt.services:
                for svc in apt.services:
                    if svc.service and svc.service.price:
                        total_revenue += svc.service.price
                    if svc.start and svc.end:
                        duration = (svc.end - svc.start).total_seconds() / 60
                        total_duration += duration
                        count_with_duration += 1
                        
                        # Count day of week
                        day_name = svc.start.strftime('%A')
                        if day_name in day_counts:
                            day_counts[day_name] += 1
        
        avg_duration = total_duration / count_with_duration if count_with_duration > 0 else 0
        
        # Format busiest days sorted Mon-Sun
        busiest_days = [
            {"label": day, "value": day_counts[day]} 
            for day in sorted(day_counts.keys(), key=lambda d: day_mapping[d])
        ]
        
        return {
            "total_appointments": total,
            "confirmed": confirmed,
            "pending": pending,
            "cancelled": cancelled,
            "today_appointments": today_count,
            "today_confirmed": today_confirmed,
            "today_pending": today_pending,
            "today_cancelled": today_cancelled,
            "total_revenue": total_revenue,
            "avg_duration_minutes": round(avg_duration, 1),
            "busiest_days": busiest_days
        }
