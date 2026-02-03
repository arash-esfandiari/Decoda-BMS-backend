import os  # Read environment variables like DATABASE_URL.
from dotenv import load_dotenv  # Load variables from a .env file.
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker  # Async SQLAlchemy engine/session.
from sqlalchemy.orm import DeclarativeBase  # Base class for ORM models.

load_dotenv()  # Pull values from .env into process environment.

DATABASE_URL = os.getenv("DATABASE_URL")  # Connection string for the database.
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Ensure we use the async driver.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=True)  # Create async engine (echo logs SQL).

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)  # Session factory.


class Base(DeclarativeBase):
    """Base class for all ORM models (collects metadata)."""
    pass


async def get_db():
    # Dependency that yields a DB session and closes it after the request.
    async with AsyncSessionLocal() as session:
        yield session
