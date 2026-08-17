# How to Run DietRiskNet

A complete step-by-step guide for setting up, running, testing, and troubleshooting DietRiskNet on a new machine.

---

## 1. Prerequisites

Before setting up DietRiskNet, ensure your environment meets the following requirements:

- **Python**: Version **3.10.x** (3.10.0 to 3.10.11 recommended). Check with `python --version` or `py -0p`.
- **Node.js**: Version **18.x** or **20.x LTS**. Check with `node --version`.
- **Package Managers**: `pip` (Python) and `npm` (Node).
- **Git & Git LFS**: Installed on `PATH` to pull large model binary artifacts (`.pth` weights).
- **OS Notes**:
  - **Windows**: PowerShell 5.1+ or Windows Terminal recommended. Ensure execution policy allows script execution (`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`).
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

## 4. Quick Command Reference (Copy-Paste Ready)

### A) Fresh Setup

**Windows (PowerShell):**
```powershell
# 1. Setup backend virtual environment (Python 3.10)
cd "backend"
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# 2. Setup environment variables
Copy-Item .env.example .env

# 3. Setup frontend dependencies
cd "frontend"
npm install
cd ..
```

**macOS / Linux:**
```bash
# 1. Setup backend virtual environment (Python 3.10)
cd backend
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# 2. Setup environment variables
cp .env.example .env

# 3. Setup frontend dependencies
cd frontend
npm install
cd ..
```

---

### B) Daily Startup

**Automated (Windows PowerShell):**
```powershell
.\run_dietrisknet.cmd
```

**Stop Launcher (Windows PowerShell):**
```powershell
.\stop_dietrisknet.cmd
```

---

### C) Backend Only

**From Project Root (Windows PowerShell):**
```powershell
$env:PYTHONPATH="."
& "backend/.venv/Scripts/python.exe" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**From Inside `backend/` Directory (Windows PowerShell):**
```powershell
cd backend
$env:PYTHONPATH=".."
& ".\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**From Project Root (macOS / Linux):**
```bash
PYTHONPATH=. backend/.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

---

### D) Frontend Only

**Windows / macOS / Linux:**
```bash
cd frontend
npm run dev
```

---

### E) Production Build & Code Quality Verification

**1. Backend Unit & Integration Tests (from project root):**
```powershell
$env:PYTHONPATH="."
& "backend/.venv/Scripts/python.exe" -m pytest backend/tests
```

**2. Frontend TypeScript Compilation (from `frontend/`):**
```powershell
cd frontend
npx tsc --noEmit
```

**3. Frontend ESLint Quality Check (from `frontend/`):**
```powershell
cd frontend
npm run lint
```

**4. Frontend Production Build Check (from `frontend/`):**
```powershell
cd frontend
npm run build
```

---

## 5. Expected URLs & Endpoints

| Service | Component | URL |
|---|---|---|
| Frontend Web UI | Application Dashboard & Pages | `http://localhost:3000` |
| Backend API | Root Health Endpoint | `http://localhost:8000/` |
| API Documentation | Interactive Swagger UI | `http://localhost:8000/docs` |
| API Documentation | ReDoc Documentation | `http://localhost:8000/redoc` |
| OpenAPI Schema | Raw JSON Schema | `http://localhost:8000/api/openapi.json` |

---

## 6. Common Troubleshooting Steps

### Issue: `ModuleNotFoundError: No module named 'backend'`
- **Cause**: Python path is not pointing to the project root directory when running backend modules or tests.
- **Fix**: Set `PYTHONPATH=.` before running `pytest` or `uvicorn` commands from the project root, or set `PYTHONPATH=..` when inside the `backend/` directory.

### Issue: `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`
- **Cause**: The Python virtual environment was created with a Python version higher than 3.10 (e.g., Python 3.14).
- **Fix**: Explicitly use Python 3.10 when creating `.venv`:
  ```powershell
  cd backend
  py -3.10 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

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
