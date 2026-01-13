import asyncio
import json
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal, engine, Base
from models import Patient, Provider, Service, Appointment, AppointmentService, Payment

# Example inline comment: Helper to parse timestamps properly
# Helper to parse datetime
def parse_dt(dt_str):
    if not dt_str:
        return None
    # Fix 'Z' suffix for Python 3.9/3.10 ISO compatibility if needed, though modern fromisoformat handles it better.
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

# Reads JSON file asynchronously (well, file IO is blocking here but it's fast enough for seed data)
async def load_json(filename):
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "..", "seed_data", filename)
    with open(file_path, "r") as f:
        return json.load(f)

async def seed_data():
    # 1. Recreate tables to ensure a clean slate
    # WARNING: This wipes existing data!
    async with engine.begin() as conn:
        print("Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)

    # 2. Start a DB session to insert data
    async with AsyncSessionLocal() as session:
        # --- SEED PATIENTS ---
        print("Seeding Patients...")
        patients_data = await load_json("patient.json")
        patients = [
            Patient(
                id=p["id"],
                first_name=p["first_name"],
                last_name=p["last_name"],
                date_of_birth=parse_dt(p["date_of_birth"]),
                gender=p["gender"],
                address=p["address"],
                phone=p["phone"],
                email=p["email"],
                source=p.get("source"),
                created_date=parse_dt(p["created_date"])
            ) for p in patients_data
        ]
        session.add_all(patients)
        
        # --- SEED PROVIDERS ---
        print("Seeding Providers...")
        providers_data = await load_json("provider.json")
        providers = [
            Provider(
                id=p["id"],
                first_name=p["first_name"],
                last_name=p["last_name"],
                email=p["email"],
                phone=p["phone"],
                created_date=parse_dt(p["created_date"])
            ) for p in providers_data
        ]
        session.add_all(providers)

        # --- SEED SERVICES ---
        print("Seeding Services...")
        services_data = await load_json("service.json")
        services = [
            Service(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                price=s["price"],
                duration=s["duration"],
                created_date=parse_dt(s["created_date"])
            ) for s in services_data
        ]
        session.add_all(services)
        
        # Commit patients, providers, services first so they can be referenced
        await session.commit() 

        # --- SEED APPOINTMENTS ---
        print("Seeding Appointments...")
        appointments_data = await load_json("appointment.json")
        appointments = [
             Appointment(
                id=a["id"],
                patient_id=a["patient_id"],
                status=a["status"],
                created_date=parse_dt(a["created_date"])
            ) for a in appointments_data
        ]
        session.add_all(appointments)
        await session.commit() # Commit appointments to reference them in payments/app_services

        # --- SEED APPOINTMENTS SERVICES (Link Table) ---
        print("Seeding Appointment Services...")
        app_services_data = await load_json("appointment_service.json")
        app_services = [
            AppointmentService(
                appointment_id=aps["appointment_id"],
                service_id=aps["service_id"],
                provider_id=aps["provider_id"],
                start=parse_dt(aps["start"]),
                end=parse_dt(aps["end"])
            ) for aps in app_services_data
        ]
        session.add_all(app_services)

        # --- SEED PAYMENTS ---
        print("Seeding Payments...")
        payments_data = await load_json("payment.json")
        payments = [
            Payment(
                id=pym["id"],
                patient_id=pym["patient_id"],
                amount=pym["amount"],
                date=parse_dt(pym["date"]),
                method=pym["method"],
                status=pym["status"],
                provider_id=pym["provider_id"],
                appointment_id=pym["appointment_id"],
                service_id=pym["service_id"],
                created_date=parse_dt(pym["created_date"])
            ) for pym in payments_data
        ]
        session.add_all(payments)
        
        await session.commit()
        print("Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
