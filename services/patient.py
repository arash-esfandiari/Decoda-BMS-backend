from typing import List, Optional
from models import Patient
from repositories.patient import PatientRepository

class PatientService:
    def __init__(self, repository: PatientRepository):
        self.repository = repository

    async def get_patients(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: str = None,
        sort_by: str = "first_name",
        sort_order: str = "asc"
    ) -> dict:
        patients, total = await self.repository.get_all(
            skip=skip, 
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return {"data": patients, "total": total}

    async def get_patient(self, patient_id: str) -> Optional[Patient]:
        patient = await self.repository.get_by_id_with_appointments(patient_id)
        
        # Calculate metrics for each appointment
        if patient and patient.appointments:
            for appointment in patient.appointments:
                # Load services count and calculate total cost
                if hasattr(appointment, 'services') and appointment.services:
                    appointment.service_count = len(appointment.services)
                    appointment.total_cost = sum(
                        svc.service.price for svc in appointment.services if svc.service
                    )
                else:
                    appointment.service_count = 0
                    appointment.total_cost = 0
        
        return patient

    async def get_analytics(self) -> dict:
        return await self.repository.get_analytics()
