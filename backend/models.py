from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base

def utcnow(): return datetime.utcnow()

class FaqEntry(Base):
    __tablename__ = "faq_entries"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    jurisdiction: Mapped[str] = mapped_column(String(16), index=True, default="US")
    category: Mapped[str] = mapped_column(String(64), index=True, default="general")
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    disclaimer: Mapped[str] = mapped_column(Text, default="Not legal advice.")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
