"""Database tables.

All gold weights are stored as whole milligrams and all money as whole paise,
so every calculation is exact integer arithmetic. Wastage is stored in basis
points (1/100 of a percent): 4.00 % == 400.
"""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .timeutil import now


class JobStatus(str, enum.Enum):
    DRAFT = "draft"  # created from a voice/text note, waiting for the jeweller's tap
    AWAITING_KARIGAR = "awaiting_karigar"  # jeweller confirmed, karigar hasn't yet
    CONFIRMED = "confirmed"  # both sides confirmed, work in progress
    DISPUTED = "disputed"  # karigar pressed "Problem" on the receipt
    FLAGGED = "flagged"  # return short by more than the agreed wastage
    RECONCILED = "reconciled"  # return checked and within the agreed norm
    PAID = "paid"  # making charge settled; job closed
    CANCELLED = "cancelled"


OPEN_STATUSES = {JobStatus.AWAITING_KARIGAR, JobStatus.CONFIRMED, JobStatus.DISPUTED}


class Shop(Base):
    __tablename__ = "shop"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(80), default="Thrissur")
    owner_name: Mapped[str] = mapped_column(String(120), default="")
    owner_phone: Mapped[str] = mapped_column(String(20), default="")
    language: Mapped[str] = mapped_column(String(5), default="en")
    gstin: Mapped[str] = mapped_column(String(20), default="")
    state: Mapped[str] = mapped_column(String(40), default="Kerala")
    # Optional rate used to print a value on job-work challans (paise per gram of 24K).
    gold_rate_paise_per_g_24k: Mapped[int] = mapped_column(Integer, default=0)
    # When the jeweller taps "Edit" on a draft, the next message corrects that draft.
    pending_edit_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # When a note named an unknown or ambiguous karigar, we keep it here until answered.
    pending_clarification: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    next_job_number: Mapped[int] = mapped_column(Integer, default=1001)
    next_challan_number: Mapped[int] = mapped_column(Integer, default=1)


class Karigar(Base):
    __tablename__ = "karigars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    # Other spellings used to match voice notes, e.g. ["രമേശ്", "रमेश", "রমেশ"].
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    phone: Mapped[str] = mapped_column(String(20), default="")
    language: Mapped[str] = mapped_column(String(5), default="ml")  # ml | hi | bn | en
    gstin: Mapped[str] = mapped_column(String(20), default="")
    default_wastage_bp: Mapped[int] = mapped_column(Integer, default=400)
    making_rate_paise_per_g: Mapped[int] = mapped_column(Integer, default=30000)
    active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    jobs: Mapped[list["JobCard"]] = relationship(back_populates="karigar")


class JobCard(Base):
    __tablename__ = "job_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    karigar_id: Mapped[int] = mapped_column(ForeignKey("karigars.id"))
    status: Mapped[str] = mapped_column(String(24), default=JobStatus.DRAFT.value, index=True)

    item: Mapped[str] = mapped_column(String(40), default="ornament")
    pieces: Mapped[int] = mapped_column(Integer, default=1)
    issued_mg: Mapped[int] = mapped_column(Integer)
    purity_karat: Mapped[int] = mapped_column(Integer, default=22)
    agreed_wastage_bp: Mapped[int] = mapped_column(Integer, default=400)
    making_rate_paise_per_g: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    source: Mapped[str] = mapped_column(String(16), default="form")  # voice | text | form | seed
    source_text: Mapped[str] = mapped_column(Text, default="")
    warnings: Mapped[list] = mapped_column(JSON, default=list)

    challan_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    jeweller_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    karigar_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    karigar_confirm_method: Mapped[str] = mapped_column(String(20), default="")  # button | in_person | challan_photo
    dispute_reason: Mapped[str] = mapped_column(Text, default="")

    # Return-day figures (filled when the jewellery comes back).
    returned_gross_mg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stone_mg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scrap_mg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    balance_mg: Mapped[int | None] = mapped_column(Integer, nullable=True)  # + = karigar owes gold
    making_charge_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution: Mapped[str] = mapped_column(Text, default="")

    paid_paise: Mapped[int] = mapped_column(Integer, default=0)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    karigar: Mapped[Karigar] = relationship(back_populates="jobs")


class Message(Base):
    """Every WhatsApp-style message, in or out. Drives the simulator and the log."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    party: Mapped[str] = mapped_column(String(24), index=True)  # "jeweller" or "karigar:<id>"
    direction: Mapped[str] = mapped_column(String(3))  # in | out
    kind: Mapped[str] = mapped_column(String(12), default="text")  # text | voice | buttons | button_reply
    body: Mapped[str] = mapped_column(Text, default="")
    buttons: Mapped[list] = mapped_column(JSON, default=list)  # [{"id","title"}]
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_cards.id"))
    kind: Mapped[str] = mapped_column(String(24))  # due_soon | overdue | confirm_nudge | confirm_escalate
    for_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuditLog(Base):
    """Append-only, hash-chained history. Editing any row breaks the chain."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(40))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    prev_hash: Mapped[str] = mapped_column(String(64), default="")
    hash: Mapped[str] = mapped_column(String(64), default="")
