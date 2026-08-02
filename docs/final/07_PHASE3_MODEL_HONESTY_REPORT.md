# Phase 3 — Model Honesty & Risk-Estimate Transparency Report

> **Scope.** This report documents the Phase 3 "model honesty" workstream:
> six fixes that make DietRiskNet present its ML outputs as what they are —
> **risk *estimates*** derived from partial inputs — rather than as
> diagnoses or measurements. Every fix is backed by a regression test, and
> the full pipeline was re-validated end-to-end with the real model weights.

---

## Summary

| # | Fix | Type | Status |
|---|---|---|---|
| 1 | DCI longitudinal semantics + missing-component Risk Fusion | Backend logic | ✅ Completed |
| 2 | XGBoost feature-order safety | Backend reliability | ✅ Completed |
| 3 | Terminology: "diagnostic" → "risk estimate" | Frontend + README | ✅ Completed |
| 4 | Risk-estimate transparency (disclaimers, null states, model-default inputs) | Frontend + docs | ✅ Completed |
| 5 | `MODEL_LIMITATIONS.md` | Documentation | ✅ Completed |
| 6 | Dead DCI/NIS parameter decision | Backend cleanup | ✅ Completed |
| — | Frontend null-DCI handling | Frontend | ✅ Completed |
| — | Backend tests + regressions | Tests | ✅ Completed |
| — | TypeScript / lint / build | Frontend CI | ✅ Completed |
| — | E2E pipeline validation (real models) | Validation | ✅ Completed |

---

## Fix 1 — DCI longitudinal semantics + missing-component Risk Fusion

### Problem
The Dietary Consistency Index (DCI) was computed from a single meal's macro
balance, which measures meal quality — not consistency. Worse, when no data
existed, the pipeline could fabricate "perfect health" default values.

### Change
- `DCIService.calculate` now computes DCI **longitudinally**: the coefficient
  of variation of total daily calories over the last 7 days, requiring at
  least **2 distinct valid days** (`backend/services/indices_services.py`).
  With fewer valid days, DCI is `None` + `"Insufficient Data"` — never a
  fabricated score.
- `RiskFusionService.fuse` now accepts `None` components and **renormalises
  the available components' weights proportionally** so the available weights
  sum to 1 — preserving the relative configured weights without substituting
  a default for the missing DCI/NIS (`backend/services/risk_fusion_service.py`).
  When no component is available it returns `(None, None)`.

### Tests
- `backend/tests/test_dci_longitudinal.py` — 8 cases: zero/one/same-day meals
  are unavailable; 2+ distinct valid days produce a score; zero-calorie days
  never establish history.
- `backend/tests/test_risk_fusion_regression.py` — 7 cases: full formula,
  all-None → `(None, None)`, DCI-missing renormalisation, "missing DCI is not
  perfect health", clamping, weights never mutated.

---

## Fix 2 — XGBoost feature-order safety

### Problem
XGBoost's `inplace_predict` (used by `predict_proba`) requires the inference
DataFrame columns to be in **exactly** `model.feature_names_in_` order; it
does not reorder by name and raises on a mismatch.

### Change
- `DiseasePredictionService._prepare_df` explicitly reorders the DataFrame to
  the trained column order and raises a clear internal `ValueError` listing any
  missing required feature — instead of silently misaligning a column
  (`backend/services/prediction_service.py`).

### Tests
- `backend/tests/test_xgboost_feature_order.py` — 4 unit cases (reorder,
  value preservation, missing-feature error, extra-column tolerance) + a
  real-model diabetes smoke test that survives the feature-order path.

---

## Fix 3 — Terminology: "diagnostic" → "risk estimate"

### Problem
The UI described itself as performing "diagnostics" / "diagnosis" of disease.
DietRiskNet does **not** diagnose; it estimates risk. Overclaiming language
was corrected app-wide while preserving the disclaimers that it is not a
medical diagnosis.

### Change (user-visible strings)
| Location | Before | After |
|---|---|---|
| Dashboard | "Real-Time Diagnostic Profiling" / "clinical disease risk calculations" | "Real-Time Risk Analytics" / "estimated disease risk" |
| Predictions | "Clinical Risk Forecasting" / "diagnostic forecasts" | "Estimated Disease Risk" / "risk estimates" |
| Upload | "Executing XGBoost … diagnostics" / "Execute Diagnostic Analysis" | "Estimating … risk" / "Run Risk Analysis" |
| Analysis | "Diagnostic Report" / "YOLO Diagnostic Canvas Overlay" | "Meal Analysis Report" / "YOLO Detection Canvas Overlay" |
| Profile | "Diagnostic Metric Vectors" / "Save Diagnostic Profile" | "Risk Assessment Inputs" / "Save Risk Profile" |
| History | "Diagnostic Indices" | "Risk & Consistency Indices" |
| Recommendations | "Diagnostic Derivation Logic" | "Risk-to-Recommendation Logic" |
| Research | "diagnostic disease-risk scoring" / "Fused Diagnostic Probability Matrix" | "Disease-risk estimation" / "Fused Risk Probability Matrix" |
| About | "diagnostic transparency" | "transparent, explainable disease-risk estimates" |
| README diagram | "Save diagnostic log to DB" | "Save analysis record to DB" |

Disclaimers were kept intentionally, e.g. the predictions page: *"Risk
estimates are AI-assisted indicators … They are not medical diagnoses."*

---

## Fix 4 — Risk-estimate transparency

- **Predictions page** now carries an explicit transparency note naming
  "profile, dietary, and **model-default** inputs" and stating the outputs are
  not medical diagnoses.
- **Null-state honesty**: everywhere a value is absent (no meals logged,
  insufficient longitudinal history, no recognised-food nutrition), the UI
  shows "No Data" / "Insufficient Data" / "N/A" rather than a fabricated zero.
- The predictions/profiles terminology reflects that many clinical model
  features are **model-defaults** (see `MODEL_LIMITATIONS.md` §4).

---

## Fix 5 — `MODEL_LIMITATIONS.md`

New root-level document covering the honest limits of every component:
vision pipeline (fixed 18/118 class vocabularies, portion-size estimation,
confidence ≠ correctness), nutrition database (static per-100g values,
`nutrition_available=false` semantics), XGBoost models (the full table of
hard-coded default inputs), DCI (needs ≥2 days, calories-only), NIS (generic
RDI, meal-level), risk fusion (fixed weights, mixed time scales,
missing-component renormalisation), the AI Dietitian (unverified LLM
narrative, fails-open), and operational bounds. It also lists the deliberate
honesty guards already built into the code. Referenced from `README.md`.

---

## Fix 6 — Dead DCI/NIS parameter decision

### Decision
The four XGBoost prediction models **never consume DCI or NIS** — those
indices feed only risk fusion and recommendations. The `dci`/`nis` parameters
on the prediction path were dead, and `DiseasePredictionRequest` required them
even though no prediction endpoint used them.

### Change
- Removed `dci`/`nis` from `DiseasePredictionService.predict_all` and from
  `DiseasePredictionRequest` (with a clarifying comment).
- Made `dci`/`nis` `Optional[float]` in `RiskFusionRequest` and
  `ExplainDietRequest` — DCI is null-able after Fix 1.
- Guarded `nis` in `ExplainDietService.recommend` (`nis is not None and …`).
- Updated all three `predict_all` callers (`meal.py`, `benchmark_pipeline.py`,
  `test_pipeline.py`). Pydantic ignores extra request fields by default, so
  the change is backward-compatible for any client still sending DCI/NIS.

---

## Frontend null-DCI handling

- **Dashboard**: `hasRiskData` / `hasDciData` / `hasNisData` guards render
  "Insufficient Data" / "N/A" / "No meals logged yet".
- **Analysis**: `dci != null` and `dci_level ?? 'Not Available'` handling.
- **Predictions**: `hasPredictions` guard with an "analyze a meal first" state.
- **History**: previously rendered null `risk_score` as "0%", null `risk_level`
  as "LOW", and null DCI as "0" — all now render "N/A" / "INSUFFICIENT DATA".
- **Trends**: recharts handles null DCI/NIS points as gaps (no fabrication).

---

## Validation results

| Check | Result |
|---|---|
| Backend pytest suite (189 tests) | ✅ **189 passed** (incl. 12 new regression tests) |
| XGBoost feature-order regression (real model) | ✅ passed |
| Risk Fusion renormalisation regression | ✅ passed |
| Frontend `tsc --noEmit` | ✅ no errors |
| Frontend ESLint | ✅ clean (2 pre-existing errors + 1 warning fixed) |
| Frontend `next build` | ✅ compiled, 17 routes prerendered |
| E2E pipeline (real YOLO + EfficientNet + XGBoost) | ✅ SUCCESS — all DB assertions correct |

### E2E evidence (real weights, `datasets/sample_meal.png`)
```
YOLOv8 detected 1 objects → Idli (Conf: 84.3%, Calories: 206 kcal)
DCI = N/A (Insufficient Data)      ← correct null on <2 longitudinal days
NIS = 0.32 (Mild Imbalance)
Diabetes: 0.0% | Obesity: 92.3% | Hypertension: 0.0% | Deficiency: 54.4%
Risk Fusion = 0.33 (Moderate)      ← DCI absent; remaining weights renormalised
SUCCESS: PIPELINE VERIFICATION PASSED. ALL DB ASSERTIONS CORRECT!
```

---

## Files changed in this phase

**Backend logic**
- `backend/services/indices_services.py` (DCI longitudinal) — pre-existing from earlier Phase 3; verified here
- `backend/services/risk_fusion_service.py` (missing-component fusion)
- `backend/services/prediction_service.py` (feature-order + FIX 6 signature)
- `backend/services/recommendation_service.py` (NIS null guard)
- `backend/schemas/schemas.py` (nullable DCI/NIS, FIX 6 request cleanup)
- `backend/routes/meal.py` (predict_all caller)

**Tests**
- `backend/tests/test_dci_longitudinal.py`
- `backend/tests/test_risk_fusion_regression.py` (new)
- `backend/tests/test_xgboost_feature_order.py` (new)
- `backend/tests/conftest.py` (new — idempotent schema creation)
- `backend/tests/test_pipeline.py` (updated caller)

**Frontend**
- `frontend/app/{dashboard,analysis,predictions,upload,history,profile,recommendations,research,about}/page.tsx`
- `frontend/components/Sidebar.tsx`, `frontend/components/analysis/AIDietitianCard.tsx`, `frontend/services/api.ts`

**Docs**
- `MODEL_LIMITATIONS.md` (new)
- `README.md` (limitations notice + diagram terminology)
- this report

---

## Notes & guardrails honoured

- **No model retraining** and **no model artifacts modified**.
- **Risk Fusion configured weights unchanged** — renormalisation preserves the
  relative configured weights.
- **No project data deleted**; tests run against an in-memory or temporary
  SQLite database.
- The `test_phase3_tmp.db` scratch database created during validation is
  removed after each run.
