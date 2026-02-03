"""Shared async repository utilities for SQLAlchemy models."""

from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Base

T = TypeVar("T", bound=Base)  # Generic model type constrained to SQLAlchemy Base.

class BaseRepository(Generic[T]):
    """Generic async repository with common read operations for a model."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        """Store the async DB session and the model class this repository serves."""
        # Session used for all database interactions in this repository instance.
        self.session = session
        # SQLAlchemy model class (not instance) for query construction.
        self.model = model

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Return a paginated list of all model rows."""
        # Build a SELECT statement with pagination.
        stmt = select(self.model).offset(skip).limit(limit)
        # Execute asynchronously and retrieve ORM model instances.
        result = await self.session.execute(stmt)
        # `scalars()` yields model instances; `all()` collects them.
        return list(result.scalars().all())

    async def get_by_id(self, id: Any) -> Optional[T]:
        """Fetch a single model instance by primary key, if it exists."""
        # `session.get` is optimized for primary-key lookup.
        return await self.session.get(self.model, id)
