
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from sqlalchemy import text

async def main():
    target_id = 'apt_580bc822e414e194'
    print(f"Checking for appointment ID: {target_id}")
    async for session in get_db():
        result = await session.execute(text("SELECT id FROM appointments WHERE id = :id"), {"id": target_id})
        row = result.fetchone()
        if row:
            print(f"FOUND: Appointment {target_id} exists in DB.")
        else:
            print(f"MISSING: Appointment {target_id} NOT found in DB.")
            print("Please import appointments before importing payments.")

if __name__ == "__main__":
    asyncio.run(main())
