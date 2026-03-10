"""Application configuration — all settings from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Browser-use timeouts (keep same as original main.py) ────────────────
os.environ.setdefault("TIMEOUT_BrowserStartEvent", "120")
os.environ.setdefault("TIMEOUT_BrowserLaunchEvent", "120")
os.environ.setdefault("TIMEOUT_UploadFileEvent", "120")

BASE_DIR = Path(__file__).parent.parent

# ── Auth ─────────────────────────────────────────────────────────────────
APP_LOGIN_EMAIL: str = os.environ.get("APP_LOGIN_EMAIL", "admin@example.com")
APP_LOGIN_PASSWORD: str = os.environ.get("APP_LOGIN_PASSWORD", "")
SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")
SESSION_COOKIE_NAME: str = "bu_session"
SESSION_MAX_AGE: int = 60 * 60 * 8  # 8 hours

# ── LLM ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")

# ── Worker ───────────────────────────────────────────────────────────────
MAX_CONCURRENCY: int = int(os.environ.get("MAX_CONCURRENCY", "3"))

# ── Storage ──────────────────────────────────────────────────────────────
UPLOAD_DIR: Path = BASE_DIR / os.environ.get("UPLOAD_DIR", "uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024  # 20 MB

# ── Database ─────────────────────────────────────────────────────────────
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BASE_DIR / 'tasks.db'}",
)


def validate() -> None:
    """Raise on missing critical config at startup."""
    errors = []
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set")
    if not APP_LOGIN_PASSWORD:
        errors.append("APP_LOGIN_PASSWORD is not set")
    if not SECRET_KEY or SECRET_KEY == "change-me-in-production":
        import warnings
        warnings.warn("SECRET_KEY is using default value — change it in production!", stacklevel=2)
    if errors:
        raise RuntimeError("Configuration errors:\n" + "\n".join(f"  • {e}" for e in errors))
