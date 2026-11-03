"""Demo data: one Thrissur shop, four karigars and five jobs in different
states, created through the real ledger functions so every message and audit
row is genuine. Names, phones and the GSTIN are placeholders."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import JobCard, Karigar, Shop
from .services import ledger
from .services.validator import DraftFields
from .timeutil import today


def seed(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Shop)):
        return
    db.add(Shop(id=1, name="Sree Jewellers (demo)", city="Thrissur", state="Kerala", owner_name="Shop owner",
                language="en", gstin="32AAAAA0000A1Z5", gold_rate_paise_per_g_24k=0))
    karigars = [
        Karigar(name="Ramesh Das", aliases=["രമേശ്", "रमेश", "রমেশ"], phone="+91 90000 00001", language="bn",
                default_wastage_bp=400, making_rate_paise_per_g=30000),
        Karigar(name="Suresh Menon", aliases=["സുരേഷ്", "सुरेश", "সুরেশ"], phone="+91 90000 00002", language="ml",
                default_wastage_bp=350, making_rate_paise_per_g=32000),
        Karigar(name="Anil Yadav", aliases=["അനിൽ", "अनिल", "অনিল"], phone="+91 90000 00003", language="hi",
                default_wastage_bp=500, making_rate_paise_per_g=28000),
        Karigar(name="Biju Thomas", aliases=["ബിജു", "बिजु", "বিজু"], phone="+91 90000 00004", language="ml",
                default_wastage_bp=300, making_rate_paise_per_g=30000),
    ]
    db.add_all(karigars)
    db.flush()
    ramesh, suresh, anil, biju = karigars
    d = today()

    def draft(k, mg, karat, pieces, item, due, wastage=None, text=""):
        job = ledger.create_draft(
            db, DraftFields(karigar_id=k.id, weight_mg=mg, purity_karat=karat, pieces=pieces, item=item,
                            due_date=due, wastage_bp=wastage),
            source="seed", source_text=text,
        )
        return job

    # JC-1001: both confirmed, due in 3 days.
    j1 = draft(ramesh, 50_000, 22, 10, "bangle", d + timedelta(days=3), text="Gave Ramesh 50 grams 22K for 10 bangles")
    ledger.confirm_by_jeweller(db, j1)
    ledger.confirm_by_karigar(db, j1, "button")
    # JC-1002: waiting for the karigar's tap.
    j2 = draft(suresh, 38_200, 22, 2, "chain", d + timedelta(days=6))
    ledger.confirm_by_jeweller(db, j2)
    # JC-1003: confirmed, two days overdue (due date set in the past after issue).
    j3 = draft(anil, 24_500, 18, 6, "ring", d + timedelta(days=5))
    ledger.confirm_by_jeweller(db, j3)
    ledger.confirm_by_karigar(db, j3, "button")
    j3.due_date = d - timedelta(days=2)
    # JC-1004: returned within wastage and paid.
    j4 = draft(biju, 31_800, 22, 4, "bangle", d + timedelta(days=4), wastage=300)
    ledger.confirm_by_jeweller(db, j4)
    ledger.confirm_by_karigar(db, j4, "in_person")
    ledger.record_return(db, j4, returned_gross_mg=30_700, stone_mg=0, scrap_mg=146)
    ledger.record_payment(db, j4)
    # JC-1005: returned short, flagged.
    j5 = draft(ramesh, 20_000, 22, 1, "necklace", d + timedelta(days=2), wastage=400)
    ledger.confirm_by_jeweller(db, j5)
    ledger.confirm_by_karigar(db, j5, "button")
    ledger.record_return(db, j5, returned_gross_mg=18_900, stone_mg=300, scrap_mg=200)
    db.commit()


def reset(db: Session) -> None:
    from .db import Base, engine

    db.close()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    from .db import SessionLocal

    fresh = SessionLocal()
    try:
        seed(fresh)
    finally:
        fresh.close()


def job_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(JobCard)) or 0
