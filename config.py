"""Settings, read once from environment variables.

Every external service is optional. With no keys set, the app runs fully in
demo mode: a built-in WhatsApp simulator, rule-based extraction and typed or
browser-transcribed voice notes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent  # project root


def _load_dotenv() -> None:
    """Read KEY=VALUE lines from .env (project root or backend/) without overriding real env vars."""
    for path in (ROOT_DIR / ".env", BASE_DIR / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: _env(
            "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'data' / 'swarnasetu.db').as_posix()}"
        )
    )
    timezone: str = field(default_factory=lambda: _env("APP_TIMEZONE", "Asia/Kolkata"))
    seed_demo: bool = field(default_factory=lambda: _env_bool("SEED_DEMO", True))
    # Reconciliation tolerance in milligrams (0.010 g by default).
    tolerance_mg: int = field(default_factory=lambda: int(_env("TOLERANCE_MG", "10")))
    # Weight above which the jeweller sees an extra warning before confirming.
    large_weight_mg: int = field(default_factory=lambda: int(_env("LARGE_WEIGHT_MG", "500000")))
    reminder_interval_s: int = field(default_factory=lambda: int(_env("REMINDER_INTERVAL_S", "300")))

    # Speech-to-text (Sarvam). Without a key, voice notes are typed or
    # transcribed in the browser.
    sarvam_api_key: str = field(default_factory=lambda: _env("SARVAM_API_KEY"))
    sarvam_model: str = field(default_factory=lambda: _env("SARVAM_MODEL", "saaras:v4"))

    # LLM extraction and answer phrasing (Gemini). Without a key, rules are used.
    gemini_api_key: str = field(default_factory=lambda: _env("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: _env("GEMINI_MODEL", "gemini-2.5-flash"))

    # Optional Lyzr agent for the ledger Q&A.
    lyzr_api_key: str = field(default_factory=lambda: _env("LYZR_API_KEY"))
    lyzr_agent_id: str = field(default_factory=lambda: _env("LYZR_AGENT_ID"))
    lyzr_url: str = field(
        default_factory=lambda: _env("LYZR_URL", "https://agent-prod.studio.lyzr.ai/v3/inference/chat/")
    )

    # Real WhatsApp Cloud API. Without these, messages stay in the simulator.
    whatsapp_token: str = field(default_factory=lambda: _env("WHATSAPP_TOKEN"))
    whatsapp_phone_number_id: str = field(default_factory=lambda: _env("WHATSAPP_PHONE_NUMBER_ID"))
    whatsapp_verify_token: str = field(default_factory=lambda: _env("WHATSAPP_VERIFY_TOKEN", "swarnasetu-verify"))
    whatsapp_api_version: str = field(default_factory=lambda: _env("WHATSAPP_API_VERSION", "v21.0"))

    frontend_dist: Path = field(
        default_factory=lambda: Path(_env("FRONTEND_DIST", str(ROOT_DIR / "frontend" / "dist")))
    )

    @property
    def stt_enabled(self) -> bool:
        return bool(self.sarvam_api_key)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def lyzr_enabled(self) -> bool:
        return bool(self.lyzr_api_key and self.lyzr_agent_id)

    @property
    def whatsapp_enabled(self) -> bool:
        return bool(self.whatsapp_token and self.whatsapp_phone_number_id)


settings = Settings()
