# Frontend — `frontend/`

React 19 single-page application built with Vite and TailwindCSS.

## Tech Stack

- **React 19** + TypeScript
- **Vite** — build tool and dev server
- **TailwindCSS** — utility-first styling
- **React Router v7** — client-side routing
- **TanStack React Query** — server state management and caching
- **Axios** — HTTP client for API calls
- **Lucide React** — icon library

## Pages

| File                  | Route            | Description                              |
|-----------------------|------------------|------------------------------------------|
| `LoginPage.tsx`       | `/login`         | Email + password login form              |
| `DashboardPage.tsx`   | `/dashboard`     | Task list, queue summary, submit new task|
| `TaskDetailPage.tsx`  | `/tasks/:taskId` | Detailed task view with live event log   |

## Components

| File              | Description                                       |
|-------------------|---------------------------------------------------|
| `SubmitForm.tsx`  | Form to create new tasks (prompt + PDF upload)     |
| `TaskTable.tsx`   | Table displaying all tasks with status and actions |

## API Layer

| File          | Description                                      |
|---------------|--------------------------------------------------|
| `client.ts`   | Axios instance configured with base URL + cookies|
| `types.ts`    | TypeScript interfaces matching backend schemas    |

## Development

```bash
npm install
npm run dev       # http://localhost:5173 with HMR
```

The Vite dev server proxies `/api/*` requests to the FastAPI backend at `http://127.0.0.1:8000`.

## Production Build

```bash
npm run build     # outputs to dist/
```

The `dist/` folder contains static files served by Nginx in production.
