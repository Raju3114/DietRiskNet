# 07 — Methodology

This chapter explains each component of the implemented system and how
it maps to the repository.

---

## 7.1 Food Detection — YOLOv8

**Model**: Ultralytics YOLOv8 (`DietRiskNet_FoodDetector_YOLOv8.pt`, 18
detection classes).

The detector localises food regions in a meal photograph and outputs
bounding boxes `(x1, y1, x2, y2)` with confidence scores. Detections are
post-processed by a per-class IoU filter (`FoodDetectionService`
`_remove_duplicate_detections`) that suppresses highly overlapping
boxes of the same class (IoU > 0.6), keeping the highest-confidence
detection. This prevents a single dish from being counted twice.

**Files**: `backend/services/ml_services.py`, `backend/utils/image_utils.py`.

## 7.2 Food Classification — EfficientNet-B3

**Model**: `DietRiskNet_FoodClassifier_EfficientNetB3.pth` (118 food
classes, fallback to the B0 variant if the B3 file is absent).

Each detected crop is resized and classified by the EfficientNet
convolutional network, producing a food class label and confidence.
The classifier exposes an internal `crop_size` (300 for B3, 224 for B0).

**Files**: `backend/services/ml_services.py`, `backend/trained_models/efficientnet_classes.json`.

## 7.3 Nutrition Lookup

A CSV database of **1,014 Indian dishes × 11 nutrients** is loaded once
into memory (`nutrition_service`). Lookup uses four priority tiers:

1. exact dish-name match
2. alias / synonym map (classifier output → CSV dish)
3. deterministic name normalisation
4. fuzzy matching (`difflib`)

Per-item nutrients are scaled by a serving weight
(`DEFAULT_SERVING_WEIGHTS`, default 100 g) and aggregated per meal. A
`display_name` field maps redundant modifiers (e.g. "Vegetable samosa" →
"Samosa") for a cleaner UI while preserving the original name.

**Files**: `backend/services/nutrition_service.py`, `nutrition/indian_food_nutrition_processed.csv`.

## 7.4 Dietary Consistency Index (DCI)

DCI measures how consistent a user's intake is over the last 7 days:

- If ≥ 2 days of history exist: `DCI = 1 − CV` where `CV` is the
  coefficient of variation of daily calories.
- Otherwise: a single-meal macro-balance score against a
  55% carbs / 15% protein / 30% fat target.

The score is classified into `High / Moderate / Low / Very Low`
Consistency via a deterministic **threshold-based classifier**
(`classification.py`) — the replacement for the earlier interval-range
approach, which was order-dependent and ambiguous at boundaries.

**Files**: `backend/services/indices_services.py`, `backend/services/classification.py`, `backend/trained_models/DietRiskNet_DCI_Config.json`.

## 7.5 Nutritional Imbalance Score (NIS)

NIS is the mean relative deviation of the meal from recommended daily
intakes (RDI) across six key nutrients:

```
NIS = mean( |actual_i − RDI_i| / RDI_i )
```

The score is mapped to `Balanced Diet / Mild / Moderate / High / Severe
Imbalance` using the same threshold classifier.

**Files**: `backend/services/indices_services.py`, `backend/trained_models/DietRiskNet_NIS_Config.json`.

## 7.6 Disease-Risk Prediction — XGBoost

Four independent XGBoost classifiers predict risk probabilities:

| Model | Inputs (engineered) |
|-------|---------------------|
| Diabetes | age, gender, BMI, hypertension / heart-disease history, HbA1c, glucose |
| Obesity | age, gender, height, weight, BMI, dietary habits (FAVC/FCVC/NCP/CAEC/FAF/TUE) |
| Hypertension | age, BMI, sodium, stress, sleep, medication, exercise, smoking |
| Deficiency | age, gender, BMI, RDA percentages, hemoglobin |

A `predict_all` wrapper computes BMI and runs all four models, returning
`{diabetes_risk, obesity_risk, hypertension_risk, deficiency_risk}`.

**Files**: `backend/services/prediction_service.py`, `backend/trained_models/*_XGBoost.pkl`.

## 7.7 Risk Fusion

The four risks plus DCI/NIS are combined by a weighted formula:

```
Fused = 0.25·(1−DCI) + 0.25·NIS + 0.20·diabetes
      + 0.15·obesity + 0.10·hypertension + 0.05·deficiency
```

The result maps to `Low / Moderate / High / Critical` risk, based on the
deployed boundaries in `risk_fusion_service.py`:
`score ≤ 0.25 → Low`, `0.25 < score ≤ 0.50 → Moderate`,
`0.50 < score ≤ 0.75 → High`, `score > 0.75 → Critical`.
Only *available* components participate: a missing component (e.g. DCI with
insufficient history) contributes no value and the remaining weights are
renormalised proportionally so the fused score stays on `[0, 1]`.

**Files**: `backend/services/risk_fusion_service.py`, `backend/trained_models/DietRiskNet_RiskFusion_Config.json`.

## 7.8 ExplainDiet — Rule Engine

Threshold-triggered, explainable recommendations. Rules fire on
sodium / sugar / calories / fiber plus risk scores (e.g. `sodium > 800
mg` or `hypertension_risk > 0.4` → "Reduce salt"). A fallback
"Excellent meal balance!" fires when nothing is flagged.

**Files**: `backend/services/recommendation_service.py`.

## 7.9 AI Dietitian — LLM Explanation Layer

The AI Dietitian (served by **Ollama by default**, or **Gemini optionally**)
is an **add-on explanation layer**. It
receives ONLY the structured output of the ML pipeline:

```
foods, nutrition, dci, nis, predictions, fusion,
rule recommendations, user profile
```

It returns a structured JSON response (summary, meal quality,
risk explanation, recommendations, healthier alternatives, warnings,
follow-up questions). The **health score is computed deterministically
by the backend** (`health_score_service`), never by the LLM.

- **Provider abstraction**: `BaseLLMProvider` interface implemented by
  `OllamaProvider` (default, local) and `GeminiProvider` (optional,
  cloud), selected by `LLMProviderFactory` — OpenAI/Claude/Azure OpenAI
  can be added without changing business logic.
- **Safety prompt**: never invents diagnoses, never contradicts backend
  predictions, recommends consulting professionals.
- **Failure mode**: missing key / timeout / bad JSON → `ai_dietitian =
  null`; the rule-based output stands.

**Files**: `backend/services/meal_ai_service.py`, `backend/services/health_score_service.py`, `backend/services/llm/*`, `backend/prompts/dietitian_prompt.py`.

## 7.10 AI Result Caching

`AIDietitianResult` persists every AI response, keyed by a stable SHA-256
`context_hash` of the full input context (foods, nutrition, DCI, NIS,
predictions, fusion, rule recs, user profile). If nothing changes, the
LLM is never called again. `prompt_version` provides logical cache
busting; `provider` + `model` columns make the cache provider-agnostic.

**Files**: `backend/services/ai_cache_service.py`, `backend/models/ai_dietitian.py`.

## 7.11 AI Chat

A meal-specific assistant (`ChatAIService`) loads the persisted analysis,
keeps an in-memory rolling history (max 10 messages) per
`(user, meal)` session, and answers via the LLM. No ML is re-run, no
conversation is persisted to the database.

**Files**: `backend/services/chat_ai_service.py`, `backend/routes/ai_chat.py`.

## 7.12 PDF Report

`ReportService` renders the meal analysis into a professional PDF using
ReportLab platypus (automatic page breaks): meal image, detected foods,
nutrition summary, health analysis, AI Dietitian section, and a
"Generated by DietRiskNet" footer with timestamp.

**Files**: `backend/services/report_service.py`, `backend/routes/report.py`.

## 7.13 Evaluation

A benchmarking module (`backend/evaluation/`) times every stage,
computes mean/median/p95, memory and CPU metrics, and emits CSV, JSON,
matplotlib charts, and dissertation-ready markdown tables.

**Files**: `backend/evaluation/*`, `docs/evaluation.md`.

## 7.14 AI Nutrition Assistant

A general-purpose conversational assistant for nutrition, meal
planning, healthy eating, hydration, grocery lists, and cooking advice.
Unlike the meal-specific AI chat, it works even when no meal has been
analysed, and it answers questions such as:

- Meal planning (breakfast ideas, weekly plans, vegetarian, weight-loss,
  muscle-gain)
- Nutrition education (protein, carbohydrates, vitamins, calories,
  fiber)
- Disease-specific advice (diabetes, hypertension, cholesterol,
  kidney-friendly, heart-healthy)
- Healthy alternatives, hydration, grocery lists, cooking methods

**Personalisation**: when the user has meal history, the service reads
the PERSISTED analysis (recent foods, nutrition, DCI, NIS, disease
risks) from the database and includes it in the context — it never
re-runs YOLO, EfficientNet, nutrition, or prediction.

**Out of scope**: obvious off-topic questions (politics, programming,
movies, sports, homework) are intercepted by a lightweight keyword guard
and answered with a polite canned reply, avoiding an unnecessary LLM
call.

**Reuse**: the assistant reuses the `LLMClient` provider abstraction,
the shared `ConversationStore` (rolling 10-message memory), the typed
`LLMProviderError` failure handling, and the prompt-versioning /
logging conventions.

**Files**: `backend/services/nutrition_assistant_service.py`,
`backend/services/conversation_store.py`,
`backend/prompts/nutrition_assistant_prompt.txt`,
`backend/routes/nutrition_chat.py`.

## 7.15 Personalized AI Nutrition Coach

The Nutrition Assistant is enhanced into a personalised coach by adding a
deterministic analytics layer over the user's stored meal history.

**`NutritionAnalyticsService`** aggregates the last 14 analysed meals and
computes, without any ML re-run or LLM call:

- **Averages**: calories, protein, carbohydrates, fat, sodium, fiber, DCI, NIS
- **Weekly view**: number of meals analysed and meals in the last 7 days
- **Risk summary**: the highest predicted disease risk across recent meals
- **Best / worst meal** (by DCI / NIS) and the **most common food**
- **Patterns**: e.g. "You have consumed high sodium in 4 of your last 5
  meals", low protein, low fiber, infrequent vegetables, hydration reminder
- **Trends**: DCI improvement/decline and the largest risk trend across
  the analysis window
- **Smart goals**: sodium reduction, protein/fiber increase, consistency,
  balance, hydration — each with a 0–1 progress score and an
  on-track / in-progress / needs-attention status
- **Positive habits** and **areas to improve**

The coach summary is injected into the chat context (via
`NutritionAssistantService`), so every answer is personalised from
historical data. A `GET /api/nutrition/analytics` endpoint exposes the
same deterministic analytics to the frontend dashboard.

**Files**: `backend/services/nutrition_analytics_service.py`,
`backend/routes/nutrition_coach.py`.

## 7.16 LLM Provider Layer — Ollama default, Gemini optional

All AI features are provider-agnostic through a single interface.

- **`BaseLLMProvider`** (`backend/services/llm/base.py`) defines
  `enabled`, `generate_json()`, `chat()`, `generate()`, `health_check()`.
  `LLMClient` is kept as a backward-compatible alias.
- **`OllamaProvider`** (default) talks to a **local Ollama server**
  (`http://localhost:11434`) over its REST API. **No API key is required**
  — the application works fully offline with a local model (default
  `llama3.2:3b`).
- **`GeminiProvider`** (optional cloud) requires `GEMINI_API_KEY` and
  remains fully supported behind the same interface.
- **`LLMProviderFactory`** (`backend/services/llm/factory.py`) selects the
  provider from `LLM_PROVIDER` (`ollama` default, `gemini` optional).
  When `gemini` is selected and Gemini fails, a **`FallbackLLMProvider`**
  automatically retries the request against local Ollama.
- **`GET /api/ai/health`** reports the active provider, model, status,
  latency, and version without authentication.
- Failure behaviour is identical for every provider: an unavailable LLM
  degrades to `ai_dietitian: null`, a friendly chat reply, or rule-based
  output — **never an HTTP 500**.

**Files**: `backend/services/llm/base.py`, `backend/services/llm/ollama_provider.py`,
`backend/services/llm/gemini_client.py`, `backend/services/llm/factory.py`,
`backend/routes/ai_chat.py`.
