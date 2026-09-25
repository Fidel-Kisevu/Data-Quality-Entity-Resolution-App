from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from services.ai_analyst import ask

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
def ai_query(payload: QueryRequest, db: Session = Depends(get_db)):
    """
    Ask the AI Analyst a question. Answers are grounded ONLY on trusted data.
    """
    return ask(db, payload.question)