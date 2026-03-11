# BrowserUse Task Queue

A full-stack web application for queuing and running browser automation tasks powered by the [browser-use](https://github.com/browser-use/browser-use) SDK and Anthropic's Claude LLM.

## Overview

Users log in, submit automation instructions (with optional PDF attachments), and the system queues and executes them using a headless Chromium browser controlled by an AI agent. Live step-by-step progress is tracked in the UI.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│          React 19 + Vite + TailwindCSS           │
│   (Runs in User's Browser — talks to API via 80) │
└──────────────────┬──────────────────────────────┘
                   │  /api/* (Port 80/443)
┌──────────────────▼──────────────────────────────┐
│                   Backend                        │
│              Nginx (Gatekeeper)                  │
│                   │                              │
│         [Local Proxy to :8000]                   │
│                   ▼                              │
│          FastAPI App (Private)                   │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Auth    │  │  Tasks   │  │   Worker      │  │
│  │ (cookie) │  │  (CRUD)  │  │  (dispatcher) │  │
│  └──────────┘  └──────────┘  └───────┬───────┘  │
│                                      │           │
│  ┌───────────────────────────────────▼────────┐  │
│  │         Automation Runner                   │  │
│  │  browser-use SDK → Playwright → Chromium    │  │
│  │  Claude LLM drives each step                │  │
│  └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## Tech Stack

| Layer     | Technology                                   |
|-----------|----------------------------------------------|
| Frontend  | React 19, TypeScript, Vite, TailwindCSS      |
| Backend   | FastAPI, Uvicorn, SQLAlchemy 2.0 (async)     |
| Database  | SQLite via aiosqlite                         |
| Browser   | Playwright (Chromium), browser-use SDK        |
| LLM       | Anthropic Claude (claude-sonnet-4-6)      |
| Auth      | Session cookies (itsdangerous signed tokens) |

## Project Structure

```
BrowserUse-jahaadbeckford/
├── app/                    # Python backend (FastAPI)
│   ├── main.py             # App entry point, lifespan, CORS
│   ├── config.py           # Environment variable settings
│   ├── database.py         # SQLAlchemy async engine & session
│   ├── models.py           # ORM models (Task, TaskEvent)
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── auth.py             # Session-based authentication
│   ├── worker.py           # Background task dispatcher
│   ├── automation_runner.py# browser-use agent execution
│   └── routers/            # API route handlers
│       ├── __init__.py     # Auth routes (/api/auth/*)
│       └── tasks.py        # Task routes (/api/tasks/*)
├── frontend/               # React frontend (Vite)
│   ├── src/
│   │   ├── pages/          # LoginPage, DashboardPage, TaskDetailPage
│   │   ├── components/     # SubmitForm, TaskTable
│   │   └── api/            # Axios client & TypeScript types
│   └── dist/               # Production build output
├── uploads/                # Uploaded PDF files
├── main.py                 # Standalone script (dev/testing)
├── pyproject.toml          # Python dependencies (uv)
├── tasks.db                # SQLite database (auto-created)
├── DEPLOYMENT.md           # Server deployment guide
└── .env                    # Environment variables (not committed)
```

## Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) package manager

### 1. Backend

```bash
# Install Python dependencies
uv sync

# Install Playwright browser
uv run playwright install --with-deps chromium

# Create .env file
cp .env.example .env   # then edit with your keys

# Start the API server
uv run uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev    # starts at http://localhost:5173
```

### 3. Access

Open **http://localhost:5173** — log in with the credentials set in `.env`.

## Environment Variables

| Variable             | Description                        | Default                    |
|----------------------|------------------------------------|----------------------------|
| `ANTHROPIC_API_KEY`  | Anthropic API key (required)       | —                          |
| `APP_LOGIN_EMAIL`    | Login email                        | `admin@example.com`        |
| `APP_LOGIN_PASSWORD` | Login password (required)          | —                          |
| `SECRET_KEY`         | Cookie signing secret              | *(change in production!)*  |
| `MAX_CONCURRENCY`    | Max simultaneous browser tasks     | `3`                        |
| `LLM_MODEL`         | Claude model name                  | `claude-sonnet-4-6`    |
| `BROWSER_HEADLESS`   | Run browser headless               | `true`                     |
| `CORS_ORIGINS`       | Extra CORS origins (comma-sep)     | —                          |
| `DATABASE_URL`       | SQLAlchemy DB URL                  | `sqlite+aiosqlite:///tasks.db` |

## API Endpoints

| Method   | Path                        | Description              |
|----------|-----------------------------|--------------------------|
| `POST`   | `/api/auth/login`           | Log in                   |
| `POST`   | `/api/auth/logout`          | Log out                  |
| `GET`    | `/api/auth/me`              | Get current user         |
| `POST`   | `/api/tasks`                | Create a new task        |
| `GET`    | `/api/tasks`                | List all tasks           |
| `GET`    | `/api/tasks/{id}`           | Get task detail + events |
| `POST`   | `/api/tasks/{id}/cancel`    | Cancel a task            |
| `POST`   | `/api/tasks/{id}/retry`     | Retry a failed task      |
| `DELETE` | `/api/tasks/{id}`           | Delete a task            |
| `GET`    | `/api/queue/summary`        | Queue stats              |
| `GET`    | `/health`                   | Health check             |

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full server deployment instructions (Ubuntu VPS).
