from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Patient, Provider, Service, Appointment, AppointmentService, Payment
from datetime import datetime

def parse_dt(dt_str):
    if not dt_str:
        return None
    # Handle various formats or fallback
    try:
        return datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
    except ValueError:
        return None

class ImportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_patients(self, data: list[dict]):
        for item in data:
            # Check if exists by ID
            stmt = select(Patient).where(Patient.id == item["id"])
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update fields
                existing.first_name = item.get("first_name", existing.first_name)
                existing.last_name = item.get("last_name", existing.last_name)
                existing.email = item.get("email", existing.email)
                existing.phone = item.get("phone", existing.phone)
                # ... add other fields as needed
            else:
                # Create new
                new_record = Patient(
                    id=item["id"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    date_of_birth=parse_dt(item.get("date_of_birth")),
                    gender=item.get("gender"),
                    address=item.get("address"),
                    phone=item.get("phone"),
                    email=item.get("email"),
                    source=item.get("source"),
                    created_date=parse_dt(item.get("created_date")) or datetime.utcnow()
                )
                self.session.add(new_record)
        await self.session.commit()

    async def upsert_providers(self, data: list[dict]):
        for item in data:
            stmt = select(Provider).where(Provider.id == item["id"])
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.first_name = item.get("first_name", existing.first_name)
                existing.last_name = item.get("last_name", existing.last_name)
                existing.email = item.get("email", existing.email)
                existing.phone = item.get("phone", existing.phone)
            else:
                new_record = Provider(
                    id=item["id"],
                    first_name=item["first_name"],
                    last_name=item["last_name"],
                    email=item.get("email"),
                    phone=item.get("phone"),
                    created_date=parse_dt(item.get("created_date")) or datetime.utcnow()
                )
                self.session.add(new_record)
        await self.session.commit()

    async def upsert_services(self, data: list[dict]):
        for item in data:
            stmt = select(Service).where(Service.id == item["id"])
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.name = item.get("name", existing.name)
                existing.price = item.get("price", existing.price)
                existing.duration = item.get("duration", existing.duration)
            else:
                new_record = Service(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                    price=item.get("price"),
                    duration=item.get("duration"),
                    created_date=parse_dt(item.get("created_date")) or datetime.utcnow()
                )
                self.session.add(new_record)
        await self.session.commit()

    async def upsert_appointments(self, data: list[dict]):
        for item in data:
            stmt = select(Appointment).where(Appointment.id == item["id"])
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.status = item.get("status", existing.status)
            else:
                new_record = Appointment(
                    id=item["id"],
                    patient_id=item["patient_id"],
                    status=item.get("status"),
                    created_date=parse_dt(item.get("created_date")) or datetime.utcnow()
                )
                self.session.add(new_record)
        await self.session.commit()

    async def upsert_appointment_services(self, data: list[dict]):
        # This one is tricky because it has a composite logic or auto-increment ID.
        # Assuming we trust the input data's logic or just append if ID not present.
        # For simplicity, if no ID is provided, we treat it as new.
        for item in data:
            # We rarely update these unless we have a specific ID. 
            # If creating new, just add.
            new_record = AppointmentService(
                appointment_id=item["appointment_id"],
                service_id=item["service_id"],
                provider_id=item["provider_id"],
                start=parse_dt(item.get("start")),
                end=parse_dt(item.get("end"))
            )
            self.session.add(new_record)
        await self.session.commit()

    async def upsert_payments(self, data: list[dict]):
        for item in data:
            stmt = select(Payment).where(Payment.id == item["id"])
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.status = item.get("status", existing.status)
            else:
                new_record = Payment(
                    id=item["id"],
                    patient_id=item["patient_id"],
                    amount=item["amount"],
                    date=parse_dt(item.get("date")),
                    method=item.get("method"),
                    status=item.get("status"),
                    provider_id=item.get("provider_id"),
                    appointment_id=item.get("appointment_id"),
                    service_id=item.get("service_id"),
                    created_date=parse_dt(item.get("created_date")) or datetime.utcnow()
                )
                self.session.add(new_record)
        await self.session.commit()
