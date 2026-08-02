# DietRiskNet — Demo Checklist

A step-by-step sequence for a live demonstration, plus an emergency checklist
for when a service (especially Ollama) fails. Target: ~10–12 minutes.

---

## Pre-demo setup (do this BEFORE the examiner arrives)

- [ ] Backend running: `backend/.venv/Scripts/python -m uvicorn backend.main:app --port 8000`
- [ ] Frontend running: `cd frontend && npm run dev` → open `http://localhost:3000`
- [ ] **Ollama running:** `ollama serve` and model present (`ollama list` shows `llama3.2:3b`)
- [ ] Health check OK: `curl http://localhost:8000/api/ai/health` → `"provider":"ollama","status":"ok"`
- [ ] A test account registered (or ready to register live)
- [ ] `datasets/sample_meal.png` available
- [ ] **Warm up the models:** analyse `sample_meal.png` once so YOLO/EfficientNet
      are loaded and the AI result is cached (makes the live demo fast)

---

## Demo sequence

### 1. Login
- [ ] Open `http://localhost:3000` → **Login** (or Register first)
- [ ] Enter credentials → lands on **Dashboard**
- [ ] Say: *"JWT auth — access + refresh tokens; refresh tokens are revoked on logout."*

### 2. Dashboard
- [ ] Point to **Fused Risk**, **DCI**, **NIS** cards and RDI intake tiles
- [ ] Say: *"Deterministic aggregate of stored meals — no LLM involved."*

### 3. Upload Meal
- [ ] **Upload** page → drop `sample_meal.png` → optional notes → **Execute Diagnostic Analysis**
- [ ] Watch the pipeline progress animation

### 4. YOLO Detection
- [ ] Analysis page shows **bounding-box overlays** on the image
- [ ] Say: *"YOLOv8 localises food regions; a per-class IoU 0.6 filter removes duplicates."*

### 5. EfficientNet Classification
- [ ] **Segmented Biochemical Profiles** list shows the recognized item(s), e.g. **Idli**
- [ ] Say: *"Each crop is classified into one of 118 Indian food classes."*

### 6. Nutrition
- [ ] Show the **Aggregated Meal Nutrition** tiles (calories, carbs, protein, fats, sodium)
- [ ] Say: *"Looked up in the 1,014-dish Indian nutrition database and scaled by serving weight."*

### 7. DCI / NIS
- [ ] Point to the **DCI** and **NIS** cards with their levels
- [ ] Say: *"DCI = 1 − CV of daily calories; NIS = mean deviation from RDI. Classified by a deterministic threshold classifier."*

### 8. Disease Prediction
- [ ] **Predictions** page → four disease-risk cards + **Weighted Risk Fusion** score
- [ ] Say: *"Four XGBoost models + a weighted fusion formula."*

### 9. Risk Fusion
- [ ] Show the fused score/level and the four-gauge cards
- [ ] Say: *"Weights: 0.25 DCI + 0.25 NIS + diabetes 0.20 + obesity 0.15 + hypertension 0.10 + deficiency 0.05."*

### 10. Recommendations
- [ ] **Recommendations** page → ExplainDiet rule cards with clinical explanations
- [ ] Say: *"Threshold-triggered rules with evidence — deterministic, no LLM."*

### 11. AI Dietitian
- [ ] Back on **Analysis** → **AI Dietitian** card: circular health score, meal quality, summary, risk explanation, alternatives
- [ ] Say: *"Health score is computed by the backend; Ollama only explains the verified numbers."*

### 12. Meal Chat
- [ ] In the **Ask AI Dietitian** panel type: *"Is this meal healthy?"*
- [ ] Show the real reply referencing the meal
- [ ] Say: *"Grounded in the persisted meal context; rolling 10-message memory; no ML re-run."*

### 13. Nutrition Assistant
- [ ] **Nutrition Assistant** page → type: *"Suggest a healthy breakfast."*
- [ ] Show the real Ollama reply + the **Personalized Coach** dashboard (averages, patterns, smart goals)

### 14. History / Trends
- [ ] **History** page → meal log cards (foods, nutrients, DCI/NIS, risk)
- [ ] **Trends** page → 7/14/30-day charts (calories, macros, DCI/NIS, four risks)

### 15. PDF Report
- [ ] Back on **Analysis** → **Download Report** → open the PDF (2 pages: image, foods, nutrition, DCI/NIS, risks, recommendations, AI Dietitian)
- [ ] Say: *"ReportLab PDF generated from the persisted analysis."*

### 16. Wrap up
- [ ] Logout (Sign Out)

---

## Emergency checklist (if a service fails)

### Ollama down / AI features unavailable
- [ ] The ML pipeline **still works** — analyse a meal and show results + rule-based recommendations
- [ ] Chat shows a **friendly "temporarily unavailable"** message (not an error page)
- [ ] `curl http://localhost:8000/api/ai/health` → `"status":"unavailable"` (diagnose)
- [ ] Fix: start Ollama (`ollama serve`), confirm `ollama list` shows `llama3.2:3b`, retry
- [ ] Say: *"The AI layer is optional and fail-safe — the clinical core never depends on it."*

### Backend down
- [ ] Restart: `backend/.venv/Scripts/python -m uvicorn backend.main:app --port 8000`
- [ ] Verify `http://localhost:8000/docs` loads

### Frontend hang / "Pending"
- [ ] Clear Next.js cache: `rm -rf frontend/.next` and restart `npm run dev`
- [ ] Confirm `NEXT_PUBLIC_API_URL` points at the backend

### Gemini-only concern (if LLM_PROVIDER=gemini)
- [ ] Remember the app **falls back to Ollama** automatically; with no key it still works
- [ ] `.env` uses `LLM_PROVIDER=ollama` for the default demo

### Slow first run
- [ ] First meal analysis loads models (~20–30 s on CPU) — **warm it up in advance**
- [ ] The frontend has a 15 s API timeout; a cold first call may need a retry — do the warm-up run before the demo
