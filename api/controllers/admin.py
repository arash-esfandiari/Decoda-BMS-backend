from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import json

from database import get_db
from services.import_service import ImportService

router = APIRouter(prefix="/admin", tags=["Admin"])

# fast and simple security for now due to time constraints
ADMIN_SECRET_KEY = "super-secret-admin-key-change-me"

async def verify_admin(x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid Admin Key")

@router.post("/import_data")
async def import_data(
    file: UploadFile = File(...),
    type: str = Header(..., description="Type of data: patients, providers, services, appointments, payments"),
    session: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_admin)
):
    """
    Import data from a JSON file. 
    'type' header determines the entity type.
    """
    # Disable endpoint temporarily
    raise HTTPException(status_code=403, detail="Data import functionality is currently disabled.")

    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON must be a list of objects")

    service = ImportService(session)

    try:
        if type == "patients":
            await service.upsert_patients(data)
        elif type == "providers":
            await service.upsert_providers(data)
        elif type == "services":
            await service.upsert_services(data)
        elif type == "appointments":
            await service.upsert_appointments(data)
        elif type == "appointment_services":
            await service.upsert_appointment_services(data)
        elif type == "payments":
            await service.upsert_payments(data)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown data type: {type}")
    except Exception as e:
        error_msg = str(e)
        if "IntegrityError" in error_msg or "ForeignKeyViolationError" in error_msg:
            raise HTTPException(
                status_code=400, 
                detail="Dependency missing: This record references an item (like an appointment or patient) that doesn't exist yet. Please ensure you import Patients -> Providers -> Services -> Appointments before Payments."
            )
        # In production we'd log this properly
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

    return {"status": "success", "count": len(data), "type": type}
