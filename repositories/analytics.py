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
