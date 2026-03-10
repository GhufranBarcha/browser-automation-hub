"""FastAPI application entry point."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config, worker
from app.database import init_db
from app.routers import router as auth_router
from app.routers.tasks import router as tasks_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: validate config, init DB, start worker. Shutdown: cancel worker."""
    config.validate()
    await init_db()
    logger.info("✅ Database initialized")

    # Start background worker dispatcher
    task = asyncio.create_task(worker.dispatcher_loop())
    logger.info(f"✅ Worker dispatcher started (max_concurrency={config.MAX_CONCURRENCY})")

    yield

    # Graceful shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("👋 Worker dispatcher stopped")


app = FastAPI(
    title="Browser Automation Task Queue",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow React dev server + same-origin in production
_default_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
_extra = os.environ.get("CORS_ORIGINS", "")
if _extra:
    _default_origins.extend([o.strip() for o in _extra.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tasks_router)


@app.get("/health")
async def health():
    return {"status": "ok", "worker_slots": worker.get_active_slots(), "max_slots": worker.get_max_slots()}
