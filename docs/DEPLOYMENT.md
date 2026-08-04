# DietRiskNet — Deployment Guide

Deployment target:

- **Frontend:** Vercel (Next.js)
- **Backend:** Render Docker web service (FastAPI / uvicorn)
- **Database:** managed PostgreSQL
- **AI/Ollama:** NOT bundled into the cloud backend. The core pipeline runs
  deterministically without an LLM; AI chat degrades gracefully to a friendly
  "temporarily unavailable" message when no remote provider is configured.

This document contains **no secrets**. All secret values must be provided via
your hosting platform's environment-variable configuration.

---

## 1. Architecture

```
Browser ─▶ Vercel (Next.js static/runtime)
               │  NEXT_PUBLIC_API_URL=https://<backend>/api
               ▼
Render ─▶ FastAPI (uvicorn, 1 worker, CPU-only PyTorch)
               │
               ├─▶ Managed PostgreSQL (DATABASE_URL)
               ├─▶ Trained models baked into the Docker image
               │      (backend/trained_models/)
               ├─▶ Uploads on container filesystem (UPLOAD_DIR)
               └─▶ optional LLM provider (Ollama / Gemini) for CHAT only
```

Core pipeline: YOLOv8 → EfficientNet-B3 → Nutrition → DCI/NIS → XGBoost →
Risk Fusion → ExplainDiet Recommendations. This never calls an LLM.

## 2. Required environment variables

| Variable | Where | Purpose / requirement |
|---|---|---|
| `SECRET_KEY` | Render (backend) | **REQUIRED.** Generate a strong random value. Never commit one. Local dev insecure default is acceptable locally only. |
| `DATABASE_URL` | Render (backend) | Managed PostgreSQL connection string (Render wires this automatically). SQLAlchemy reads it directly. |
| `PORT` | Render (backend) | HTTP port, `8000`. uvicorn binds `0.0.0.0:PORT`. |
| `UPLOAD_DIR` | Render (backend) | Default `/app/backend/uploads`. Parent dir is auto-created on startup. |
| `LLM_PROVIDER` | Render (backend) | `ollama` (default) or `gemini`. Not bundled in cloud; chat degrades if unreachable. |
| `NEXT_PUBLIC_API_URL` | Vercel (frontend) | **Build-time public** variable → `https://<backend>/api`. Must be set before the production build. |
| `FRONTEND_ORIGIN` | Render (backend) | CORS origin for the frontend. Leave empty when frontend is on `*.vercel.app` (a safe pattern is allowed); set to the real origin otherwise. |

## 3. Backend — Render setup

1. Build from the repo root using `backend/Dockerfile` (Render `runtime: docker`).
2. Provide the env vars above (Render auto-generates `SECRET_KEY` if you use
   the `render.yaml` blueprint; it also provisioned the managed Postgres).
3. Health check: Render hits `/`, which returns `{"status": "healthy"}`.

The Docker image includes:

- `backend/` (source + `backend/trained_models/` — YOLO / EfficientNet /
  XGBoost model artifacts are **kept in the image**)
- `nutrition/` (food nutrition database)
- Python CPU-only dependencies (PyTorch CPU wheel)

## 4. PostgreSQL setup

- Managed PostgreSQL is provisioned by Render (`dietrisknet-db` in
  `render.yaml`) and connected via `DATABASE_URL`.
- On first startup the backend auto-creates all tables via
  `Base.metadata.create_all(...)`; **no migration step is required for the
  current schema.**
- Cloud deployment starts with an **empty** production database. Local user
  data (SQLite) is not copied up.

## 5. Frontend — Vercel setup

1. Import the `frontend/` directory as a Next.js project (or the whole repo
   with root=`frontend/`).
2. Set **`NEXT_PUBLIC_API_URL=https://<backend-host>/api`** as a build-time
   environment variable **before** building. `NEXT_PUBLIC_*` is inlined at
   build time, so changing it requires a rebuild.
3. If `NEXT_PUBLIC_API_URL` is unset the frontend falls back to
   `http://localhost:8000/api` for local development only — no production
   hostname is hard-coded in source.

CORS: the backend allows the configured `FRONTEND_ORIGIN` plus a safe
`*.vercel.app` pattern. A wildcard `*` origin is intentionally **not** used.

## 6. Upload persistence (IMPORTANT)

Meal images are written to the container filesystem (`UPLOAD_DIR`,
mounted at `/static`). **The Render FREE plan provides an ephemeral
filesystem and no persistent disk** — uploads are lost on every redeploy,
and previously referenced `/static/...` images then 404.

- For a short-lived demo this is acceptable.
- For durable uploads you must add a **paid Render persistent disk** mounted
  under `UPLOAD_DIR`, or move to object storage later. Do not assume a free
  persistent disk exists.

## 7. Ollama / cloud-AI limitation

Ollama (llama3.2:3b) is **not** deployed with the cloud backend. Consequences:

- The core analysis pipeline (YOLOv8→…→Recommendations) works fully.
- AI Dietitian chat and Nutrition Assistant return a friendly
  "temporarily unavailable" message (HTTP 200, never a 500) when no provider
  is reachable.
- To enable cloud chat later, set `LLM_PROVIDER=gemini` and provide a
  `GEMINI_API_KEY`, or run Ollama as a separate reachable service.

## 8. Deployment verification procedure

1. **Backend:** open `https://<backend>/` → `{"app": "DietRiskNet", "status": "healthy", ...}`.
2. **API docs:** confirm `/docs` loads (OpenAPI). *(Public: optionally restrict in production.)*
3. **Both:** confirm the Vercel frontend at `https://<app>.vercel.app` loads
   and the auth register/login round-trip against the Render backend without
   CORS errors.
4. **Real meal pipeline:** upload a meal image and confirm analysis completes
   (detection → nutrition → DCI/NIS → risk → recommendations).
5. **AI degrade:** in chat, confirm the friendly "temporarily unavailable"
   fallback appears instead of an error when no LLM provider is configured.

## 9. Rollback

The known-good local capstone checkpoint is:

```
54735e1bb2b972f61bc7d9a83ed0a9923d766862
```

- **Frontend (Vercel):** redeploy the previous successful Vercel build, or
  point the project back to the `main` branch.
- **Backend (Render):** redeploy from the previous commit `54735e1...`.
- Any deployment-preparation work on this branch is done only on
  `deploy/render-vercel`; `main` is untouched.

Rollback does not affect the managed Postgres database (data persists).

---

*Security note:* never place a real `SECRET_KEY` or `GEMINI_API_KEY` in a
tracked file. Configure them as environment variables in the hosting
platform only.