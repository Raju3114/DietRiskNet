# DietRiskNet — Portable Project Migration Guide

Practical guide for copying DietRiskNet (with a **project-local Ollama**) to an
external HDD and running it on another Windows laptop — including the Ollama
runtime and the `llama3.2:3b` model, with **no Gemini API key required**.

---

## 1. What changed (this migration)

- Copied the portable Ollama runtime into the project: `runtime/ollama/bin/`
  (`ollama.exe` + `lib/`, ~1.9 GB).
- Copied the `llama3.2:3b` model into the project: `runtime/ollama/models/`
  (~1.9 GB), so Ollama needs **no separate install** on the destination.
- Created portable startup scripts in `scripts/` that resolve the project root
  **relative to their own location** (work from any drive/folder, including
  paths with spaces).
- Created `scripts/setup_new_pc.bat` to recreate the environment on a new PC.
- Removed machine-specific paths from `.env.example` (the app resolves
  `MODELS_DIR` / `NUTRITION_CSV_PATH` to project-relative defaults).
- Portability scan: **0 machine-specific runtime paths** remain in source.

## 2. Portable architecture

```
DietRiskNet/
├── backend/                 # FastAPI source (+ trained_models/)
├── frontend/                # Next.js source
├── docs/
├── nutrition/               # 1,014-dish nutrition CSV
├── datasets/                # sample_meal.png
├── runtime/
│   └── ollama/
│       ├── bin/             # ollama.exe + lib/  (project-local Ollama)
│       └── models/          # llama3.2:3b (blobs + manifests)
├── scripts/
│   ├── start_ollama.bat
│   ├── start_backend.bat
│   ├── start_frontend.bat
│   ├── start_all.bat
│   └── setup_new_pc.bat
├── .env                     # local config (gitignored — do not share secrets)
├── .env.example
└── requirements.txt
```

## 3. Project-local Ollama

- Executable: `runtime/ollama/bin/ollama.exe`
- Runtime libs: `runtime/ollama/bin/lib/ollama/` (CUDA v12/v13 + CPU DLLs)
- Model dir: `runtime/ollama/models/` (contains `blobs/` + `manifests/`)
- Model: `llama3.2:3b` (verified — version 0.32.5, real generation OK)
- `start_ollama.bat` sets `OLLAMA_MODELS=<root>\runtime\ollama\models` and
  `OLLAMA_HOST=127.0.0.1:11434`, reuses an already-running server on 11434,
  and waits for readiness.

## 4. Folders to COPY to the HDD

- All source: `backend/` (incl. `backend/trained_models/`), `frontend/`
  (source + `package.json`/`package-lock.json`), `nutrition/`, `datasets/`,
  `docs/`, `scripts/`
- `runtime/ollama/bin/` and `runtime/ollama/models/` (offline Ollama)
- `requirements.txt`, `.env.example`, `README.md`, `docker-compose.yml`,
  `render.yaml`, `.gitignore`

## 5. Folders NOT worth copying (regenerate)

| Folder | Why | How to regenerate |
|---|---|---|
| `backend/.venv` | machine-bound (venv pyvenv.cfg points to the source PC Python) | `scripts/setup_new_pc.bat` |
| `frontend/node_modules` | not portable | `npm install` (setup script) |
| `frontend/.next` | build cache | `npm run dev` / `npm run build` |
| `__pycache__`, `.pytest_cache`, `backend/logs` | caches/logs | auto-created |
| `backend/uploads` | runtime user data | optional (test meal images) |
| `dietrisknet.db`, `test.db` | runtime DB | optional (demo data) |
| `new models/` | **redundant duplicate** of `backend/trained_models` (SHA-256 identical) | skip |

## 6. Software required on the destination laptop

- **Python 3.10+** (from python.org; tick "Add to PATH")
- **Node.js LTS + npm** (from nodejs.org)
- No separate Ollama install — Ollama travels inside the project.
- No Gemini key — Ollama is the default local provider.

## 7. First run on a new PC

1. Copy the project (from the HDD) anywhere, e.g. `E:\DietRiskNet`.
2. `cd scripts`
3. Run `setup_new_pc.bat` — it checks Python/Node, creates `backend\.venv`,
   installs `requirements.txt`, runs `npm install`, and verifies the project
   Ollama binary + model.
4. Create/keep `.env` (see §8).
5. Run `start_all.bat`.

## 8. .env setup

`.env` is **not** in git and should be copied separately (or created from
`.env.example`). Required values:

```
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=120
# GEMINI_API_KEY=           # OPTIONAL — leave empty for a fully local Ollama run
```

**Security:** never copy or share real API keys in `.env`; never commit `.env`.

## 9. Startup scripts (all determine the project root via `%~dp0..`)

| Script | What it does |
|---|---|
| `start_ollama.bat` | Starts project-local Ollama on 11434 (reuses an existing server) |
| `start_backend.bat` | Starts FastAPI via `backend\.venv\python -m uvicorn backend.main:app` |
| `start_frontend.bat` | `cd frontend && npm run dev` |
| `start_all.bat` | Starts Ollama, then backend + frontend in their own windows |

URLs: Ollama `http://localhost:11434` · Backend `http://localhost:8000`
(/docs) · Frontend `http://localhost:3000`.

## 10. Copying to an external HDD

Reserve **≈ 5 GB** (see §16). Copy the folders in §4, exclude §5. Excluding
`backend/.venv`, `frontend/node_modules`, `frontend/.next`, `new models/`,
uploads/logs/DBs keeps the transfer ≈ **4.1 GB**.

## 11. Running from a different drive letter

Supported. All scripts use `%~dp0..` (relative to the script), `config.py`
uses project-relative defaults, and Ollama uses `runtime\...` paths. Verified
statically for `E:\DietRiskNet`.

## 12. Running under a different Windows username

Supported. No source or script references the original user profile. The only
machine-specific piece is `backend\.venv` (recreated by `setup_new_pc.bat`).

## 13. CPU / GPU considerations

- **ML models (YOLO/EfficientNet/XGBoost):** CPU-only inference
  (`torch.set_num_threads(1)`); no GPU required.
- **Ollama:** ships CUDA v12/v13 DLLs in `lib/`. On a laptop **without** an
  NVIDIA GPU, Ollama automatically falls back to CPU (verified — this project
  runs CPU). On a **different** NVIDIA GPU, Ollama auto-selects the driver set;
  exact performance varies, but it works without configuration.
- First model load on CPU is slower (~5–10 s); subsequent calls are fast.

## 14. Troubleshooting

- **Port 8000/3000/11434 in use** → stop the old process first, then
  `start_all.bat`.
- **Ollama not ready** → check `http://localhost:11434/api/version`; the model
  dir must contain `manifests/` and `blobs/`.
- **"AI section missing"** → confirm Ollama is running and `GET
  /api/ai/health` reports `provider=ollama, status=ok`.
- **`python` not found** → install Python 3.10+ and add to PATH.
- **`npm` not found** → install Node LTS.
- **Backend fails to start** → run `setup_new_pc.bat` again (venv rebuild).

## 15. Demo-day startup procedure

1. `scripts\start_all.bat` (or the three individual scripts).
2. Wait for "Ollama ready".
3. Open `http://localhost:3000` → Login/Register.
4. Upload `datasets/sample_meal.png` → Analyse.
5. Show AI Dietitian, Nutrition Assistant, Coach, Meal Chat.
6. Download the PDF report.

## 16. Storage requirements

| Item | Size |
|---|---|
| `runtime/ollama/bin` | ~1.9 GB |
| `runtime/ollama/models` | ~1.9 GB |
| `backend/trained_models` | ~0.17 GB |
| Source + docs + nutrition + scripts | ~0.1 GB |
| **HDD transfer (recommended)** | **≈ 4.1 GB** (reserve ≥ 5 GB) |
| After setup on the laptop (adds venv/node_modules/.next) | ~7.7 GB |

## 17. Emergency manual startup (if a script misbehaves)

```
# Ollama
set OLLAMA_MODELS=<root>\runtime\ollama\models
set OLLAMA_HOST=127.0.0.1:11434
<root>\runtime\ollama\bin\ollama.exe serve

# Backend
cd <root>
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd <root>\frontend
npm run dev
```

---

*Verified end-to-end: project-local Ollama (0.32.5, llama3.2:3b), real
generation, full ML pipeline, AI Dietitian, Nutrition Assistant, Coach, Meal
Chat, PDF, offline fallback, and 169 passing backend tests.*
