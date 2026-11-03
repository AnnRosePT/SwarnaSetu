"""SwarnaSetu API and web app.

Run:  uvicorn app.main:app --reload   (from the backend/ folder)
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router, webhook
from .config import settings
from .db import SessionLocal, init_db
from .services import reminders
from .timeutil import today

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("swarnasetu")


async def _reminder_loop() -> None:
    while True:
        await asyncio.sleep(settings.reminder_interval_s)
        db = SessionLocal()
        try:
            sent = reminders.run(db, today())
            db.commit()
            if sent:
                log.info("Reminders sent: %s", sent)
        except Exception:  # never let the loop die
            db.rollback()
            log.exception("Reminder run failed")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.seed_demo:
        from .seed import seed

        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()
    task = asyncio.create_task(_reminder_loop()) if settings.reminder_interval_s > 0 else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="SwarnaSetu", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(router)
app.include_router(webhook)

dist = settings.frontend_dist
if (dist / "index.html").exists():
    if (dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str, request: Request):
        if path.startswith(("api/", "webhook/")):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = (dist / path).resolve()
        if path and candidate.is_file() and dist.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")
else:

    @app.get("/", include_in_schema=False)
    def root():
        return {"app": "SwarnaSetu API", "docs": "/docs", "note": "Build the frontend (cd frontend && npm run build) to serve the web app here."}
