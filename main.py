from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api.controllers import patients, analytics, appointments, services, providers, dashboard, admin, chat

from sqlalchemy import select
from database import AsyncSessionLocal
from models import Patient
from scripts.seed import seed_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        # In production, we might use alembic instead of create_all
        await conn.run_sync(Base.metadata.create_all)
    
    # Check if DB is empty and seed if necessary
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Patient).limit(1))
        patient = result.scalar_one_or_none()
        if not patient:
            print("Database appears empty. seeding data...")
            await seed_data(reset=False)
        else:
            print("Database already contains data. Skipping seed.")

    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(title="Beauty Med Spa API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(analytics.router)
app.include_router(appointments.router)
app.include_router(services.router)
app.include_router(providers.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message": "Beauty Med Spa API is running"}
