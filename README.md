# DietRiskNet

**AI-Assisted Dietary Analysis and Personalized Disease-Risk-Aware Dietary Guidance — Capstone Research System**

DietRiskNet is a capstone research system that recognises food in a meal photo
and produces **model-derived dietary risk estimates** and **dietary guidance**.
It combines computer vision (YOLOv8 food-region localisation + EfficientNet-B3
classification over 118 Indian food classes), nutrition lookup, longitudinal
indices (DCI / NIS), four XGBoost risk-estimation models, a weighted risk-fusion
engine, and a deterministic rule-based recommendation generator (ExplainDiet).
Optional LLM features — a Nutrition Assistant / Nutrition Coach, meal-specific
AI chat, and an AI Dietitian summary — layer on top and are not required for
the core analysis.

> **Important — model honesty.** DietRiskNet produces **disease-risk estimates**,
> **not diagnoses**. Every score is a model-derived estimate for research and
> dietary guidance only. Read [MODEL_LIMITATIONS.md](MODEL_LIMITATIONS.md)
> before interpreting any output.

---

## Key Features

- **Meal-image analysis** — YOLOv8 localises food regions; EfficientNet-B3
  classifies each crop into one of **118 food classes**; nutrients are looked
  up from an Indian food nutrition database.
- **Dietary indices** — **DCI** (Dietary Consistency Index, longitudinal) and
  **NIS** (Nutritional Imbalance Score, per meal).
- **Risk estimation** — four XGBoost models produce estimates for
  **diabetes, obesity, hypertension, and nutritional-deficiency** risk.
- **Weighted risk fusion** — combines DCI, NIS, and the four risk estimates
  into a single fused score with severity levels.
- **ExplainDiet recommendations** — deterministic, threshold-triggered dietary
  guidance with evidence.
- **Longitudinal view** — dashboard, history, and trends from persisted
  analyses.
- **AI features (optional)** — Nutrition Assistant / Coach chat, meal-specific
  AI chat, and an AI Dietitian meal summary.
- **PDF meal report** — one-click downloadable report per analysis.

---

## System Architecture

```mermaid
graph TD
    Upload[Meal image] --> YOLO[YOLOv8 localises food regions<br/>(single 'food' class)]
    YOLO --> Crops[Extract detected crops]
    Crops --> EffNet[EfficientNet-B3 classifies crops into 118 food classes]
    EffNet --> CSV[Look up nutrition in Indian Food Nutrition CSV]
    CSV --> Agg[Aggregate meal nutrients]
    Agg --> DCI[DCI — dietary consistency index]
    Agg --> NIS[NIS — nutritional imbalance score]
    Agg --> XGB[XGBoost risk estimates<br/>diabetes / obesity / hypertension / deficiency]
    DCI --> Fusion[Weighted risk fusion]
    NIS --> Fusion
    XGB --> Fusion
    Fusion --> Recs[ExplainDiet recommendations]
    Recs --> DB[Persist analysis + dashboard / history / trends]
    Recs -. optional .-> LLM[LLM — Nutrition Assistant / meal chat / AI Dietitian]
```

Notes on the real implementation:

- **YOLOv8 is a localiser, not a classifier.** The deployed detector uses a
  single `food` class to draw bounding boxes around food regions. It does **not**
  identify the 118 dishes — classification is done by EfficientNet-B3.
- **DCI and NIS do NOT feed the XGBoost models.** The four XGBoost
  risk-estimation models consume nutrition plus user-profile features. DCI and
  NIS feed only the **risk-fusion** stage, which combines them with the four
  XGBoost estimates.
- **XGBoost outputs are risk estimates**, not diagnoses.

---

## Tech Stack

- **Backend:** FastAPI, Python 3.10, SQLAlchemy (PostgreSQL / SQLite),
  Pydantic, JWT auth, Uvicorn.
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS v4,
  Framer Motion, TanStack React Query, Zustand, Recharts.
- **Machine Learning:** Ultralytics YOLOv8, PyTorch (EfficientNet-B3, CPU),
  XGBoost, OpenCV, NumPy, Pandas.
- **AI / LLM:** provider-agnostic layer — **Ollama (default, local)** and
  **Gemini (optional cloud)**; ReportLab for PDFs.
- **Deployment:** Docker, Docker Compose, Render (backend), Vercel (frontend).

---

## Project Structure

```
DietRiskNet/
├── backend/
│   ├── database/        # SQLAlchemy connection + ORM models
│   ├── routes/          # FastAPI endpoint routers
│   ├── schemas/         # Pydantic validation models
│   ├── services/        # Business logic (auth, ML, nutrition, prediction, fusion, recs, AI)
│   ├── trained_models/  # YOLO, EfficientNet, XGBoost checkpoints + DCI/NIS configs
│   ├── utils/           # Logging, token auth, image utils
│   └── main.py          # App entrypoint
├── frontend/
│   ├── app/             # App Router pages (dashboard, analysis, history, trends, …)
│   ├── components/      # UI components (sidebar, providers)
│   ├── lib/             # Zustand stores
│   └── services/        # Frontend API request layer
├── nutrition/
│   └── indian_food_nutrition_processed.csv   # Mapped nutrition database
├── scripts/             # Windows helper scripts (setup / start / stop / Ollama)
├── docs/                # Deployment guide, API reference, thesis, final reports
├── run_dietrisknet.cmd  # One-command launcher (configured Windows machine)
├── stop_dietrisknet.cmd # Stop services launched by the launcher
├── render.yaml          # Render blueprint (backend + managed Postgres)
├── .dockerignore        # Docker build-context exclusions (models kept)
├── docker-compose.yml   # Local Postgres + backend + frontend orchestration
├── requirements.txt
└── README.md
```

---

## Quick Start — Existing Configured Windows Machine

On a machine that already has the environment prepared (Python venv,
`frontend/node_modules`, ML models, and local Ollama runtime present), start
everything with one command from the project root in **PowerShell**:

```powershell
.\run_dietrisknet.cmd
```

This script:

- detects the project root automatically,
- starts or reuses a local **Ollama** server,
- starts or reuses the **FastAPI backend** (`http://localhost:8000`),
- starts or reuses the **Next.js frontend** (`http://localhost:3000`),
- runs health checks on all three services,
- avoids starting duplicate services if they are already running,
- opens the frontend in your browser when ready.

Stop the services with:

```powershell
.\stop_dietrisknet.cmd
```

> **Important.** This launcher assumes an **already-configured machine**. It
> does **not** install Python, Node.js, npm packages, Python dependencies,
> Ollama, or ML models. On a fresh machine, run **First-Time Setup** below.

---

## First-Time Setup

On a fresh Windows machine, use the setup helper first:

```powershell
.\scripts\setup_new_pc.bat
```

This script:

- verifies Python 3.10+ and Node.js LTS are installed (it does **not** install
  them — install manually if missing),
- creates `backend\.venv` and installs backend requirements,
- runs `npm install` in `frontend`,
- checks for the project-local Ollama runtime (`runtime\ollama`) and model,
- warns if `.env` is missing (create it from `.env.example`).

After setup, start the project with `.\run_dietrisknet.cmd` or
`.\scripts\start_all.bat`.

---

## Running on Another Computer

Cloning or copying the repository alone is **not always sufficient**. A second
computer needs:

1. **Python 3.10+** and **Node.js LTS** installed and on `PATH`.
2. **ML model artifacts.** The EfficientNet `.pth` checkpoints are stored with
   **Git LFS** — after cloning, run `git lfs pull` (the YOLO `.pt` and XGBoost
   `.pkl` files are committed directly). Do **not** retrain or replace models.
3. **Python environment:**
   ```powershell
   python -m venv backend\.venv
   backend\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
4. **Frontend dependencies:**
   ```powershell
   cd frontend
   npm install
   cd ..
   ```
5. **Environment file:** copy `.env.example` to `.env` and adjust values.
6. **Local AI (optional):** install Ollama (or use the project-local
   `runtime\ollama`), then pull the default model:
   ```powershell
   ollama pull llama3.2:3b
   ```
7. **Database:** the backend falls back to a local SQLite file if
   `DATABASE_URL` is unset — no manual database setup is required for a local
   demo. Tables are created automatically on first startup.

On Windows you can then run `.\scripts\setup_new_pc.bat` (skips what already
exists) and `.\run_dietrisknet.cmd`.

---

## AI / LLM Setup

The **core meal-analysis pipeline and rule-based recommendations require no
LLM**. AI features are additive:

- **Nutrition Assistant / Nutrition Coach** — general nutrition chat that works
  with or without meal history.
- **Meal-specific AI chat** — asks questions about a particular analysis.
- **AI Dietitian summary** — an optional per-meal narrative summary.

**Local provider (default): Ollama**

```bash
ollama serve                 # start the local Ollama server
ollama pull llama3.2:3b      # pull the default model (~2 GB)
```

**Optional cloud provider: Gemini**

Set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` in `.env`. If Gemini is selected
and a request fails, the provider layer automatically falls back to local
Ollama (implemented in `backend/services/llm/`).

**If no LLM is available:** the analysis is still fully produced — `ai_dietitian`
is `null`, chat returns a friendly "temporarily unavailable" message (HTTP 200,
never a 500), and deterministic ExplainDiet recommendations still render. A
failed AI call never invalidates the core ML analysis.

---

## Environment Variables

Documented below are the variables the application actually reads
(`backend/config.py` + frontend build). Never put real credentials in tracked
files — configure them via environment variables.

| Variable | Required? | Default | Notes |
|---|---|---|---|
| `SECRET_KEY` | **Required for deployment** | insecure dev placeholder | Signing key for JWT. The code has an insecure development default; **set a strong random value for any real deployment**. |
| `DATABASE_URL` | optional | SQLite `./dietrisknet.db` | SQLAlchemy connection string. PostgreSQL string for deployment (Render). |
| `PORT` | deployment | `8000` | Backend HTTP port (Render sets this). |
| `UPLOAD_DIR` | optional | `backend/uploads` | Meal-image upload directory (auto-created). Persistence depends on the hosting plan. |
| `MODELS_DIR` | optional | auto-resolved to `backend/trained_models` | Override model directory if needed. |
| `NUTRITION_CSV_PATH` | optional | auto-resolved to `nutrition/…csv` | Override nutrition database path if needed. |
| `FOOD_CLASSIFIER_MODEL` | optional | `…EfficientNetB3.pth` | Primary classifier; B0 is the fallback if the B3 file is absent. |
| `LLM_PROVIDER` | optional | `ollama` | `ollama` (default) or `gemini`. |
| `OLLAMA_URL` / `OLLAMA_MODEL` / `OLLAMA_TIMEOUT` | optional | `http://localhost:11434` / `llama3.2:3b` / `120` | Local provider settings. |
| `GEMINI_API_KEY` / `GEMINI_MODEL` / `GEMINI_TIMEOUT` | optional | empty / `gemini-2.0-flash` / `15` | Leave empty to keep Gemini disabled. |
| `NEXT_PUBLIC_API_URL` | **frontend build-time** | `http://localhost:8000/api` | Frontend API base. **Must be set before the production build** to the deployed backend. |
| `FRONTEND_ORIGIN` | deployment | empty | Backend CORS origin for the deployed frontend (e.g. a Vercel app). |

---

## Verification & Testing

**Backend (root directory):**

```bash
python -m pytest backend/tests -q
```

Current status: **193 tests passing / 0 failing** (includes threshold
classification, risk-fusion boundaries, duplicate detection, AI cache, chat,
PDF report, nutrition coach, assistant, meal-AI integration, and an end-to-end
pipeline test).

**Frontend (in `frontend/`):**

```bash
npx tsc --noEmit   # TypeScript type-check
npm run lint       # ESLint
npm run build      # production build
```

---

## Deployment

The intended deployment architecture (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
for full instructions):

- **Backend → Render** (Docker web service, managed PostgreSQL).
- **Frontend → Vercel** (Next.js; set the build-time `NEXT_PUBLIC_API_URL` to
  the deployed backend).

Required deployment configuration: a strong `SECRET_KEY`, `DATABASE_URL`
(managed Postgres), and `NEXT_PUBLIC_API_URL`. Ollama is **not** bundled into
the cloud backend — the core pipeline runs without it, and AI chat degrades
gracefully when no remote provider is configured. Uploaded images live on the
container filesystem; on Render's free plan they are ephemeral (lost on
redeploy) unless a paid persistent disk is added.

Repo deployment files: `render.yaml`, `.dockerignore`, `docker-compose.yml`,
`backend/Dockerfile`.

> The live deployment is **not** claimed to be working here; follow
> [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) to deploy and verify.

---

## Model Limitations

Read the full [MODEL_LIMITATIONS.md](MODEL_LIMITATIONS.md). Key points:

- **Fixed vocabulary** — YOLOv8 is a single-class (`food`) localiser;
  EfficientNet-B3 recognises **118 food classes**. Anything outside those is
  mislabelled or rejected.
- **Portion size is estimated, not measured** — serving weights come from a
  static lookup table; nutrient totals carry portion-size uncertainty.
- **Single, top-down photo** — optimised for clear, well-lit meal photos.
- **Confidence ≠ correctness** — model self-assurance does not guarantee the
  label is the true food.
- **Risk estimates only** — XGBoost outputs and the fused score are
  model-derived estimates, not clinical diagnoses.

---

## Documentation

- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Render + Vercel deployment guide
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) — API reference
- [docs/thesis/](docs/thesis/) — architecture, methodology, thesis chapters
- [docs/final/](docs/final/) — evaluation reports, demo/viva preparation
- [HOW_TO_RUN.md](HOW_TO_RUN.md) — local run guide
- [MODEL_LIMITATIONS.md](MODEL_LIMITATIONS.md) — model honesty & limitations
