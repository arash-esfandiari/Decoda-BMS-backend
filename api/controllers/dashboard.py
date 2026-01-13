from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

"""
Controller for the Dashboard.
Aggregates high-level data for the main dashboard view, including:
- Appointments today
- Revenue forecast
- New patients
- Pending actions
- Timeline of upcoming appointments
"""

from database import get_db
from models import Appointment, AppointmentService, Patient, Service
from schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(session: AsyncSession = Depends(get_db)):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # ---------------------------------------------------------
    # 1. Appointments Today & Revenue Forecast
    # ---------------------------------------------------------
    # Find appointments with any service starting today
    stmt_today = (
        select(Appointment)
        .join(AppointmentService)
        .join(Service)
        .options(
            selectinload(Appointment.services).selectinload(AppointmentService.service),
            selectinload(Appointment.services).selectinload(AppointmentService.provider),
            selectinload(Appointment.patient),
            selectinload(Appointment.payments)
        )
        .where(
            and_(
                AppointmentService.start >= today_start,
                AppointmentService.start < today_end
            )
        )
        .distinct()
    )
    
    result_today = await session.execute(stmt_today)
    appointments_today_list = result_today.scalars().all()
    
    appointments_today_count = len(appointments_today_list)
    
    revenue_forecast = 0
    for apt in appointments_today_list:
        # Sum price of all services for these appointments
        # Note: simplistic logic, summing all services of the appointment even if some are not today?
        # Ideally we only sum services that are today.
        for svc in apt.services:
             # Check if this specific service is today
             if svc.start and svc.start >= today_start and svc.start < today_end:
                 if svc.service.price:
                     revenue_forecast += svc.service.price

    # ---------------------------------------------------------
    # 2. New Patients Today
    # ---------------------------------------------------------
    stmt_patients = (
        select(func.count(Patient.id))
        .where(
            and_(
                Patient.created_date >= today_start,
                Patient.created_date < today_end
            )
        )
    )
    result_patients = await session.execute(stmt_patients)
    new_patients_today = result_patients.scalar() or 0

    # ---------------------------------------------------------
    # 3. Pending Actions (Appointments with status 'pending')
    # ---------------------------------------------------------
    stmt_pending = (
        select(func.count(Appointment.id))
        .where(Appointment.status == "pending")
    )
    result_pending = await session.execute(stmt_pending)
    pending_actions = result_pending.scalar() or 0

    # ---------------------------------------------------------
    # 4. Upcoming/Today's Timeline (Reuse appointments_today_list)
    # ---------------------------------------------------------
    # Sort by start time of the service that falls within today
    def get_start_time(apt):
        starts = [s.start for s in apt.services if s.start and s.start >= today_start and s.start < today_end]
        return min(starts) if starts else datetime.max

    upcoming_sorted = sorted(appointments_today_list, key=get_start_time)
    
    # Populate computed fields for the schema
    for apt in upcoming_sorted:
        apt.service_count = len(apt.services)
        apt.total_cost = sum(s.service.price for s in apt.services if s.service)
        
        # Calculate duration
        duration = 0
        starts = []
        for s in apt.services:
            if s.start and s.end:
                duration += (s.end - s.start).total_seconds() / 60
                starts.append(s.start)
        apt.duration_minutes = int(duration)
        apt.start_time = min(starts) if starts else None

    return {
        "appointments_today": appointments_today_count,
        "revenue_forecast_today": revenue_forecast,
        "new_patients_today": new_patients_today,
        "pending_actions": pending_actions,
        "upcoming_appointments": upcoming_sorted
    }
