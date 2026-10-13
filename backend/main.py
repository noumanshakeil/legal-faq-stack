"""Legal FAQ Stack — FastAPI backend + Jinja UI."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .llm import complete

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "data" / "store.json"
FIELDS = ['question', 'answer', 'jurisdiction']

app = FastAPI(title="Legal FAQ Stack", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT / "templates"))


def load_store() -> dict:
    if not DATA.exists():
        DATA.parent.mkdir(parents=True, exist_ok=True)
        payload = {"faqs": [
  {
    "id": "f1",
    "question": "Data residency?",
    "answer": "EU region available",
    "jurisdiction": "EU"
  }
]}
        DATA.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json.loads(DATA.read_text(encoding="utf-8"))


def save_store(store: dict) -> None:
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(store, indent=2), encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "legal-faq-stack", "llm_mode": settings.llm_mode}


@app.get("/api/faqs")
def list_items() -> dict:
    store = load_store()
    return {"faqs": store.get("faqs", [])}


@app.post("/api/faqs")
def create_item(payload: dict) -> dict:
    store = load_store()
    item = {"id": uuid.uuid4().hex[:8]}
    for key in FIELDS:
        item[key] = payload.get(key)
    store.setdefault("faqs", []).insert(0, item)
    save_store(store)
    return item


@app.post("/api/answer_faq")
def run_action(payload: dict) -> dict:
    """Answer legal FAQ with disclaimer."""
    prompt = (
        "You are the AI engine for Legal FAQ Stack.\n"
        "Task: Answer legal FAQ with disclaimer.\n"
        f"Input JSON: {json.dumps(payload)[:4000]}"
    )
    text = complete(prompt)
    return {"ok": True, "action": "answer_faq", "result": text, "mode": settings.llm_mode}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, last_result: str | None = None) -> HTMLResponse:
    store = load_store()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Legal FAQ Stack",
            "description": "Legal FAQ stack with jurisdiction tags, disclaimer banners, and editor tools.",
            "resource": "faqs",
            "action": "answer_faq",
            "action_desc": "Answer legal FAQ with disclaimer",
            "items": store.get("faqs", []),
            "llm_mode": settings.llm_mode,
            "last_result": last_result,
        },
    )


@app.post("/ui/create", response_class=HTMLResponse)
async def ui_create(request: Request) -> HTMLResponse:
    form = await request.form()
    data = {k: form.get(k) for k in FIELDS}
    create_item(data)
    return home(request)


@app.post("/ui/action", response_class=HTMLResponse)
async def ui_action(request: Request, prompt: str = Form("demo")) -> HTMLResponse:
    result = run_action({"prompt": prompt})
    store = load_store()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Legal FAQ Stack",
            "description": "Legal FAQ stack with jurisdiction tags, disclaimer banners, and editor tools.",
            "resource": "faqs",
            "action": "answer_faq",
            "action_desc": "Answer legal FAQ with disclaimer",
            "items": store.get("faqs", []),
            "llm_mode": settings.llm_mode,
            "last_result": result.get("result"),
        },
    )
