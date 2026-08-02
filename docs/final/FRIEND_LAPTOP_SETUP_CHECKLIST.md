# DietRiskNet — Friend-Laptop Setup Checklist

A short, practical checklist to set DietRiskNet up on another Windows laptop
from the external HDD. **No Gemini key needed — Ollama travels inside the
project.**

---

## Before you go

- [ ] Copy the DietRiskNet project to the HDD **without** `backend/.venv`,
      `frontend/node_modules`, `frontend/.next`, `new models/`, uploads/logs/DBs
      (they are regenerated). Keep `runtime/ollama/bin` and
      `runtime/ollama/models` — they must travel.
- [ ] Copy your `.env` separately (or be ready to create it from `.env.example`).
- [ ] Reserve ≥ 5 GB free on the HDD and ≥ 8 GB free on the friend's laptop.

## On the friend's laptop

- [ ] 1. Copy the project from the HDD, e.g. to `E:\DietRiskNet` (any drive/folder works).
- [ ] 2. Install Python 3.10+ from https://www.python.org/downloads/ — tick **"Add python.exe to PATH"**.
- [ ] 3. Install Node.js LTS from https://nodejs.org/ (includes npm).
- [ ] 4. Open a terminal (Win+R → `cmd`) and verify:
      - `python --version`
      - `node --version`
      - `npm --version`
- [ ] 5. `cd E:\DietRiskNet\scripts`
- [ ] 6. Run `setup_new_pc.bat` — it will:
      - [ ] check Python / Node / npm
      - [ ] create `backend\.venv` and install requirements (takes a while)
      - [ ] run `npm install` in `frontend`
      - [ ] verify `runtime\ollama\bin\ollama.exe` and the model folder
- [ ] 7. Create/keep `.env` (gitignored). Minimal content:
      ```
      LLM_PROVIDER=ollama
      OLLAMA_URL=http://localhost:11434
      OLLAMA_MODEL=llama3.2:3b
      OLLAMA_TIMEOUT=120
      ```
- [ ] 8. Run `start_all.bat` (starts Ollama → backend → frontend).

## Verify it works

- [ ] Ollama: open `http://localhost:11434/api/version` → `{"version":"0.32.5"}`
- [ ] Backend: `http://localhost:8000` → healthy JSON; `http://localhost:8000/docs`
- [ ] AI health: `http://localhost:8000/api/ai/health` → `"provider":"ollama","status":"ok"`
- [ ] Frontend: open `http://localhost:3000`
- [ ] Login / Register an account
- [ ] Upload `datasets/sample_meal.png` → Analyse (waits ~10–20 s on CPU)
- [ ] AI Dietitian card + health score appear
- [ ] Nutrition Assistant: type "Suggest a healthy breakfast." → real reply
- [ ] Download the PDF report → opens as a valid PDF

## Reminders

- `backend/.venv` and `frontend/node_modules` are **recreated** — never copied.
- `frontend/.next` is regenerated on first `npm run dev`.
- Ollama needs **no separate install** — it runs from `runtime\ollama`.
- CPU-only laptop: works (Ollama falls back to CPU). NVIDIA GPU: works too
  (auto-selects; performance differs).
- If port 8000/3000 is busy, stop the old process first, then `start_all.bat`.
