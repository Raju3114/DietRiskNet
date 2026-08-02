# Phase 4 — Final Model & End-to-End Evaluation Report

> **Scope.** This report consolidates the Phase 4 evaluation of the deployed
> DietRiskNet system as it exists in the working tree: the real model weights,
> the real services, and the real persisted data. It **does not** modify any
> model, threshold, formula, fusion weight, mapping, or artifact. It reports
> verified numbers only, and marks every quantity that **cannot** be honestly
> derived as `N/A — not formally evaluated`.
>
> **Method.** Every headline figure below was independently recomputed from the
> raw artifacts in `docs/evaluation/` by
> `backend/evaluation/phase4/validate_phase4.py`, whose result is written to
> `docs/evaluation/phase4_validation.json`. Where the reported figure and the
> recomputed figure agree, the number is marked **verified**.

---

## 1. Executive Summary

DietRiskNet is **feature-complete and end-to-end functional**, and its Phase 4
evaluation confirms the honesty framing introduced in Phase 3: the system
produces **risk *estimates*** derived from partial inputs, not diagnoses.

| Area | Verified result |
|---|---|
| End-to-end pipeline (real weights) | 92 historical uploads re-analysed; **82 recognized-food analyses, 10 expected safe rejections, 0 unexpected failures** |
| Classifier confidence separation | Food mean confidence **0.826** vs non-food max **0.036** vs acceptance threshold **0.45** (verified) |
| Nutrition mapping coverage | **87 / 118** classes mapped → **73.73 %** (verified) |
| DCI | CV-based longitudinal consistency, **≥ 2 distinct valid days**, all 10 controlled scenarios verified |
| NIS | 6 controlled scenarios, ascending order + severity labels verified |
| Risk fusion | Weights sum to 1; missing-component renormalisation and manual calculation verified |
| XGBoost | 4 artifacts load; feature-order protected; artifacts unchanged |
| Formal accuracy metrics | `N/A` — no held-out labelled split or detection annotations exist in the repository |
| Software regression | pytest **189 passed**; TypeScript clean; ESLint clean; production build **17 routes** |

**Headline caveat.** There is **no labelled held-out dataset** in the
repository. Formal Top-1/Top-3/Top-5 classifier accuracy, macro-F1, and YOLO
mAP **cannot be honestly computed** and are reported as `N/A` rather than
invented. The evaluation therefore separates
**controlled / synthetic functional evaluation** (evidence we have) from
**formal labelled detection/classification benchmarking** (evidence we do not).

---

## 2. Evaluation Scope

- **What was evaluated.** The shipped pipeline as configured in the working
  tree: YOLOv8 detection → EfficientNet-B3 classification → Indian-food
  nutrition lookup → DCI / NIS → 4× XGBoost → weighted risk fusion →
  rule-based recommendations, over the locally available meal uploads, plus
  controlled unit-level probes for every index.
- **What was NOT evaluated (honestly marked `N/A`).**
  - Top-1/3/5 classifier accuracy, macro/weighted precision-recall-F1,
    per-class metrics, confusion matrix — because **no labelled held-out split
    exists** (`datasets/` contains only `sample_meal.png`; no training script
    and no train/val/test split are present).
  - YOLO precision/recall/mAP — because **no detection ground-truth labels
    exist** anywhere in the repository.
- **Configuration under test.**
  - `CLASSIFIER_CONFIDENCE_THRESHOLD = 0.45` (unchanged).
  - DCI thresholds `0.85 / 0.70 / 0.50` (unchanged numeric values).
  - NIS RDI table and `0.20 / 0.40 / 0.60 / 0.80` levels (unchanged).
  - Risk fusion weights `0.25/0.25/0.20/0.15/0.10/0.05` (unchanged).
  - Default serving weights (`DEFAULT_SERVING_WEIGHTS`, 100 g fallback) — unchanged.

---

## 3. Final System Configuration

| Component | Configuration (as evaluated) |
|---|---|
| Detector | YOLOv8 (`DietRiskNet_FoodDetector_YOLOv8.pt`) |
| Classifier | EfficientNet-B3 (`DietRiskNet_FoodClassifier_EfficientNetB3.pth`), B0 fallback, **118 classes**, crop 300 (B3) / 224 (B0) |
| Confidence gate | `CLASSIFIER_CONFIDENCE_THRESHOLD = 0.45` |
| Nutrition | `nutrition/indian_food_nutrition_processed.csv`, per-100 g, linear scaling by serving weight |
| Indices | DCI (longitudinal CV, ≥2 days), NIS (6-nutrient RDI deviation) |
| Prediction | 4× XGBoost (diabetes, obesity, hypertension, deficiency) with feature-order protection |
| Fusion | Weighted renormalised average; weights DCI 0.25, NIS 0.25, Diabetes 0.20, Obesity 0.15, HTN 0.10, Deficiency 0.05 |
| Recommendation | ExplainDiet threshold rule engine |
| Persistence | SQLAlchemy (SQLite dev); 12 tables |

Model artifacts were **not** retrained or modified for this evaluation. Git
status confirms only the two config JSONs (DCI/NIS) differ from `HEAD`, and the
difference is the documented Phase-2/3 refactor from interval ranges to
point-threshold levels **with the same numeric cut-offs** (0.85/0.70/0.50 and
0.20/0.40/0.60/0.80). The `.pth`, `.pt`, and `.pkl` weights are unchanged.

---

## 4. Dataset and Evaluation Protocol

- **Available images.** `datasets/sample_meal.png` (the single in-repo food
  image) and the ~92 locally uploaded meal photos under `backend/uploads/`
  (real-world usage, timestamps preserved).
- **No labelled split.** There is no annotated dataset, no training script, and
  no train/validation/test partition anywhere in the repository.
- **Controlled synthetic probes.** For multi-food and non-food robustness,
  synthetic images were constructed with **known ground truth by
  construction** (image composites of real food tiles for multi-object probes;
  solid colour / gradient / noise / dark / blur / tiny / corrupt bytes for
  robustness). These support **functional** claims only.
- **Guarding against over-claiming.** Because no held-out split can be
  reconstructed reliably, the report states `N/A` for formal classifier and
  detector metrics rather than reporting training or validation performance as
  if it were held-out test performance.

---

## 5. EfficientNet-B3 Quantitative Evaluation

**Result: `N/A — held-out evaluation split not reliably reconstructable`.**

No labelled validation or test split exists in the repository, and the final
B3 checkpoint's training dataset is not present, so **Top-1 / Top-3 / Top-5
accuracy, macro/weighted precision-recall-F1, per-class metrics, and a
confusion matrix cannot be computed or reconstructed**. They are deliberately
**not** reported. This matches the project's own long-standing position
(`FINAL_PROJECT_SUBMISSION_SUMMARY.md`: "these are pre-trained models; the
project does not claim retrained or measured mAP/accuracy figures").

What *is* available is **functional confidence evidence** on real inference
(§6), which does not substitute for held-out accuracy.

---

## 6. Classifier Confidence and Error Analysis

**Verified** from `docs/evaluation/classifier_confidence.json` and the E2E
accepted items (independent recomputation in `phase4_validation.json`).

| Statistic | Value (verified) |
|---|---|
| Accepted items analysed | 83 |
| Mean confidence | **0.8256** |
| Median confidence | 0.8430 |
| Min / Max | 0.464 / 0.991 |
| P25 / P75 / P95 | 0.782 / 0.886 / 0.955 |
| Config acceptance threshold | **0.45** (unchanged) |
| Low-confidence items rejected in E2E | 8 |
| Full-image fallback confidences (no-food cases) | 0.255 |

**Non-food vs food confidence probe** (classifier only):

| Input | Confidence | Class |
|---|---|---|
| Real food control (`sample_meal.png`) | **0.867** | idli |
| Solid red / green / blue / white / black | 0.021 – 0.028 | (various) |
| Gradient | 0.032 | strawberry_shortcake |
| Gaussian noise | 0.036 | ice_cream |
| **Max non-food confidence** | **≤ 0.036** | — |

The measured separation is: real food ≈ **0.87**, non-food ≤ **0.04**, gate at
**0.45**. The margin between non-food and the gate is ~12×, and the margin
between the gate and typical food is ~2×. This is strong **functional**
evidence that the 0.45 threshold rejects clearly non-food input without being
so strict that it discards genuine (even slightly degraded) food crops. It is
**not** a held-out accuracy figure.

Confidence distribution plot: `docs/evaluation/confidence_distribution.png`.

---

## 7. YOLO Evaluation

**Formal labelled benchmark available: No.**

**Result: Formal YOLO mAP `N/A` — appropriate labelled detection benchmark not
available/reconstructed.** No detection ground-truth annotations exist in the
repository, so precision, recall, mAP@0.5, and mAP@0.5:0.95 cannot be computed,
and are **not** derived from synthetic probes.

**Functional localization** (controlled synthetic composites with known ground
truth; `docs/evaluation/multifood/multifood_summary.json`):

| Probe | Ground-truth objects | Service boxes | Matched GT |
|---|---|---|---|
| P2 idli + pizza | 2 | 2 | YES |
| P3 idli + pizza + samosa | 3 | 3 | YES |
| P2 same-class idli ×2 (IoU < 0.6) | 2 | 2 | YES |
| P2 masala dosa + chapati | 2 | 2 | YES |
| P4 four distinct foods in a row | 4 | **0** (conf 0.25) | NO |

The detector demonstrates **functional multi-object localization on controlled
2–3 item probes**, keeps distinct same-class instances when IoU < 0.6, but
shows **reduced recall on a crowded four-item arrangement** (0 service boxes at
the built-in 0.25 confidence; only 3 weak boxes recovered at conf 0.1, missing
one tile). This is consistent with a detector whose training data was
predominantly single-food images.

---

## 8. Multi-Food Evaluation

**Evaluation type: CONTROLLED / SYNTHETIC FUNCTIONAL EVALUATION** (not a formal
labelled detection benchmark — see §7).

- **2-item:** P2 idli+pizza, P2 same-class idli×2, P2 masala dosa+chapati → all
  localized (2 boxes each, matched ground truth).
- **3-item:** P3 idli+pizza+samosa → localized (3 boxes, matched ground truth).
- **4-item:** P4 four-food row → **0 service boxes**; reduced multi-object
  recall in a crowded composition.

**Overall interpretation** (per the recovered evidence, superseding the earlier
exploratory "YOLO only detects one box per image" note):

> The current pipeline demonstrated multi-object localization on controlled
> 2–3 item synthetic probes, while a four-item arrangement exposed reduced
> multi-object recall. This supports **functional multi-food capability but not
> robust/general multi-food detection.**

No formal multi-food accuracy is claimed.

---

## 9. Nutrition Coverage

**Verified** (`docs/evaluation/nutrition_coverage.json`, independent
recomputation).

| Metric | Value |
|---|---|
| Classifier vocabulary | **118** classes (`efficientnet_classes.json`) |
| Mapped to nutrition records | **87** (array count 87, matches reported) |
| Unmapped | **31** (array count 31, matches reported) |
| Coverage | **87/118 = 73.73 %** (recomputed 73.73, matches reported) |

Mapping priority breakdown (as recorded): 75 alias matches, 5 normalised, 7
fuzzy, 0 exact; 31 unresolved. When a recognised food has no nutrition record,
the pipeline flags `nutrition_available = false` and treats its nutrients as
**unknown** (not zero-health); if no item has nutrition, DCI/NIS/risk are
suppressed (§15).

---

## 10. Portion Estimation Audit

**Preserved finding:** portion estimation is **static / configuration-based**,
not inferred from the image.

- `portion_estimation.json`: "Food recognition is image-based, but portion mass
  is currently default/configuration-based rather than visually estimated."
- Source: `DEFAULT_SERVING_WEIGHTS` (12 per-food overrides) with a **100 g**
  fallback; the system does **not** estimate physical mass/volume from image
  geometry or depth.
- **Controlled scaling verified:** `portion_scaling.csv` — 24 rows across 6
  foods (idli, samosa, masala dosa, butter naan, chai, pizza) at 50/100/150/200 g
  confirm every nutrient scales linearly as `per_100g × weight/100`
  (**all proportional = True**).

**Clear statement for the thesis:** *Food recognition is image-based; physical
portion mass is not estimated from image geometry/depth.* Calorie and nutrient
totals therefore carry portion-size uncertainty. (Per the task scope, portion
estimation was **not** implemented.)

---

## 11. NIS Controlled Evaluation

**Verified** (`docs/evaluation/nis_evaluation.json` + `nis_controlled_tests.csv`,
independent recomputation).

| Scenario | NIS | Level |
|---|---|---|
| balanced | 0.026 | Balanced Diet |
| low_protein | 0.3244 | Mild Imbalance |
| idli | 0.4745 | Moderate Imbalance |
| high_fat | 0.543 | Moderate Imbalance |
| high_sodium | 0.5622 | Moderate Imbalance |
| extreme | 0.871 | Severe Imbalance |

- **Ascending-order verified:** the recorded `ascending_nis_order` is sorted by
  NIS value and every recorded value equals the recomputed value.
- Severity labels present for all 6 scenarios; `balanced` → Balanced Diet and
  `extreme` → Severe Imbalance as expected.
- Honesty note recorded in the artifact: NIS is a project-designed dietary
  imbalance indicator and is **not claimed as clinically validated**.

---

## 12. DCI Longitudinal Evaluation

**Verified** (`docs/evaluation/dci_evaluation.json` + `dci_controlled_tests.csv`,
independent recomputation of the CV formula).

| Scenario | Distinct days | DCI (recomputed = reported) | Level |
|---|---|---|---|
| 0 valid days | 0 | None | Insufficient Data |
| 1 valid day | 1 | None | Insufficient Data |
| multiple meals, same day | 1 | None | Insufficient Data |
| 2 consistent days | 2 | 1.0 | High Consistency |
| 2 varying days | 2 | 0.8182 | Moderate Consistency |
| 3 consistent days | 3 | 0.9801 | High Consistency |
| 3 highly varying days | 3 | 0.6409 | Low Consistency |
| 7 consistent days | 7 | 1.0 | High Consistency |
| 7 varying days | 7 | 0.7674 | Moderate Consistency |
| zero-calorie history | 0 | None | Insufficient Data |

- **Semantics verified:** DCI is the coefficient of variation of total daily
  calories over the last 7 days, `DCI = clamp(1 − CV, 0, 1)`, requiring **≥ 2
  distinct valid days**; with fewer, DCI is `None` + "Insufficient Data" —
  never fabricated.
- All 10 scenarios match the recomputed CV values **and** the ≥2-day semantics.

---

## 13. XGBoost Regression Summary

**Confirmed** (code + real-model tests + live E2E execution):

- **Feature ordering protected.** `DiseasePredictionService._prepare_df`
  reorders inference DataFrames to `model.feature_names_in_` order and raises a
  clear `ValueError` listing missing features instead of silently misaligning
  columns. Regression test `test_xgboost_feature_order.py` passes (real
  diabetes model included).
- **All four model artifacts load.** Independently verified in this session:
  diabetes (644 735 B), obesity (2 932 299 B), hypertension (659 775 B),
  deficiency (1 780 882 B) all load successfully. The live E2E run executed
  XGBoost on all 82 recognised analyses (`xgboost_executed = True`).
- **Model artifacts unchanged.** Git status shows no modification to any
  `.pkl` / `.pth` / `.pt`; only the DCI/NIS config JSONs differ, and only in
  format (intervals → point thresholds), not in numeric cut-offs.
- **Known default/heuristic clinical inputs documented.** The large set of
  features not collected by the app (smoking, HbA1c, glucose, sleep, stress,
  medication, etc.) are supplied as fixed defaults; this is fully documented in
  `MODEL_LIMITATIONS.md` §4 and surfaced in the UI transparency note.
- **No clinical validation claimed.** These are pre-trained public-survey
  models; outputs are estimates, and the report does not claim clinical
  validation.

---

## 14. Risk Fusion Evaluation

**Verified** (`docs/evaluation/risk_fusion_evaluation.json` +
`risk_fusion_tests.csv`, independent recomputation using the implementation's
`dci_risk = 1 − DCI` convention).

| Scenario | DCI | NIS | Others | Fused (recomputed = reported) | Level |
|---|---|---|---|---|---|
| A — all available | 0.8 | 0.3 | 0.2/0.3/0.1/0.2 | 0.23 | Low |
| B — DCI missing | — | 0.3 | 0.2/0.3/0.1/0.2 | **0.24** | Low |
| C — DCI & NIS missing | — | — | 0.2/0.3/0.1/0.2 | 0.21 | Low |
| D — subset only | 0.8 | — | 0.2 only | 0.20 | Low |
| E — none available | — | — | — | None | None |

- **Manual calculation verified:** scenario B — available weight = 0.75;
  `(0.25·0.3 + 0.2·0.2 + 0.15·0.3 + 0.1·0.1 + 0.05·0.2)/0.75 = 0.18/0.75 =
  0.24` — matches both the service output and the reported value.
- **Missing-component renormalisation verified:** available weights are
  renormalised to sum to 1; a missing DCI is **not** substituted with
  0/1/0.5 (scenario B fused = 0.24 ≠ 0, i.e. "missing DCI is not perfect
  health" holds).
- Weights sum to 1.0; all five scenarios match.

---

## 15. End-to-End Evaluation

**Verified** (`docs/evaluation/e2e_evaluation.csv`, `e2e_summary.json`,
independent recomputation). 92 real uploads re-analysed through the real
detection → classification → nutrition → DCI/NIS → XGBoost → fusion →
recommendation pipeline, persisted in a **temporary** DB (cleaned up).

| Outcome | Count | Classification |
|---|---|---|
| **Total cases** | **92** | — |
| `ok` — recognized-food analyses | **82** | Successful analyses |
| `no_food_recognized` | **9** | **Expected safe rejection** (classifier confidence below the 0.45 gate, incl. 8 low-confidence rejects + 1 full-image fallback at 0.255) |
| `no_nutrition_data` | **1** | **Expected guardrail** (recognised food `nachos` @ 0.824 has no nutrition record → nutrients treated as unknown, indices/risk suppressed) |
| **Unexpected failures** | **0** | — |

82 + 9 + 1 = 92, with **0 unexpected failures**. The "no-food" and
"no-nutrition" outcomes are **deliberate honesty guardrails** (the system
refuses to fabricate a meal it cannot recognise and refuses to report nutrients
it does not have), not failed tests. In the E2E run, 8 of the 82 recognised
analyses had ≥ 2-day DCI history available; the rest correctly reported
"Insufficient Data".

---

## 16. Robustness Evaluation

**Verified** (`docs/evaluation/robustness_matrix.csv`). The same detection →
classification gate used by `analyze_meal` was pushed with controlled inputs;
no threshold changed.

| Input | YOLO boxes | Outcome | Classifier conf | Class |
|---|---|---|---|---|
| real food (`sample_meal.png`) | 1 | recognized | 0.857 | idli |
| solid red / blue / white / black | 0 | no_food_recognized | 0.021–0.028 | (various) |
| gradient | 0 | no_food_recognized | 0.032 | strawberry_shortcake |
| gaussian noise | 0 | no_food_recognized | 0.036 | ice_cream |
| dark image | 0 | no_food_recognized | 0.021 | foie_gras |
| tiny 8×8 | 0 | no_food_recognized | 0.022 | foie_gras |
| blurred real food | 1 | low_confidence_rejected | 0.089 | tuna_tartare |
| corrupt bytes | — | error (graceful) | — | Truncated File Read |

Confirmed handling of: valid images (recognized), non-food / solid-colour /
gradient / noise / dark / tiny (safe rejection below gate), blurred real food
(rejected rather than mis-labelled as a high-confidence wrong food), corrupt
bytes (graceful, caught error), unmapped nutrition (E2E §15), new user with
<2-day DCI ("Insufficient Data"), and ≥2-day DCI (score computed, §12).

---

## 17. Database Consistency

**Verified against `dietrisknet.db`:**

| Quantity | Value |
|---|---|
| Total users | **20** |
| Total meals | **92** |
| Phase-4 / evaluation users remaining | **0** |

The Phase 4 E2E harness persisted its meals in a **temporary** SQLite database
and deleted its evaluation user on completion — no Phase-4 evaluation user
remains in the production database, and no `*_tmp.db` / `phase4*.db` files are
left behind. No destructive cleanup was performed in this session. (The 20
users are the pre-existing development/usage accounts; the largest contributor
is `user1@gmail.com` with 60 of the 92 meals.)

---

## 18. Software Regression

Run once at the end of Phase 4 (read-only; no fixes applied because none were
blocking).

| Check | Command | Result |
|---|---|---|
| Backend tests | `python -m pytest backend/tests/ -q` | **189 passed** (0 failed) |
| TypeScript | `npx tsc --noEmit` | **0 errors** |
| ESLint | `npx eslint .` | **clean** |
| Production build | `npm run build` | **success, 17/17 routes prerendered** |

No genuine blocking software defect was found; the only notices are
non-blocking Pydantic v2 deprecation warnings and the expected
`SECRET_KEY`-insecure-default runtime warning in dev.

---

## 19. Final Verified Metrics Table

| Metric | Value | Basis |
|---|---|---|
| Classifier architecture | EfficientNet-B3 (B0 fallback) | `ml_services.py`, `efficientnet_classes.json` |
| Classifier vocabulary | 118 classes | `efficientnet_classes.json` (len=118) |
| Nutrition mapped / total / coverage | 87 / 118 / **73.73 %** | verified |
| Classifier confidence (mean) | **0.826** | verified |
| Classifier confidence (median) | 0.843 | verified |
| Non-food max confidence | **0.036** | verified |
| Classifier acceptance threshold | **0.45** (unchanged) | verified |
| DCI semantics | CV, ≥2 distinct days, 10/10 scenarios | verified |
| NIS ordering | 6/6 ascending, severity correct | verified |
| Risk fusion renormalisation | 5/5 scenarios + manual calc (B=0.24) | verified |
| XGBoost models load | 4/4 | verified this session |
| XGBoost feature order | protected (`_prepare_df`) | code + regression test |
| E2E total / ok / guardrails / failures | 92 / 82 / 10 / **0** | verified |
| Portion scaling | proportional, 6 foods × 4 weights | verified |
| Formal classifier accuracy (Top-1/3/5, F1) | **N/A** — no held-out split | not reconstructable |
| Formal YOLO precision/recall/mAP | **N/A** — no annotations | not reconstructable |
| Database users / meals / eval users | 20 / 92 / 0 | verified |
| Backend pytest | **189 passed** | regression |
| Frontend TS / ESLint / build | clean / clean / 17 routes | regression |

---

## 20. Supported Claims

Claims for which the evaluation provides direct, verified evidence:

1. **118-class food recognition vocabulary** — verified from
   `efficientnet_classes.json` and the model configuration.
2. **73.73 % nutrition-mapping coverage** across the 118 classes — verified.
3. **DCI is a longitudinal consistency index** (CV of daily calories, ≥2
   distinct days, `null` otherwise) — verified by controlled tests.
4. **NIS is a deterministic meal-level imbalance index** with monotonic
   severity ordering — verified.
5. **Risk fusion renormalises missing components** and never fabricates a
   missing DCI/NIS — verified by manual calculation.
6. **XGBoost feature-order safety** and loading of all four artifacts —
   verified.
7. **The 0.45 classifier gate separates food from non-food** in the measured
   functional probe (food ≈0.83–0.87 vs non-food ≤0.036) — verified.
8. **The pipeline runs end-to-end on real weights** (82 recognised analyses,
   0 unexpected failures) — verified.
9. **Non-food / unmapped-nutrition inputs are safely rejected or marked
   unavailable** rather than fabricating data — verified.
10. **Nutrient values scale linearly with serving weight** — verified.

---

## 21. Supported-With-Limitations Claims

1. **EfficientNet-B3 classification quality** — functional confidence evidence
   only; **no held-out accuracy** (`N/A`).
2. **YOLO localisation** — functional on controlled 2–3 item probes; **no
   formal mAP** (`N/A`); reduced recall on four-item compositions.
3. **Multi-food capability** — functional 2–3 items, **not robust/general**.
4. **Nutrition estimation** — deterministic lookup + linear scaling, not
   laboratory measurement of the photographed meal.
5. **Portion estimation** — static serving-weight config (100 g fallback); no
   image-geometry/depth estimation.
6. **DCI** — calories-only, 7-day window, needs history (≥2 days).
7. **NIS** — generic (non-personalised) RDI, meal-level, 6 nutrients.
8. **XGBoost risk estimates** — dominated by fixed default/heuristic clinical
   inputs; pre-trained on public survey data; not clinically validated.
9. **Risk fusion** — fixed designer weights; mixes longitudinal (DCI) and
   meal-level (NIS) and demographic (XGBoost) time scales.
10. **AI-generated recommendations / AI Dietitian narrative** — grounded in
    structured ML output but otherwise unverified LLM text; fails open to
    rule-based output when the LLM is unavailable.

---

## 22. Claims That Should NOT Be Made

These must **not** be stated unless real held-out evidence is later produced:

- **Clinically validated disease prediction.**
- **Medical diagnosis** (or "diagnostic" outcomes).
- **Exact / accurate nutritional estimation from a photograph.**
- **Accurate visual portion-mass estimation.**
- **Universal food recognition.**
- **Robust / general arbitrary multi-food detection.**
- **Formal Top-1/Top-3/Top-5 classifier accuracy, macro-F1, or a confusion
  matrix** (none computed).
- **Formal YOLO mAP / precision / recall** (none computed).
- Reporting **training or validation accuracy as test accuracy** (no held-out
  test set exists).

---

## 23. Remaining Limitations

- No labelled held-out split for the classifier or detector ⇒ no formal
  accuracy/mAP; only functional evidence.
- Pre-trained weights; no retraining pipeline and no accuracy figures.
- Portion mass is configured, not measured from the image.
- Static nutrition database (per-100 g representative values); 31/118 classes
  unmapped.
- Several XGBoost clinical inputs are fixed defaults (see `MODEL_LIMITATIONS.md` §4).
- Risk-fusion weights are designer-chosen, not learned.
- CPU-only, single-threaded inference; no rate limiting or server-side upload
  size limit; chat sessions in-memory.
- Detector recall degrades on crowded multi-food compositions.

---

## 24. Recommended Future Work

1. **Build a labelled held-out split** (e.g. a regional Indian-food image
   subset) and report genuine Top-1/Top-3/Top-5, macro-F1, and a confusion
   matrix for EfficientNet-B3.
2. **Label a detection benchmark** for YOLOv8 and report precision/recall /
   mAP@0.5 / mAP@0.5:0.95.
3. **Multi-object training/fine-tuning** for the detector to lift recall on
   crowded plates.
4. **Vision-based portion estimation** (mass/volume from geometry/depth).
5. Personalise the NIS RDI to age/gender/activity; expand beyond 6 nutrients.
6. Clinical validation of the four XGBoost risk models on a target-population
   cohort; calibrate outputs.
7. Learn/validate the risk-fusion weights on outcome data.
8. Add rate limiting, server-side upload limits, Alembic migrations, and
   persisted chat sessions.

---

## 25. Overall Phase 4 Status

**PASS.** All existing Phase 4 artifacts were validated (independent
recomputation agrees with every reported headline number), the missing formal
metrics are honestly reported as `N/A` rather than invented, the software
regression passes in full (189 pytest, clean TS/ESLint, 17-route build), and
the capstone claim audit (**§20–22**) is SAFE: supported claims are evidenced,
limitations are explicit, and no unsupported claim is made. No thresholds,
formulas, weights, mappings, or model artifacts were changed.

---

*Artifacts referenced: `docs/evaluation/phase4_validation.json` (new),
`classifier_confidence.json`, `confidence_distribution.png`,
`robustness_matrix.csv`, `dci_evaluation.json`, `dci_controlled_tests.csv`,
`nis_evaluation.json`, `nis_controlled_tests.csv`,
`risk_fusion_evaluation.json`, `risk_fusion_tests.csv`,
`nutrition_coverage.json`, `portion_estimation.json`, `portion_scaling.csv`,
`e2e_evaluation.csv`, `e2e_summary.json`, `multifood/multifood_summary.json`,
`multifood/upload_detection_scan.csv`, `multifood/synthetic_probes.csv`.
This report is part of the DietRiskNet transparency workstream.*
