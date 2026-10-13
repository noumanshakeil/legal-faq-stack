from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.llm import get_llm
from backend.models import FaqEntry
from backend.services.rag_core import score_chunk

DISCLAIMER = (
    "This is educational information, not legal advice. "
    "Consult a licensed attorney in your jurisdiction."
)

async def add_entry(
    session: AsyncSession,
    question: str,
    answer: str,
    jurisdiction: str = "US",
    category: str = "general",
) -> FaqEntry:
    row = FaqEntry(
        id=uuid.uuid4().hex[:10],
        question=question.strip(),
        answer=answer.strip(),
        jurisdiction=jurisdiction.upper()[:16],
        category=(category or "general").lower()[:64],
        disclaimer=DISCLAIMER,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row

async def list_entries(
    session: AsyncSession, jurisdiction: str | None = None, category: str | None = None
) -> list[FaqEntry]:
    stmt = select(FaqEntry)
    if jurisdiction:
        stmt = stmt.where(FaqEntry.jurisdiction == jurisdiction.upper())
    if category:
        stmt = stmt.where(FaqEntry.category == category.lower())
    return list((await session.execute(stmt.order_by(FaqEntry.created_at.desc()))).scalars())

async def ask(
    session: AsyncSession, question: str, jurisdiction: str | None = None
) -> dict:
    rows = await list_entries(session, jurisdiction)
    scored = []
    for row in rows:
        blob = f"{row.question}\n{row.answer}"
        s = score_chunk(question, blob)
        if s <= 0:
            continue
        scored.append((s, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:4]
    if not top:
        return {
            "answer": "No matching FAQ found. " + DISCLAIMER,
            "disclaimer": DISCLAIMER,
            "citations": [],
        }
    context = "\n\n".join(
        f"[{i}] ({r.jurisdiction}/{r.category}) Q: {r.question}\nA: {r.answer}"
        for i, (_, r) in enumerate(top, start=1)
    )
    llm = get_llm()
    answer = await llm.complete(
        f"Legal FAQ assistant. Always include a disclaimer. Never invent statutes.\n"
        f"USER: {question}\n\nFAQ:\n{context}",
        system="Conservative legal education assistant. Prefer quoting FAQ entries.",
    )
    if "not legal advice" not in answer.lower():
        answer = f"{answer}\n\n{DISCLAIMER}"
    return {
        "answer": answer,
        "disclaimer": DISCLAIMER,
        "citations": [
            {
                "index": i,
                "id": r.id,
                "jurisdiction": r.jurisdiction,
                "category": r.category,
                "question": r.question,
                "score": round(s, 3),
            }
            for i, (s, r) in enumerate(top, start=1)
        ],
    }
