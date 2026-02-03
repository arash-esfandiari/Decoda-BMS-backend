from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class RawSqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, sql: str, params: dict | None = None) -> list[dict]:
        result = await self.session.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings().all()]
