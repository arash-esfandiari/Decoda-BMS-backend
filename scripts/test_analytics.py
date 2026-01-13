
import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from repositories.patient import PatientRepository

# JSON encoder for datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

async def main():
    async for session in get_db():
        repo = PatientRepository(session)
        print("--- Fetching Analytics ---")
        try:
            data = await repo.get_analytics()
            
            print("\n[Top Patients]")
            for p in data.get('top_patients', []):
                print(f"- {p['name']}: ${p['total_spent']} ({p['visit_count']} visits)")
                
            print("\n[Retention Opportunities]")
            for p in data.get('retention_opportunities', []):
                print(f"- {p['name']}: Last visit {p['days_since_last_visit']} days ago")
                
            # print(json.dumps(data, cls=DateTimeEncoder, indent=2))
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
