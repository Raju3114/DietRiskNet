# How to Run DietRiskNet

## Step 1 — Open the project

Open a terminal in the project root:

```
DietRiskNet/
├── backend/
├── frontend/
├── nutrition/
├── datasets/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Step 2 — Start the backend

Open **Terminal 1**.

### 2a — Create a virtual environment

```bash
cd backend
python -m venv .venv
```

### 2b — Activate it

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

Your prompt should now show `(.venv)`.

### 2c — Install dependencies

```bash
pip install --upgrade pip
pip install -r ../requirements.txt
```

### 2d — Start the server

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Wait about 5 seconds for:

```
Uvicorn running on http://127.0.0.1:8000
```

### 2e — Verify

Open http://localhost:8000 in your browser or run:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"app":"DietRiskNet","status":"healthy","message":"Welcome to the DietRiskNet FastAPI Service!"}
```

---

## Step 3 — Start the frontend

Open **Terminal 2** (separate from Terminal 1).

```bash
cd frontend
npm install
npm run dev
```

Wait until you see:

```
✓ Ready in ~2s
http://localhost:3000
```

Open http://localhost:3000 in your browser.

---

## Step 4 — Register an account

On the DietRiskNet landing page, click **Get Started**.

Or use the terminal:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword","full_name":"Your Name"}'
```

Save the `access_token` from the response — you will need it for the next steps.

---

## Step 5 — AI features (Ollama default / Gemini optional)

The ML pipeline and rule-based recommendations work with **no LLM**. The AI
features (AI Dietitian, meal chat, AI Nutrition Assistant, Personalized
Nutrition Coach) use **Ollama by default**:

```bash
ollama serve               # start the local Ollama server (if not running)
ollama pull llama3.2:3b    # pull the default model (~2 GB)
```

Verify the AI health endpoint reports the Ollama provider:

```bash
curl http://localhost:8000/api/ai/health
# {"provider":"ollama","model":"llama3.2:3b","status":"ok", ...}
```

Optionally, set `LLM_PROVIDER=gemini` and a `GEMINI_API_KEY` in `.env` to use
Gemini as a cloud provider (with automatic fallback to Ollama). With no LLM
available, `ai_dietitian` is `null`, chat returns a friendly message, and the
app never crashes.

---

## Step 6 — Test the full meal pipeline

Save your token as a variable:

```bash
TOKEN="<paste your access_token here>"
```

### 5a — Upload a meal photo

```bash
curl -X POST http://localhost:8000/api/analyze-meal \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@datasets/sample_meal.png" \
  -F "notes=Test meal"
```

This runs the complete pipeline: YOLO detection → EfficientNet classification → nutrition lookup → DCI → NIS → disease predictions → risk fusion → recommendations.

The response includes the meal analysis with nutritional breakdown, risk scores, and dietary recommendations.

### 5b — View your dashboard

```bash
curl http://localhost:8000/api/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

### 5c — View your history

```bash
curl http://localhost:8000/api/history \
  -H "Authorization: Bearer $TOKEN"
```

---

## Step 7 — Run the tests

In Terminal 1 (stop the server with `Ctrl+C` first), or in a **new Terminal 3**:

```bash
cd DietRiskNet
python -m pytest backend/tests/test_thresholds.py -v
```

Expected output:

```
47 passed in 0.19s
```

---

## Step 8 — Stop everything

**Terminal 1:** press `Ctrl+C` to stop the backend.

**Terminal 2:** press `Ctrl+C` to stop the frontend.

---

## Troubleshooting

### Frontend pages hang, stay on "Pending", or return 500

This is usually caused by a stale Next.js / Turbopack cache in the `.next` directory.

**Windows (Command Prompt):**
```cmd
cd frontend
rmdir /s /q .next
npm run dev
```

**macOS / Linux:**
```bash
cd frontend
rm -rf .next
npm run dev
```

After clearing the cache, the frontend will recompile all pages from scratch (takes slightly longer on the first load).

---

### Port 8000 or 3000 already in use

```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### "SECRET_KEY is set to an insecure default value"

This is normal for development mode. The app still works. For production, generate a real key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Then set it as `SECRET_KEY` in your `.env` file or as an environment variable.

### Virtual environment not working

Delete it and recreate:

```bash
rm -r backend/.venv       # macOS / Linux
rmdir /s backend\.venv     # Windows
cd backend
python -m venv .venv
```

### "No module named 'pytest'"

```bash
pip install pytest
```

### Frontend says "Cannot reach backend"

Make sure the backend is running on port 8000. The frontend expects the API at `http://localhost:8000/api`.

---

## Using Docker instead

If you have Docker installed, you can skip Steps 2 and 3 and run everything with one command:

```bash
docker-compose up --build
```

This starts three containers:

| Container | URL |
|-----------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

To stop:

```bash
docker-compose down
```

---

## Where to find API docs

With the backend running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
