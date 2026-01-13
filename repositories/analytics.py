from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, literal_column
from repositories.base import BaseRepository
from models import Patient, Appointment, Payment, Service, AppointmentService, Provider

class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_total_revenue(self) -> int:
        result = await self.session.execute(select(func.sum(Payment.amount)).where(Payment.status == 'paid'))
        return result.scalar() or 0

    async def get_total_patients(self) -> int:
        result = await self.session.execute(select(func.count(Patient.id)))
        return result.scalar() or 0

    async def get_total_appointments(self) -> int:
        result = await self.session.execute(select(func.count(Appointment.id)))
        return result.scalar() or 0

    async def get_patients_by_source(self):
        result = await self.session.execute(
            select(Patient.source, func.count(Patient.id)).group_by(Patient.source)
        )
        return result.all()

    async def get_top_services(self, limit: int = 5):
        # Join AppointmentService with Service to get names
        stmt = (
            select(Service.name, func.count(AppointmentService.service_id).label("count"))
            .join(AppointmentService, Service.id == AppointmentService.service_id)
            .group_by(Service.name)
            .order_by(desc("count"))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_appointments_by_status(self):
        result = await self.session.execute(
            select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status)
        )
        return result.all()

    async def get_monthly_revenue(self):
        # Group payments by month for the last 12 months
        # Note: SQLite vs Postgres date functions differ. Assuming Postgres based on recent interactions.
        # "YYYY-MM" format
        stmt = (
            select(
                func.to_char(Payment.date, 'YYYY-MM').label('month'),
                func.sum(Payment.amount)
            )
            .where(Payment.status == 'paid')
            .group_by('month')
            .order_by('month')
            .limit(12)
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_patient_demographics(self):
        # Gender
        gender_result = await self.session.execute(
            select(Patient.gender, func.count(Patient.id)).group_by(Patient.gender)
        )
        
        # Age
        # Calculate age from DOB. 
        # PostgreSQL: extract(year from age(current_date, date_of_birth))
        stmt_age = (
             select(
                func.width_bucket(func.extract('year', func.age(Patient.date_of_birth)), 0, 100, 10).label('age_group'),
                func.count(Patient.id)
            ).group_by('age_group').order_by('age_group')
        )
        age_result = await self.session.execute(stmt_age)
        
        return {
            "gender": gender_result.all(),
            "age": age_result.all()
        }

    async def get_appointment_patterns(self):
        # Day of week (0=Sunday, 6=Saturday in some versions, or 1-7). Postgres: isodow (1=Mon, 7=Sun) or dow (0=Sun, 6=Sat)
        # Let's use to_char(Day) for simpler labeling later
        stmt = (
            select(func.to_char(AppointmentService.start, literal_column("'Day'")), func.count(AppointmentService.appointment_id))
            .select_from(AppointmentService)
            .join(Appointment, AppointmentService.appointment_id == Appointment.id) # Ensure we are counting valid appts
            .group_by(func.to_char(AppointmentService.start, literal_column("'Day'")))
        )
        result = await self.session.execute(stmt)
        result = await self.session.execute(stmt)
        return result.all()

    async def get_provider_revenue(self):
        # Revenue by provider
        # Join Payment with Provider
        stmt = (
            select(
                func.concat(Provider.first_name, ' ', Provider.last_name).label('provider_name'),
                func.sum(Payment.amount)
            )
            .join(Provider, Payment.provider_id == Provider.id)
            .where(Payment.status == 'paid')
            .group_by('provider_name')
            .order_by(func.sum(Payment.amount).desc())
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_provider_services(self):
        # Services by provider
        # Join AppointmentService with Provider
        stmt = (
            select(
                func.concat(Provider.first_name, ' ', Provider.last_name).label('provider_name'),
                func.count(AppointmentService.id)
            )
            .join(Provider, AppointmentService.provider_id == Provider.id)
            .group_by('provider_name')
            .order_by(func.count(AppointmentService.id).desc())
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_top_patients(self, limit: int = 5) -> list[dict]:
        from sqlalchemy import case
        # Top patients by total value of services provided (excluding cancelled appointments for revenue)
        # But visit count includes all appointments
        
        stmt = (
            select(
                Patient.id,
                func.concat(Patient.first_name, ' ', Patient.last_name).label('name'),
                func.sum(
                    case(
                        (Appointment.status != 'cancelled', Service.price),
                        else_=0
                    )
                ).label('total_spent'),
                func.count(func.distinct(Appointment.id)).label('visit_count'),
                func.max(AppointmentService.start).label('last_visit')
            )
            .join(Appointment, Appointment.patient_id == Patient.id)
            .join(AppointmentService, AppointmentService.appointment_id == Appointment.id)
            .join(Service, AppointmentService.service_id == Service.id)
            .group_by(Patient.id, Patient.first_name, Patient.last_name)
            .order_by(
                func.sum(
                    case(
                        (Appointment.status != 'cancelled', Service.price),
                        else_=0
                    )
                ).desc()
            )
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
                Patient.id,
                func.concat(Patient.first_name, ' ', Patient.last_name).label('name'),
                Patient.phone,
                Patient.email,
                func.max(AppointmentService.start).label('last_visit'),
                func.count(func.distinct(Appointment.id)).label('visit_count')
            )
            .join(Appointment, Appointment.patient_id == Patient.id)
            .join(AppointmentService, AppointmentService.appointment_id == Appointment.id)
            .group_by(Patient.id, Patient.first_name, Patient.last_name, Patient.phone, Patient.email)
            .having(
                (func.count(func.distinct(Appointment.id)) >= 2) & 
                (func.max(AppointmentService.start) < sixty_days_ago)
            )
        )
        
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
