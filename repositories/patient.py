from sqlalchemy.ext.asyncio import AsyncSession
from models import Patient
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models import Patient
from repositories.base import BaseRepository

class PatientRepository(BaseRepository[Patient]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Patient)
    
    
    async def get_by_id_with_appointments(self, patient_id: str):
        """Get patient with all appointments loaded"""
        from models import Appointment, AppointmentService
        
        query = (
            select(self.model)
            .options(
                selectinload(self.model.appointments)
                .selectinload(Appointment.services)
                .selectinload(AppointmentService.service)
            )
            .where(self.model.id == patient_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: str = None, 
        sort_by: str = "first_name", 
        sort_order: str = "asc"
    ) -> tuple[list[Patient], int]:
        # Base query structure for filtering
        filters = []
        if search:
            search_filter = f"%{search}%"
            # Concatenate first_name and last_name for full name search
            full_name = func.concat(self.model.first_name, ' ', self.model.last_name)
            
            filters.append(
                (self.model.first_name.ilike(search_filter)) |
                (self.model.last_name.ilike(search_filter)) |
                (self.model.email.ilike(search_filter)) |
                (full_name.ilike(search_filter))  # Match "FirstName LastName"
            )

        # Get total count
        count_query = select(func.count()).select_from(self.model)
        for f in filters:
            count_query = count_query.where(f)
        total = await self.session.scalar(count_query) or 0

        # Get data
        query = select(self.model)
        for f in filters:
            query = query.where(f)
            
        if sort_by:
            sort_attr = getattr(self.model, sort_by, self.model.first_name)
            if sort_order == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
             query = query.order_by(self.model.first_name.asc())

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def get_analytics(self) -> dict:
        # Total Patients
        total_query = select(func.count(self.model.id))
        total = await self.session.scalar(total_query) or 0

        # By Source
        source_query = select(self.model.source, func.count(self.model.id)).group_by(self.model.source)
        source_result = await self.session.execute(source_query)
        by_source = [{"label": s.replace('_', ' ').title() if s else "Unknown", "value": c} for s, c in source_result.all()]

        # By Gender
        gender_query = select(self.model.gender, func.count(self.model.id)).group_by(self.model.gender)
        gender_result = await self.session.execute(gender_query)
        by_gender = [{"label": g.title() if g else "Unknown", "value": c} for g, c in gender_result.all()]

        # Average Age & By Decade
        # Postgres-specific age calculation
        age_in_years = func.extract('year', func.age(self.model.date_of_birth))
        
        avg_age_query = select(func.avg(age_in_years))
        avg_age = await self.session.scalar(avg_age_query) or 0

        decade_expr = func.floor(age_in_years / 10) * 10
        decade_query = select(decade_expr, func.count(self.model.id)).group_by(decade_expr).order_by(decade_expr)
        decade_result = await self.session.execute(decade_query)
        by_decade = [{"label": f"{int(d)}s", "value": c} for d, c in decade_result.all() if d is not None]

        return {
            "total_patients": total,
            "by_source": by_source,
            "by_gender": by_gender,
            "average_age": round(float(avg_age), 1),
            "by_decade": by_decade,
            "top_patients": await self.get_top_patients(),
            "retention_opportunities": await self.get_retention_opportunities()
        }

    async def get_top_patients(self, limit: int = 5) -> list[dict]:
        from models import Payment, Appointment
        
        # Top patients by total payment amount
        stmt = (
            select(
                self.model.id,
                func.concat(self.model.first_name, ' ', self.model.last_name).label('name'),
                func.sum(Payment.amount).label('total_spent'),
                func.count(func.distinct(Appointment.id)).label('visit_count'),
                func.max(Payment.date).label('last_visit')
            )
            .join(Payment, Payment.patient_id == self.model.id)
            .outerjoin(Appointment, Appointment.patient_id == self.model.id)
            .group_by(self.model.id, self.model.first_name, self.model.last_name)
            .order_by(func.sum(Payment.amount).desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return [
            {
                "id": r.id, 
                "name": r.name, 
                "total_spent": (r.total_spent or 0) / 100.0, # Convert cents to dollars
                "visit_count": r.visit_count,
                "last_visit": r.last_visit
            } 
            for r in result
        ]

    async def get_retention_opportunities(self, limit: int = 5) -> list[dict]:
        from models import Appointment, AppointmentService
        from datetime import datetime, timedelta
        
        # Logic:
        # 1. Regulars: At least 2 past appointments
        # 2. At risk: Last appointment was > 60 days ago
        # 3. Opportunity: No future appointments booked
        
        sixty_days_ago = datetime.now() - timedelta(days=60)
        now = datetime.now()
        
        # Subquery for last appointment date per patient
        # We need to join Appointment -> AppointmentService to get the actual date
        
        stmt = (
            select(
                self.model.id,
                func.concat(self.model.first_name, ' ', self.model.last_name).label('name'),
                self.model.phone,
                self.model.email,
                func.max(AppointmentService.start).label('last_visit'),
                func.count(func.distinct(Appointment.id)).label('visit_count')
            )
            .join(Appointment, Appointment.patient_id == self.model.id)
            .join(AppointmentService, AppointmentService.appointment_id == Appointment.id)
            .group_by(self.model.id, self.model.first_name, self.model.last_name, self.model.phone, self.model.email)
            .having(
                (func.count(func.distinct(Appointment.id)) >= 2) & 
                (func.max(AppointmentService.start) < sixty_days_ago)
            )
        )
        
        # Execute and filter in python for "no future appointments" 
        # (Doing pure SQL for "no future" with having/subqueries is complex in asyncpg/sqlalchemy randomly sometimes, 
        # easier to filter the small list of candidates or use a NOT EXISTS)
        
        # Let's try adding a NOT EXISTS clause for robustness
        # Actually, simpler: fetch candidates, then check if they have future appts.
        
        result = await self.session.execute(stmt)
        candidates = result.all()
        
        opportunities = []
        for r in candidates:
            # Check for future appointments
            future_check = (
                select(func.count(Appointment.id))
                .join(AppointmentService)
                .where(
                    (Appointment.patient_id == r.id) &
                    (AppointmentService.start > now) &
                    (Appointment.status != 'cancelled')
                )
            )
            future_count = await self.session.scalar(future_check) or 0
            
            if future_count == 0:
                days_since = (now - r.last_visit).days
                opportunities.append({
                    "id": r.id,
                    "name": r.name,
                    "last_visit": r.last_visit,
                    "days_since_last_visit": days_since,
                    "phone": r.phone,
                    "email": r.email
                })
                
        # Sort by days since last visit (descending) -> most overdue first
        opportunities.sort(key=lambda x: x['days_since_last_visit'], reverse=True)
        
        return opportunities[:limit]
