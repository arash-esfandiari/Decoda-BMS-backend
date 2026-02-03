import asyncio
import os
import re
from typing import Any

from openai import OpenAI

from services.query import QueryService


class ChatService:
    def __init__(self, query_service: QueryService):
        self.query_service = query_service
        self.client = OpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.2")

    def _schema_context(self) -> str:
        return (
            "Database schema:\n"
            "patients(id, first_name, last_name, date_of_birth, gender, address, phone, email, source, created_date)\n"
            "providers(id, first_name, last_name, email, phone, created_date)\n"
            "services(id, name, description, price, duration, created_date)\n"
            "appointments(id, patient_id, status, created_date)\n"
            "appointment_services(id, appointment_id, service_id, provider_id, start, end)\n"
            "payments(id, patient_id, amount, date, method, status, provider_id, appointment_id, service_id, created_date)\n"
            "Notes: amount and price are in cents. Use only SELECT statements. No semicolons."
        )

    def _extract_sql(self, text: str) -> str:
        sql = text.strip()
        sql = re.sub(r"^```sql", "", sql, flags=re.IGNORECASE).strip()
        sql = re.sub(r"```$", "", sql).strip()
        return sql

    async def generate_sql(self, question: str) -> str:
        def _call() -> str:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a data analyst. Convert the user question into a single "
                            "PostgreSQL SELECT statement. Return only SQL."
                        ),
                    },
                    {"role": "system", "content": self._schema_context()},
                    {"role": "user", "content": question},
                ],
            )
            return response.output_text

        raw = await asyncio.to_thread(_call)
        return self._extract_sql(raw)

    async def ask(self, question: str, limit: int = 200) -> dict[str, Any]:
        sql = await self.generate_sql(question)
        rows = await self.query_service.run(sql, limit=limit)
        return {"answer": "", "sql": sql, "rows": rows}
