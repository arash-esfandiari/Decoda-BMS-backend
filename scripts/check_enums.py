
import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

async def main():
    async for session in get_db():
        print("--- Checking Enum Values ---")
        
        # Check Patients
        print("\n[Patients]")
        result = await session.execute(text("SELECT DISTINCT gender FROM patients"))
        print(f"Genders: {[r[0] for r in result]}")
        
        result = await session.execute(text("SELECT DISTINCT source FROM patients"))
        print(f"Sources: {[r[0] for r in result]}")

        # Check Appointments
        print("\n[Appointments]")
        result = await session.execute(text("SELECT DISTINCT status FROM appointments"))
        print(f"Statuses: {[r[0] for r in result]}")
        
        # Check Payments
        print("\n[Payments]")
        result = await session.execute(text("SELECT DISTINCT p.status FROM payments p"))
        print(f"Statuses: {[r[0] for r in result]}")
        
        result = await session.execute(text("SELECT DISTINCT method FROM payments"))
        print(f"Methods: {[r[0] for r in result]}")

if __name__ == "__main__":
    asyncio.run(main())
