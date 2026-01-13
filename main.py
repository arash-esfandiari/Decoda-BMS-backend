from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api.controllers import patients, analytics, appointments, services, providers, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        # In production, we might use alembic instead of create_all
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(title="Beauty Med Spa API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

@app.get("/")
async def root():
    return {"message": "Beauty Med Spa API is running"}
