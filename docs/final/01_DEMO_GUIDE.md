# DietRiskNet — Final Project Demonstration Guide

*A complete, timed walkthrough for the final project presentation.*

---

## Introduction

This guide is a step-by-step script for presenting **DietRiskNet** live. It
covers the full user journey — from login, through the vision-and-ML meal
analysis pipeline, to the AI Dietitian, the personalized Nutrition Coach,
and the PDF report. Each step explains:

- which page to open,
- which buttons to click,
- what should happen on screen,
- what to say while it runs,
- common examiner questions, and
- model answers.

**Target length: 10–15 minutes.**

---

## Pre-Demo Setup (do before the examiner arrives)

1. **Start the backend** from the project root:
   ```bash
   backend/.venv/Scripts/python -m uvicorn backend.main:app --port 8000
   ```
   > Use `python -m uvicorn`, not the `uvicorn.exe` console script — the
   > copied virtual environment may resolve the wrong site-packages.

2. **Start the frontend**:
   ```bash
   cd frontend && npm run dev
   ```
   Open `http://localhost:3000`.

3. **Warm up the ML models** — analyse one meal (e.g. `datasets/sample_meal.png`)
   *before* the demo so the live analysis is fast (first call loads the
   ~126 MB EfficientNet model and can take 30–60 s).

4. **Set `GEMINI_API_KEY`** if you want to show the AI Dietitian, meal chat,
   and Nutrition Coach live. If you cannot set it, the demo still works:
   the AI card is hidden and chat returns a friendly "temporarily
   unavailable" message. Decide which story to tell:
   - *with a key* → "here are the AI features", or
   - *without a key* → "here is how the system fails safe when the LLM is absent".

5. **Have two or three real meal photos** ready (e.g. a thali, idlis, a
   pizza) — real photos impress more than the bundled sample.

6. Keep the browser on the **landing page**, logged out.

---

## Project Overview (1–2 minutes)

**What to say:**

> "DietRiskNet is an end-to-end medical-adjacent system. A photo of a meal
> is analysed by a deterministic vision-and-ML pipeline: YOLOv8 localises
> food, EfficientNet classifies each dish into one of 118 Indian foods, a
> 1,014-dish Indian nutrition database computes the nutrients, DCI and NIS
> measure dietary consistency and imbalance, four XGBoost models predict
> disease risk, and a weighted fusion produces a single risk score.
> On top of that, a Gemini-powered AI Dietitian explains the results, a
> meal-specific chat and a general Nutrition Coach personalise advice, and
> every meal can be exported as a PDF report. The ML core is deterministic
> and explainable; the AI layer only explains it and fails safe if
> unavailable."

---

## Demo Flow

### 1. Login (1 minute)

- **Page to open:** Landing page (`/`) → click **Get Started**.
- **Buttons to click:** Register (or login with an existing account).
- **What should happen:** A JWT access + refresh token pair is issued; you
  land on the **Dashboard**.
- **What to explain:** "Authentication uses JWT — a short-lived access token
  for API calls and a revocable refresh token for renewing sessions. This
  is also where the user profile is captured, which feeds the disease-risk
  models."

**Common examiner questions:**
- *Why two tokens?* → "A leaked access token expires quickly; the refresh
  token can be revoked on logout, so a stolen token cannot be replayed."
- *Where is the profile used?* → "Age, gender, height, weight and existing
  conditions are inputs to the XGBoost predictors and to the coach's
  personalisation."

### 2. Dashboard (1 minute)

- **Page to open:** Dashboard.
- **Point to:** the **fused-risk gauge**, the **DCI / NIS cards**, the
  **daily intake vs RDI progress bars**, **recent meals**, and the
  **recommendations** panel.
- **What should happen:** Today's aggregated nutrition, latest indices, risk
  score and recommendations render from the stored analyses.
- **What to explain:** "The dashboard aggregates today's meals against
  recommended daily intakes and shows the latest DCI, NIS and fused risk."

**Common examiner questions:**
- *What is the fused risk?* → "A weighted sum —
  `0.25·(1−DCI) + 0.25·NIS + 0.20·diabetes + 0.15·obesity + 0.10·hypertension
  + 0.05·deficiency`. One number that summarises the whole meal."
- *What is DCI?* → "Dietary Consistency Index: 1 minus the coefficient of
  variation of daily calories; high means consistent eating."

### 3. Upload Meal (2–3 minutes) ⭐ highlight

- **Page to open:** Upload page (`/upload`).
- **Buttons to click:** **Analyze Meal**, choose a real meal photo.
- **What should happen:** The **animated pipeline** runs (17 steps), then
  the app navigates to the **Analysis page** with the results.
- **What to explain while it runs:** "YOLOv8 finds food regions and returns
  bounding boxes; each region is cropped and EfficientNet-B3 classifies it;
  the dish is looked up in the nutrition database and scaled by a serving
  weight."

**Common examiner questions:**
- *Why two models?* → "YOLO is strong at localisation, EfficientNet at
  fine-grained classification; cascading them is a standard, modular
  design."
- *How do you stop the same dish being counted twice?* → "A per-class IoU
  filter keeps only the highest-confidence box when two boxes overlap by
  more than 0.6."

### 4. YOLO Detection

- **Where:** inside the analysis pipeline (and visible as **bounding boxes**
  on the Analysis page).
- **What should happen:** each detected food gets a box `(x1, y1, x2, y2)`, a
  confidence, and a coarse class.
- **What to explain:** "YOLOv8 is a single-shot detector: one forward pass
  predicts all boxes and confidences. We then apply a second-stage per-class
  IoU filter so a dish is not double-counted."

**Likely question:** *What is NMS / IoU?* → "Non-Maximum Suppression removes
overlapping boxes for the same object; IoU is the overlap-to-union ratio of
two boxes. We suppress a lower-confidence box when its IoU with a kept box
exceeds 0.6."

### 5. EfficientNet Classification

- **Where:** each crop is classified; results appear as **segment cards**.
- **What should happen:** every crop maps to one of 118 dish names with a
  confidence.
- **What to explain:** "EfficientNet-B3 uses compound scaling for strong
  accuracy per parameter; it resizes each crop to 300×300 (B0 fallback 224)
  and returns a class-indexed probability."

**Likely question:** *Why EfficientNet specifically?* → "Best accuracy per
FLOP; compact enough (~126 MB) to fit a 512 MB container alongside YOLO."

### 6. Nutrition Analysis

- **Where:** segment cards + **aggregated nutrition tiles**.
- **What should happen:** per-item and total calories, protein, carbs, fat,
  sugar, fiber, sodium, calcium, iron, vitamin C, folate.
- **What to explain:** "CSV values are per 100 g; we multiply by the serving
  weight (default 100 g) and sum all items. Lookup uses four tiers: exact →
  alias → normalised → fuzzy."

**Likely question:** *What if a food isn't found?* → "It falls through the
tiers to a default profile and logs the fallback — the pipeline never
crashes."

### 7. DCI

- **Where:** the **Dietary Consistency (DCI)** card.
- **What should happen:** a 0–1 score and a level (High / Moderate / Low /
  Very Low).
- **What to explain:** "With ≥2 days of history, DCI = 1 − CV of daily
  calories; otherwise a single-meal macro-balance fallback. The score is
  mapped to a level by a deterministic threshold classifier."

**Likely question:** *Why threshold instead of intervals?* → "Intervals
overlap at boundaries and the winner depended on JSON key order; a single
inequality per threshold, evaluated strictest-first, is order-independent
and provably overlap-free."

### 8. NIS

- **Where:** the **Nutrient Imbalance (NIS)** card.
- **What should happen:** a score and level (Balanced / Mild / Moderate /
  High / Severe).
- **What to explain:** "NIS is the mean relative deviation from recommended
  daily intakes across six key nutrients — lower is better."

**Likely question:** *What does NIS = 0 mean?* → "The meal matches every RDI
exactly — perfectly balanced."

### 9. Disease Prediction

- **Page to open:** Predictions page (`/predictions`).
- **What should happen:** four **risk gauges** (diabetes, obesity,
  hypertension, deficiency) plus the fused score.
- **What to explain:** "Four independent XGBoost classifiers take the profile
  plus meal features and output a risk probability each."

**Likely question:** *What features feed the models?* → "Age, gender, BMI,
existing conditions and engineered dietary features; each model has its own
feature set from its training data."

### 10. Risk Fusion

- **Where:** Predictions page (fused score) and the dashboard gauge.
- **What should happen:** one fused 0–1 score and a Low/Moderate/High level.
- **What to explain:** "The weights are configurable and the formula is
  transparent, so the number is fully explainable."

**Likely question:** *Why not a simple average?* → "Weights reflect clinical
and data confidence; they live in a JSON file so they can be tuned without
code changes."

### 11. Rule Recommendations

- **Page to open:** Recommendations page (`/recommendations`).
- **What should happen:** threshold-triggered advice cards with explanations
  (e.g. high sodium → "reduce salt").
- **What to explain:** "Rules fire on nutrients and risk scores — e.g.
  sodium > 800 mg or hypertension risk > 0.4 triggers the salt advice. Every
  recommendation is traceable to the input that triggered it."

**Likely question:** *Why rule-based instead of ML?* → "Deterministic and
auditable — important for medical-adjacent advice. Each output can be
justified."

### 12. AI Dietitian

- **Where:** the **AI Dietitian card** on the Analysis page.
- **What should happen:** circular **health score**, meal quality, summary,
  risk explanation, recommendations, healthier alternatives, warnings.
- **What to explain:** "The health score is computed by the backend — Gemini
  only explains it, so it cannot hallucinate the score. If Gemini fails,
  `ai_dietitian` is null and the rule-based advice stands."

**Common examiner questions:**
- *How do you stop Gemini contradicting your predictions?* → "A strict
  system prompt and schema-validated JSON output; it explains the backend's
  values, never invents new ones."
- *What if Gemini is down?* → "The meal analysis still succeeds — the AI
  field is simply null and the rule engine remains. It never returns a 500
  because of Gemini."

### 13. AI Nutrition Assistant

- **Page to open:** Nutrition Assistant (`/nutrition`).
- **Buttons to click:** a **quick action** (e.g. 📊 Weekly Summary) or type a
  nutrition question.
- **What should happen:** the assistant answers about nutrition, meal
  planning, hydration, grocery lists, etc.; off-topic questions are politely
  redirected.
- **What to explain:** "It works even with no meal analysed. When history
  exists, it includes the stored data for personalisation — no ML re-run.
  Obvious off-topic questions are intercepted locally to avoid an
  unnecessary LLM call."

**Likely question:** *How is it kept on-topic?* → "A keyword guard returns a
canned reply for obvious off-topic topics, and the system prompt enforces the
nutrition scope."

### 14. Personalized Nutrition Coach

- **Where:** the **dashboard above the chat** on the Nutrition page.
- **What should happen:** average calories/protein/carbs/fat, average
  DCI/NIS, **meals this week**, **risk trend**, detected **patterns** (e.g.
  high sodium), **smart goals** with progress bars, positive habits and
  areas to improve.
- **What to explain:** "The dashboard is deterministic analytics from stored
  meal history — free, reproducible and unable to hallucinate. The coach
  then feeds that verified summary into Gemini so the advice is grounded in
  real numbers."

**Likely question:** *Why deterministic analytics instead of AI?* → "It is
testable, instant, and always reflects the database exactly; the LLM only
writes the narrative around verified facts."

### 15. History

- **Page to open:** History (`/history`).
- **What should happen:** a chronological log of every meal with foods,
  indices and risk.
- **What to explain:** "History comes from the stored analyses, so everything
  is consistent with what we have seen."

### 16. Trends

- **Page to open:** Trends (`/trends`).
- **Buttons to click:** switch the **7 / 14 / 30-day** tabs.
- **What should happen:** charts for calories, macros, DCI/NIS, and the four
  disease risks over time.
- **What to explain:** "Trends are aggregated from stored analyses —
  longitudinal, not re-computed."

### 17. PDF Report

- **Where:** Analysis page → **Download Report**.
- **What should happen:** a PDF downloads containing the meal image, foods
  table, nutrition, DCI/NIS, predictions, fusion, the AI Dietitian section,
  and a "Generated by DietRiskNet" footer.
- **What to explain:** "ReportLab builds a paginated document from the stored
  analysis — no re-computation. Page breaks, tables and the embedded image
  are handled by platypus flowables."

**Likely question:** *Why ReportLab?* → "It generates professional documents
in pure Python with automatic page breaks and tables, ideal for server-side
generation."

---

## Wrap-Up (30 seconds)

> "In summary: a deterministic, explainable ML core enhanced by a fail-safe
> AI layer, with caching, PDF export, a benchmarking module that produces
> dissertation-ready tables, and 149 automated tests. The architecture is
> modular and provider-agnostic, so the LLM can be swapped without touching
> the pipeline."

---

## Demo Pacing Cheat-Sheet

| Minute | Segment |
|---|---|
| 0–2 | Introduction + architecture |
| 2–3 | Login |
| 3–4 | Dashboard |
| 4–7 | Upload + vision pipeline (highlight) |
| 7–9 | Analysis + Predictions |
| 9–11 | Recommendations + AI Dietitian + PDF |
| 11–12 | AI chat |
| 12–13 | Nutrition Coach |
| 13–14 | History + Trends |
| 14–15 | Wrap-up + Q&A |

---

## Key facts to remember during the demo

- **149** backend tests pass; frontend type-checks and builds clean.
- **12** database tables; **27** API endpoints.
- **Models:** YOLOv8 (~22 MB), EfficientNet-B3 (~126 MB), 4 × XGBoost.
- **Nutrition DB:** 1,014 Indian dishes × 11 nutrients.
- **AI fail-safe:** missing key / timeout / bad JSON → `ai_dietitian: null`
  (never a 500).
- **Duplicate suppression:** per-class IoU filter with a 0.6 threshold.
- **Thresholds:** DCI 0.85/0.70/0.50; NIS 0.2/0.4/0.6/0.8 — deterministic,
  order-independent.
