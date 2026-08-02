# 12 — Deployment Guide

## 12.1 Installation

**Prerequisites**: Python 3.10+, Node.js 20+, npm 10+, optional Docker.

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate.bat        # Windows CMD (or .venv\Scripts\Activate.ps1 / source .venv/bin/activate)
pip install --upgrade pip
pip install -r ../requirements.txt

# Frontend
cd ../frontend
npm install
```

## 12.2 Configuration

Copy `.env.example` to `.env` at the project root and set:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLite (`sqlite:///./dietrisknet.db`) or PostgreSQL |
| `SECRET_KEY` | JWT signing key — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `MODELS_DIR` | directory containing the `.pt` / `.pth` / `.pkl` model files |
| `NUTRITION_CSV_PATH` | path to `nutrition/indian_food_nutrition_processed.csv` |
| `UPLOAD_DIR` | directory for uploaded meal images |
| `LLM_PROVIDER` | **`ollama` (default)** or `gemini` (optional cloud) |
| `OLLAMA_URL` | local Ollama server URL (default `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama model, e.g. `llama3.2:3b` (must be pulled first) |
| `OLLAMA_TIMEOUT` | Ollama request timeout in seconds (default 120) |
| `GEMINI_API_KEY` | Google Gemini key — **optional**; leave empty; the app runs fully on Ollama with no key |
| `GEMINI_MODEL` | e.g. `gemini-2.0-flash` |
| `GEMINI_TIMEOUT` | Gemini request timeout in seconds |

Frontend: create `frontend/.env.local` with:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 12.3 Running the Backend

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Tables are created automatically. Verify at `http://localhost:8000/docs`.

## 12.4 Running the Frontend

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`. *(If pages hang, clear the Next.js cache:
`rm -rf frontend/.next` and restart.)*

## 12.5 Running the Evaluation

```bash
# Activate venv, then from the project root:
python -m backend.evaluation.benchmark_pipeline --iterations 5
python -m backend.evaluation.benchmark_ai      --iterations 5
python -m backend.evaluation.benchmark_cache   --iterations 20
python -m backend.evaluation.benchmark_pdf     --iterations 5
python -m backend.evaluation.system_metrics    --iterations 5   # all + charts + tables
```

## 12.6 Generating Reports (PDF)

From the **Analysis page**, click **Download Report**. The endpoint is:

```
GET /api/report/{meal_id}   (Authorization: Bearer <token>)
```

## 12.7 Docker Deployment

```bash
docker-compose up --build        # or: docker-compose up -d --build
docker-compose down              # stop
docker-compose down -v           # stop and remove volumes
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Database | `postgresql://postgres:postgres@localhost:5432/dietrisknet` |

## 12.8 Render Deployment

`render.yaml` deploys the backend (Docker) + a PostgreSQL database.
`SECRET_KEY` is auto-generated (`generateValue: true`). The frontend is
deployed separately (e.g. Vercel) with `NEXT_PUBLIC_API_URL` pointing to
the Render backend. The frontend includes a self-healing fallback that
switches to the production backend when it detects a non-localhost
domain.

## 12.9 Troubleshooting

- **`.next` stale cache** → `rm -rf frontend/.next` then restart.
- **`SECRET_KEY` warning** → set a generated key (see §12.2).
- **Port in use** → `netstat -ano | findstr :8000`, `taskkill /PID <pid> /F`.
- **AI section missing** → the LLM provider is unavailable. For the
  default Ollama setup, ensure `ollama serve` is running and the model is
  pulled (`ollama pull llama3.2:3b`); check `GET /api/ai/health`. Gemini
  (optional) additionally requires `GEMINI_API_KEY`. Rule-based
  recommendations always stand.
