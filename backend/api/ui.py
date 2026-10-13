from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import legal as svc

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, jurisdiction: str = "US", db: AsyncSession = Depends(get_db)):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Legal FAQ Stack",
            "jurisdiction": jurisdiction,
            "entries": await svc.list_entries(db, jurisdiction),
            "answer": None,
            "citations": [],
            "disclaimer": svc.DISCLAIMER,
        },
    )

@router.post("/ui/faq")
async def ui_add(
    question: str = Form(...),
    answer: str = Form(...),
    jurisdiction: str = Form("US"),
    category: str = Form("general"),
    db: AsyncSession = Depends(get_db),
):
    await svc.add_entry(db, question, answer, jurisdiction, category)
    return RedirectResponse(f"/?jurisdiction={jurisdiction}", status_code=303)

@router.post("/ui/ask", response_class=HTMLResponse)
async def ui_ask(
    request: Request,
    question: str = Form(...),
    jurisdiction: str = Form("US"),
    db: AsyncSession = Depends(get_db),
):
    result = await svc.ask(db, question, jurisdiction)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Legal FAQ Stack",
            "jurisdiction": jurisdiction,
            "entries": await svc.list_entries(db, jurisdiction),
            "answer": result["answer"],
            "citations": result["citations"],
            "disclaimer": result["disclaimer"],
            "question": question,
        },
    )
