# Backend — `app/`

FastAPI backend that manages browser automation tasks through a queue-based system.

## Modules

| File                   | Purpose                                                       |
|------------------------|---------------------------------------------------------------|
| `main.py`              | FastAPI app entry point — lifespan hooks, CORS middleware      |
| `config.py`            | All settings loaded from environment variables                 |
| `database.py`          | SQLAlchemy async engine, session factory, table creation       |
| `models.py`            | ORM models — `Task` and `TaskEvent`                           |
| `schemas.py`           | Pydantic schemas for API request/response validation           |
| `auth.py`              | Session-based auth using `itsdangerous` signed cookies         |
| `worker.py`            | Background dispatcher — polls DB, runs up to N tasks concurrently |
| `automation_runner.py` | Executes browser automation via the `browser-use` SDK          |

## Routers

| File                   | Prefix         | Description                           |
|------------------------|----------------|---------------------------------------|
| `routers/__init__.py`  | `/api/auth`    | Login, logout, session check          |
| `routers/tasks.py`     | `/api`         | Task CRUD, cancel, retry, queue stats |

## How It Works

1. **User submits a task** via `POST /api/tasks` (prompt text + optional PDF)
2. Task is saved to SQLite with status `queued`
3. **Worker dispatcher** (background loop in `worker.py`) picks up queued tasks
4. Each task runs inside `automation_runner.py`:
   - Launches a Playwright Chromium browser session
   - Creates a `browser-use` Agent with the Claude LLM
   - Agent reads the prompt and drives the browser step-by-step
   - Step progress is written back to the DB as `TaskEvent` records
5. On completion/failure, task status and timestamps are updated

## Task Lifecycle

```
queued → running → completed
                 → failed → (retry) → queued
                 → cancelled
```

## Key Configuration

- `MAX_CONCURRENCY` — controls how many browser tasks run simultaneously (default: 3)
- `BROWSER_HEADLESS` — `true` for servers (no display), `false` for local debugging
- `LLM_MODEL` — which Claude model to use for the AI agent
