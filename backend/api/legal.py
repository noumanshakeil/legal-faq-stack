from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import legal as svc

class EntryIn(BaseModel):
    question: str = Field(min_length=5)
    answer: str = Field(min_length=10)
    jurisdiction: str = "US"
    category: str = "general"

class AskIn(BaseModel):
    question: str = Field(min_length=3)
    jurisdiction: str | None = None

router = APIRouter()

@router.get("/faq")
async def list_faq(
    jurisdiction: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    rows = await svc.list_entries(db, jurisdiction, category)
    return {
        "entries": [
            {
                "id": r.id,
                "jurisdiction": r.jurisdiction,
                "category": r.category,
                "question": r.question,
            }
            for r in rows
        ]
    }

@router.post("/faq")
async def create(payload: EntryIn, db: AsyncSession = Depends(get_db)):
    row = await svc.add_entry(
        db, payload.question, payload.answer, payload.jurisdiction, payload.category
    )
    return {"id": row.id}

@router.post("/ask")
async def ask(payload: AskIn, db: AsyncSession = Depends(get_db)):
    return await svc.ask(db, payload.question, payload.jurisdiction)
