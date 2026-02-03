import re
from repositories.raw_sql import RawSqlRepository


class QueryService:
    def __init__(self, repository: RawSqlRepository):
        self.repository = repository
        self.max_limit = 500

    def validate(self, sql: str) -> str:
        normalized = re.sub(r"\s+", " ", sql.strip())
        if not normalized:
            raise ValueError("SQL cannot be empty.")

        lowered = normalized.lower()
        if not lowered.startswith("select"):
            raise ValueError("Only SELECT statements are allowed.")

        if ";" in lowered:
            raise ValueError("Multiple statements are not allowed.")

        forbidden = r"\b(update|delete|insert|drop|alter|truncate|create|grant|revoke|commit|rollback)\b"
        if re.search(forbidden, lowered):
            raise ValueError("Write or DDL statements are not allowed.")

        return normalized

    def enforce_limit(self, sql: str, limit: int) -> str:
        safe_limit = max(1, min(limit, self.max_limit))
        if re.search(r"\blimit\s+\d+\b", sql, re.IGNORECASE):
            return sql
        return f"{sql} LIMIT {safe_limit}"

    async def run(self, sql: str, limit: int = 200) -> list[dict]:
        normalized = self.validate(sql)
        limited = self.enforce_limit(normalized, limit)
        return await self.repository.execute(limited)
