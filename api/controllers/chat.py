from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from repositories.raw_sql import RawSqlRepository
from services.query import QueryService
from services.chat import ChatService
from schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_query_service(session: AsyncSession = Depends(get_db)) -> QueryService:
    return QueryService(RawSqlRepository(session))


def get_chat_service(
    query_service: QueryService = Depends(get_query_service),
) -> ChatService:
    return ChatService(query_service)


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    try:
        result = await service.ask(payload.question, limit=payload.limit or 200)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result
