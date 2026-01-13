from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from repositories.patient import PatientRepository
from services.patient import PatientService
from schemas import Patient as PatientSchema, PaginatedPatientsResponse
from api.analytics_schema import PatientAnalyticsResponse

router = APIRouter(prefix="/patients", tags=["Patients"])

def get_patient_repository(session: AsyncSession = Depends(get_db)) -> PatientRepository:
    return PatientRepository(session)

def get_patient_service(repository: PatientRepository = Depends(get_patient_repository)) -> PatientService:
    return PatientService(repository)

@router.get("/", response_model=PaginatedPatientsResponse)
async def read_patients(
    skip: int = 0, 
    limit: int = 100, 
    search: str = None,
    sort_by: str = "first_name",
    sort_order: str = "asc",
    service: PatientService = Depends(get_patient_service)
):
    return await service.get_patients(
        skip=skip, 
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/analytics", response_model=PatientAnalyticsResponse)
async def get_analytics(
    service: PatientService = Depends(get_patient_service)
):
    return await service.get_analytics()

@router.get("/{patient_id}", response_model=PatientSchema)
async def read_patient(
    patient_id: str, 
    service: PatientService = Depends(get_patient_service)
):
    patient = await service.get_patient(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
