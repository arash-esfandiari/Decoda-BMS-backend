from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from repositories.appointment import AppointmentRepository
from services.appointment import AppointmentService
from schemas import Appointment as AppointmentSchema, PaginatedAppointmentsResponse

router = APIRouter(prefix="/appointments", tags=["Appointments"])

def get_appointment_repository(session: AsyncSession = Depends(get_db)) -> AppointmentRepository:
    return AppointmentRepository(session)

def get_appointment_service(repository: AppointmentRepository = Depends(get_appointment_repository)) -> AppointmentService:
    return AppointmentService(repository)

@router.get("/analytics")
async def read_appointment_analytics(
    service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointment analytics including status breakdown and revenue"""
    return await service.get_analytics()

@router.get("/", response_model=PaginatedAppointmentsResponse)
async def read_appointments(
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    sort_by: str = "start_time",
    sort_order: str = "desc",
    date_filter: str = None,
    service: AppointmentService = Depends(get_appointment_service)
):
    return await service.get_appointments(
        skip=skip, 
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        date_filter=date_filter
    )

@router.get("/{appointment_id}", response_model=AppointmentSchema)
async def read_appointment(
    appointment_id: str, 
    service: AppointmentService = Depends(get_appointment_service)
):
    appointment = await service.get_appointment(appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment
