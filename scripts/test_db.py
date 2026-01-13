
import asyncio
import sys
import os

# Add parent directory to path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from sqlalchemy import text

async def main():
    try:
        print("Testing database connection...")
        async for session in get_db():
            result = await session.execute(text("SELECT 1"))
            print(f"Connection successful! Result: {result.scalar()}")
            break
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
