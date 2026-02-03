import os
import re
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool

from services.query import QueryService


class ChatService:
    def __init__(self, query_service: QueryService):
        self.query_service = query_service
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-5.2")
        self.model = ChatOpenAI(model=self.model_name, temperature=0)
        self._current_limit = 200
        self._last_sql = ""
        self._last_rows: list[dict[str, Any]] = []
        self._table_names: list[str] | None = None
        self._dialect = self._detect_dialect()
        self.agent = self._build_agent()

    def _detect_dialect(self) -> str:
        url = os.getenv("DATABASE_URL", "").lower()
        if "sqlite" in url:
            return "sqlite"
        if "mysql" in url:
            return "mysql"
        return "postgresql"

    def _system_prompt(self) -> str:
        return (
            "You are an agent designed to interact with a SQL database. "
            "Given an input question, create a syntactically correct "
            f"{self._dialect} SELECT query to run, then look at the results and "
            "return a concise answer. Unless the user specifies a specific number "
            "of examples they wish to obtain, always limit your query to at most "
            f"{self._current_limit} results. "
            "Never query for all columns from a specific table, only ask for "
            "the relevant columns given the question. "
            "You MUST double check your query before executing it. If you get an "
            "error while executing a query, rewrite the query and try again. "
            "DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) "
            "to the database. Use only SELECT statements. No semicolons. "
            "To start you should ALWAYS look at the tables in the database to see "
            "what you can query. Do NOT skip this step. Then you should query the "
            "schema of the most relevant tables. "
            "Domain notes: amount and price are stored in cents."
        )

    def _build_agent(self):
        tools = [
            self._list_tables_tool(),
            self._schema_tool(),
            self._query_checker_tool(),
            self._query_tool(),
        ]
        return create_agent(
            self.model,
            tools,
            system_prompt=self._system_prompt(),
        )

    async def _fetch_table_names(self) -> list[str]:
        if self._dialect == "sqlite":
            query = (
                "SELECT name AS table_name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
        else:
            query = (
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "ORDER BY table_name"
            )
        rows = await self.query_service.repository.execute(query)
        return [row["table_name"] for row in rows]

    def _normalize_table_names(self, raw: str) -> list[str]:
        if not raw:
            return []
        names = [name.strip().strip('"') for name in raw.split(",") if name.strip()]
        allowed = set(self._table_names or [])
        if not allowed:
            return names
        return [name for name in names if name in allowed]

    def _list_tables_tool(self):
        @tool("sql_db_list_tables")
        async def sql_db_list_tables(_: str = "") -> str:
            """Return a comma-separated list of available tables."""
            tables = await self._fetch_table_names()
            self._table_names = tables
            return ", ".join(tables)

        return sql_db_list_tables

    def _schema_tool(self):
        @tool("sql_db_schema")
        async def sql_db_schema(table_names: str) -> str:
            """Return column info for the requested tables."""
            if not self._table_names:
                self._table_names = await self._fetch_table_names()
            names = self._normalize_table_names(table_names)
            if not names:
                return "No matching tables found. Call sql_db_list_tables first."

            sections: list[str] = []
            for name in names:
                if self._dialect == "sqlite":
                    columns = await self.query_service.repository.execute(
                        f"PRAGMA table_info({name})"
                    )
                    column_lines = [
                        f"{col['name']} {col['type']}"
                        for col in columns
                    ]
                else:
                    columns = await self.query_service.repository.execute(
                        "SELECT column_name, data_type, is_nullable "
                        "FROM information_schema.columns "
                        "WHERE table_schema = 'public' AND table_name = :table "
                        "ORDER BY ordinal_position",
                        {"table": name},
                    )
                    column_lines = [
                        f"{col['column_name']} {col['data_type']} "
                        f"{'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}"
                        for col in columns
                    ]

                sections.append(
                    "\n".join(
                        [
                            f"Table: {name}",
                            "Columns:",
                            *[f"- {line}" for line in column_lines],
                        ]
                    )
                )

            return "\n\n".join(sections)

        return sql_db_schema

    def _query_checker_tool(self):
        @tool("sql_db_query_checker")
        async def sql_db_query_checker(query: str) -> str:
            """Clean SQL input and strip code fences."""
            cleaned = query.strip()
            cleaned = re.sub(r"^```sql", "", cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
            return cleaned

        return sql_db_query_checker

    def _query_tool(self):
        @tool("sql_db_query")
        async def sql_db_query(query: str) -> str:
            """Validate, limit, and execute a SQL query."""
            try:
                normalized = self.query_service.validate(query)
                limited = self.query_service.enforce_limit(
                    normalized,
                    self._current_limit,
                )
            except ValueError as exc:
                return f"Error: {exc}"

            try:
                rows = await self.query_service.run(limited, limit=self._current_limit)
            except Exception as exc:
                return f"Error: {type(exc).__name__}: {exc}"

            self._last_sql = limited
            self._last_rows = rows
            return str(rows)

        return sql_db_query

    def _extract_answer(self, result: Any) -> str:
        if isinstance(result, dict):
            if "output" in result and isinstance(result["output"], str):
                return result["output"].strip()
            messages = result.get("messages")
            if isinstance(messages, list) and messages:
                last = messages[-1]
                content = getattr(last, "content", None)
                if isinstance(content, str):
                    return content.strip()
        content = getattr(result, "content", None)
        if isinstance(content, str):
            return content.strip()
        return str(result).strip()

    async def ask(self, question: str, limit: int = 200) -> dict[str, Any]:
        self._current_limit = limit or 200
        self._last_sql = ""
        self._last_rows = []

        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        answer = self._extract_answer(result)
        return {"answer": answer, "sql": self._last_sql, "rows": self._last_rows}
