# How to Run DietRiskNet

A complete step-by-step guide for setting up, running, testing, and troubleshooting DietRiskNet on a new machine.

---

## 1. Prerequisites

Before setting up DietRiskNet, ensure your environment meets the following requirements:

- **Python**: Version **3.10.x** (3.10.0 to 3.10.11 recommended). Check with `python --version`.
- **Node.js**: Version **18.x** or **20.x LTS**. Check with `node --version`.
- **Package Managers**: `pip` (Python) and `npm` (Node).
- **Git & Git LFS**: Installed on `PATH` to pull large model binary artifacts (`.pth` weights).
- **OS Notes**:
  - **Windows**: PowerShell 5.1+ or Windows Terminal recommended. Ensure execution policy allows script execution if needed (`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`).
  - **macOS / Linux**: Standard bash or zsh shell. Ensure `python3` and `pip3` alias appropriately.

---

## 2. Model Requirements & Artifacts Verification

DietRiskNet requires machine learning models and configuration files located in `backend/trained_models/` and the nutrition CSV in `nutrition/`:

1. **Check model files**:
   - `backend/trained_models/DietRiskNet_FoodDetector_YOLOv8.pt` (~22 MB)
   - `backend/trained_models/DietRiskNet_FoodClassifier_EfficientNetB3.pth` (~131 MB)
   - `backend/trained_models/DietRiskNet_Diabetes_XGBoost.pkl`
   - `backend/trained_models/DietRiskNet_Obesity_XGBoost.pkl`
   - `backend/trained_models/DietRiskNet_Hypertension_XGBoost.pkl`
   - `backend/trained_models/DietRiskNet_NutritionalDeficiency_XGBoost.pkl`
   - `backend/trained_models/DietRiskNet_DCI_Config.json`
   - `backend/trained_models/DietRiskNet_NIS_Config.json`
   - `backend/trained_models/DietRiskNet_RiskFusion_Config.json`
   - `backend/trained_models/efficientnet_classes.json`
   - `nutrition/indian_food_nutrition_processed.csv`

2. **Pull Git LFS assets** (if `.pth` files are text pointers):
   ```bash
   git lfs install
   git lfs pull
   ```

---

## 3. Environment Variables Configuration

Copy `.env.example` to `.env` in the project root:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Key environment variables in `.env`:
- `SECRET_KEY`: Random string for JWT encoding. (Default: insecure development key; generate a production key with `python -c "import secrets; print(secrets.token_urlsafe(48))"`).
- `DATABASE_URL`: Defaults to `sqlite:///./dietrisknet.db` (local file database). Optional PostgreSQL connection string: `postgresql://user:pass@localhost:5432/dietrisknet`.
- `LLM_PROVIDER`: `"ollama"` (default, local) or `"gemini"` (optional cloud).
- `OLLAMA_URL`: Default `http://localhost:11434`.
- `OLLAMA_MODEL`: Default `llama3.2:3b`.
- `GEMINI_API_KEY`: (Optional) Your Google Gemini API key if using Gemini.

---

## 4. Backend Setup

Open **Terminal 1** in the repository root.

### 4a — Create Python Virtual Environment

```bash
cd backend
python -m venv .venv
```

### 4b — Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

Your prompt will show `(.venv)`.

### 4c — Install Backend Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4d — Database Initialization

The database schema initializes automatically on backend startup using SQLAlchemy `Base.metadata.create_all(bind=engine)`. No manual migration step is required for local SQLite or initial setup.

### 4e — Start Backend Server

From the project root directory:

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="."
& "backend/.venv/Scripts/python.exe" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**macOS / Linux:**
```bash
PYTHONPATH=. backend/.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Expected output:
```
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 5. Frontend Setup

Open **Terminal 2** (in parallel with Terminal 1).

### 5a — Install Node Dependencies

```bash
cd frontend
npm install
```

### 5b — Start Frontend Development Server

```bash
npm run dev
```

Expected output:
```
✓ Ready in ~2s
- Local: http://localhost:3000
```

---

## 6. Automated One-Command Startup (Windows)

On Windows, you can start the entire stack (Backend, Frontend, and optional Ollama) with a single command from the project root:

```powershell
.\run_dietrisknet.cmd
```

To stop all background processes started by the launcher:

```powershell
.\stop_dietrisknet.cmd
```

---

## 7. Expected URLs & Endpoints

| Service | Component | URL |
|---|---|---|
| Frontend Web UI | Application Dashboard & Pages | `http://localhost:3000` |
| Backend API | Root Health Endpoint | `http://localhost:8000/` |
| API Documentation | Interactive Swagger UI | `http://localhost:8000/docs` |
| API Documentation | ReDoc Documentation | `http://localhost:8000/redoc` |
| OpenAPI Schema | Raw JSON Schema | `http://localhost:8000/api/openapi.json` |

---

## 8. Verification Steps

To verify that all components are fully functional and pass system checks:

### 8a — Run Backend Unit & Integration Tests

From the project root:

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="."
& "backend/.venv/Scripts/python.exe" -m pytest backend/tests
```

**macOS / Linux:**
```bash
PYTHONPATH=. backend/.venv/bin/pytest backend/tests
```

All 193+ tests must pass.

### 8b — Verify Frontend TypeScript Compilation

From the `frontend` directory:

```bash
cd frontend
npx tsc --noEmit
```

Must complete with exit code 0.

### 8c — Verify Frontend Code Quality (ESLint)

From the `frontend` directory:

```bash
cd frontend
npm run lint
```

Must complete without lint errors.

### 8d — Verify Frontend Production Build

From the `frontend` directory:

```bash
cd frontend
npm run build
```

Must complete successfully with all static pages generated.

---

## 9. Common Troubleshooting Steps

### Issue: `ModuleNotFoundError: No module named 'backend'`
- **Cause**: Python path is not pointing to the project root directory when running backend modules or tests.
- **Fix**: Set `PYTHONPATH=.` before running `pytest` or `uvicorn` commands, or run from the project root directory.

### Issue: `SECRET_KEY is set to an insecure default value`
- **Cause**: Warning logged when `.env` is using the default development JWT key.
- **Fix**: Generate a strong secret key using `python -c "import secrets; print(secrets.token_urlsafe(48))"` and set `SECRET_KEY` in `.env`.

### Issue: Port 8000 or 3000 already in use
- **Cause**: Previous backend or frontend process was left running.
- **Fix (Windows)**:
  ```powershell
  netstat -ano | findstr :8000
  taskkill /PID <PID> /F
  ```
- **Fix (macOS / Linux)**:
  ```bash
  lsof -i :8000
  kill -9 <PID>
  ```

### Issue: Stale Next.js Turbopack Cache (`frontend/.next`)
- **Cause**: Frontend pages fail to render, hang on loading, or return stale build errors.
- **Fix**:
  ```bash
  cd frontend
  # Windows
  rmdir /s /q .next
  # macOS / Linux
  rm -rf .next
  
  npm run dev
  ```

### Issue: Missing ML Model Weights
- **Cause**: EfficientNet `.pth` files were cloned as Git LFS text pointers instead of binary weights.
- **Fix**:
  ```bash
  git lfs install
  git lfs pull
  ```
