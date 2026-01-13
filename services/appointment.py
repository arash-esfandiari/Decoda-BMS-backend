from typing import List, Optional
from models import Appointment
from repositories.appointment import AppointmentRepository

class AppointmentService:
    def __init__(self, repository: AppointmentRepository):
        self.repository = repository

    async def get_appointments(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        sort_by: str = "start_time",
        sort_order: str = "desc",
        date_filter: str = None
    ) -> dict:
        appointments, total = await self.repository.get_all_with_patient(
            skip=skip, 
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            date_filter=date_filter
        )
        
        # Calculate metrics for each appointment
        for appointment in appointments:
            if appointment.services:
                # Service count
                appointment.service_count = len(appointment.services)
                
                # Total cost (sum of all service prices)
                appointment.total_cost = sum(
                    svc.service.price for svc in appointment.services if svc.service
                )
                
                # Duration (earliest start to latest end) and start time
                if appointment.services:
                    starts = [svc.start for svc in appointment.services if svc.start]
                    ends = [svc.end for svc in appointment.services if svc.end]
                    if starts and ends:
                        earliest_start = min(starts)
                        latest_end = max(ends)
                        appointment.duration_minutes = int((latest_end - earliest_start).total_seconds() / 60)
                        appointment.start_time = earliest_start  # Add start time
                    else:
                        appointment.start_time = None
                
                # Payment status for each service
                for service in appointment.services:
                    # Find payment for this specific service
                    payment = next(
                        (p for p in (appointment.payments or [])
                         if p.service_id == service.service_id),
                        None
                    )
                    if payment:
                        service.payment_status = payment.status  # "pending", "paid", or "failed"
                    else:
                        service.payment_status = "unpaid"
            else:
                appointment.service_count = 0
                appointment.total_cost = 0
                appointment.duration_minutes = 0
                appointment.start_time = None
        
        return {"data": appointments, "total": total}

    async def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        appointment = await self.repository.get_by_id_with_details(appointment_id)
        
        if appointment and appointment.services:
            # Calculate metrics
            appointment.service_count = len(appointment.services)
            appointment.total_cost = sum(
                svc.service.price for svc in appointment.services if svc.service
            )
            
            if appointment.services:
                starts = [svc.start for svc in appointment.services]
                ends = [svc.end for svc in appointment.services]
                if starts and ends:
                    earliest_start = min(starts)
                    latest_end = max(ends)
                    appointment.duration_minutes = int((latest_end - earliest_start).total_seconds() / 60)
            
            # Payment status for each service
            for service in appointment.services:
                # Find payment for this specific service
                payment = next(
                    (p for p in (appointment.payments or [])
                     if p.service_id == service.service_id),
                    None
                )
                if payment:
                    service.payment_status = payment.status  # "pending", "paid", or "failed"
                else:
                    service.payment_status = "unpaid"
        
        return appointment
    
    async def get_analytics(self) -> dict:
        """Get appointment analytics"""
        return await self.repository.get_analytics()
