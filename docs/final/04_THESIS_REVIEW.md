# DietRiskNet — Thesis Review

**Reviewer note.** This review examines `docs/thesis/` (chapters 01–14 + README)
as an academic submission. Every factual claim about the *implementation* was
verified against the repository (source, configs, models, tests, and
`backend/evaluation/reports/`) on **2026-07-31**. Findings are listed by
category, then per chapter, with suggested corrections and an academic score
for each chapter.

**Verdict at a glance:** strong, honest technical content — the engineering is
real, the methodology chapter is detailed, and the results are presented with
appropriate caveats. It is held back as an *academic* thesis by three things:
(1) two confirmed factual errors (risk-fusion risk levels and the automated
test count), (2) **no references or citations anywhere**, and (3) weak
formatting discipline (table numbering, figure captions, section numbering,
terminology, spelling).

---

## 0. Executive summary

| Dimension | Rating | Comment |
|---|---|---|
| Technical accuracy of the system description | A | Architecture, DCI/NIS formulas, routes, DB schema verified correct |
| Results honesty | A | Correctly discloses stub-based vision benchmarks and low n |
| Algorithms documentation | B | Formulas correct, but feature engineering misrepresented in §7.6 |
| Academic rigour (citations) | F | Zero references, zero inline citations |
| Formatting discipline | C | Table numbering, figure captions, section numbering inconsistent |
| Internal consistency | C | Test counts stale, terminology drift, route lists differ |
| Grammar / prose | A− | Generally clean; a few awkward phrasings |

**Overall thesis score: B+ (82%)** — technically excellent, academically
undercooked. The corrections in §3–§4 below are mostly mechanical (re-verify
numbers, add references/captions, standardise terminology).

---

## 1. Findings by category

### 1.1 Grammar

Overall the prose is clean, professional, and consistent in tense. No
sentence-level errors that impair meaning. Specific items:

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| G1 | Minor | `03_sequence_ai_chat.md:44-45` | "the conversation remembers the previous meal within the session" — ambiguous. | "…the conversation *for that meal* is retained for the lifetime of the session." |
| G2 | Minor | `02_sequence_meal_upload.md` (Notes) | "its failure never breaks the pipeline" (good) but the intro says "the AI Dietitian runs only after the meal is saved" — fine. No issue. | — |
| G3 | Minor | `12_deployment_guide.md:12` | Inline comment is overlong: "Windows CMD (or .venv\Scripts\Activate.ps1 / source .venv/bin/activate)" reads awkwardly in print. | Split into three explicit activation commands. |
| G4 | Minor | `07_methodology.md:45` | "maps redundant modifiers … for a cleaner UI" — slightly loose ("maps … to a display label"). | "maps the canonical dish name to a friendlier `display_name` (e.g. 'Vegetable samosa' → 'Samosa') while preserving the original name." |

### 1.2 Formatting

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| F1 | Major | `09_results.md` (all tables 5.1–5.4) | Tables are labelled **"Table 5.1–5.4"** but appear in **chapter 09**. The "5.x" numbering comes from the evaluation module's output filenames, not the thesis chapter structure. | Either renumber tables **9.1–9.4** (and update the eval-module output filenames to `table_9_x_*`), or make Results a formal Chapter 5. |
| F2 | Major | All chapters 01–06 | **Figures have no captions or numbers.** Every Mermaid diagram is a bare code block; there is no "Figure 6.1" numbering and no List of Figures. | Add `Figure N.M` captions under each diagram and a List of Figures in the front matter. |
| F3 | Major | `13_user_manual.md:71,79` | **Duplicate heading `## 13.7`** appears twice ("Dashboard, Trends & History" and "Notes & Limitations"). | Renumber the second to `## 13.8 Notes & Limitations`. |
| F4 | Minor | `11_conclusion.md` | Uses unnumbered headings (`## Contributions`, `## Validation`, `## Closing`) whereas chapters 07–10, 12–14 use `N.N`. | Use `11.1 … 11.4` (or consistently unnumbered across the thesis). |
| F5 | Minor | `06_database_er_diagram.md:66` | Mermaid attribute `float x1 y1 x2 y2` is rendered as a single attribute with spaces. | Split into four attributes (`float x1`, `float y1`, `float x2`, `float y2`). |
| F6 | Minor | `01_system_architecture.md:14` | The one-line page list is extremely long and wraps unpredictably. | Split pages into a sub-list or table. |
| F7 | Minor | `08_experimental_setup.md:28` | CPU row reads "Intel (single-node, multi-core)" — no model or clock; not reproducible. | Name the CPU model, core count, and clock (or at least the class). |

### 1.3 Consistency (internal + code)

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| C1 | Major | `09_results.md:87` and `11_conclusion.md:45` | **"122 passed" is stale.** `pytest --collect-only` collects **149 tests**; the thesis's own sub-rows (23 duplicate + 47 threshold) already total 70, and 122+23+47 = 192 ≠ 149. The companion `02_VIVA_PREPARATION.md` correctly says "149 tests". | Re-run `pytest` and report the current total (149 collected) with a clean breakdown; remove "122" everywhere. |
| C2 | Major | `07_methodology.md:105` | Risk fusion maps to **"Low / Moderate / High"**; the code (`risk_fusion_service.py`) produces **four** levels including **Critical** (>0.75). The DB model comment also lists all four. | Change to "Low / Moderate / High / Critical" and describe the 0.75 boundary. |
| C3 | Major | `01_system_architecture.md:23` vs `05_component_diagram.md:8-16` vs `14_developer_guide.md:11` | Chapter 01 and 05 **omit the `nutrition_coach` router**; the code registers **8** routers (auth, meal, prediction, user, ai_chat, report, nutrition_chat, nutrition_coach) and chapter 14 lists all 8. | Add `nutrition_coach` to the routes list in 01 and to the "HTTP layer" subgraph in 05. |
| C4 | Major | Terminology across `01:17`, `05:78`, `07 §7.15`, `13 §13.6` | The same page is called **"Nutrition Assistant page"**, **"Nutrition page"**, and **"Personalized AI Nutrition Coach"**. The sidebar label is "Nutrition Assistant"; the page header is "Nutrition Coach". | Pick one canonical term (recommend "Personalized AI Nutrition Coach" or "Nutrition Coach") and use it everywhere; reserve "Nutrition Assistant" for the underlying chat service. |
| C5 | Minor | `07_methodology.md:43-46` | Serving-weight scaling is described as if implemented in `nutrition_service.py`; it actually lives in **`backend/routes/meal.py`** (`DEFAULT_SERVING_WEIGHTS` + `scale = item.weight_g / 100.0`). Also, the weights are **dish-specific** (idli 60 g, dosa 180 g, rice 180 g…), not "default 100 g" (100 g is only the fallback). | Correct the Files line to include `backend/routes/meal.py` and describe per-dish weights + 100 g fallback. |
| C6 | Minor | Spelling | Mixed **UK/US**: "analysed", "normalisation", "recognised" vs "Personalized", "normalization". | Adopt one convention (e.g., UK: "personalised", "analysed", "normalisation"). |
| C7 | Minor | `06_database_er_diagram.md` | ER omits `created_at`/`updated_at` on several tables where the model has them (`diet_history`, `refresh_tokens`, `user_settings`). | Either show the audit columns or state they are elided. |
| C8 | Minor | `14_developer_guide.md:60` | Says "Bump `AICacheService.PROMPT_VERSION`"; the constant is a **module-level** `PROMPT_VERSION = "1"` in `ai_cache_service.py`. | Write `ai_cache_service.PROMPT_VERSION`. |
| C9 | Minor | `12_deployment_guide.md:22` | Says "copy `.env.example` to `.env`", but `.env.example` contains **stale machine-specific paths** (`d:\DietRiskNet\backend\trained_models`, `…nutrition\…`) that do not match this checkout's path. | Make `.env.example` relative or platform-agnostic (e.g. blank defaults), or document that `MODELS_DIR`/`NUTRITION_CSV_PATH` must be adjusted. |
| C10 | Minor | `12_deployment_guide.md` | CWD ambiguity: §12.1 ends in `frontend/`, but §12.3 runs `uvicorn backend.main:app` which requires the **project root** as CWD. | State explicitly: "return to the project root before running uvicorn." |
| C11 | Minor | `07_methodology.md §7.11`, `03_sequence_ai_chat.md` | The chat memory is described only as "max 10 messages"; the shared `ConversationStore` also caps **256 sessions** and applies **idle-TTL eviction**. | Add the session cap / TTL for completeness. |
| C12 | Nit | `04_data_flow_diagram.md:28,69` | Data store `D4` is labelled "AIDietitianResults cache"; the table is `ai_dietitian_results`. | Align the label with the table name. |
| C13 | Nit | `01_system_architecture.md:44` | The Data subgraph's DB list omits `user_settings`, `refresh_tokens`, `diet_history`, `audit_logs`, `meal_items`. | Mark as partial ("key tables") or list all 12. |

### 1.4 Architecture

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| A1 | Major | `01_system_architecture.md:23` | Missing `nutrition_coach` router (see C3). | Add it. |
| A2 | Good | throughout | Three-tier structure, deterministic-core/AI-separation, fail-safe AI, and provider-agnostic `LLMClient` are all accurately described and match the code. | — |
| A3 | Minor | `05_component_diagram.md:101` | Contract for `ai_cache_service` lists `invalidate` — **verified present** in `ai_cache_service.py:148`. No change. | — |
| A4 | Nit | `01_system_architecture.md` | "Backward compatible" property is well documented. No change. | — |

### 1.5 Algorithms

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| AL1 | **Critical** | `07_methodology.md:105` | Fusion level set wrong — **Critical omitted** (see C2). | Four levels: Low / Moderate / High / Critical. |
| AL2 | **Major** | `07_methodology.md:84-89` (§7.6 table) | The four XGBoost "Inputs (engineered)" rows **misrepresent the real feature vectors**:
- **Obesity**: code does **not** use BMI (the `bmi` argument is unused); `Height` is converted to **metres**. The model is **multiclass (7 classes)** and risk = Σ of class probabilities 2–6 — none of this is stated.
- **Hypertension**: `stress`, `sleep`, `medication`, `exercise`, `smoking` are **hardcoded constants** (3.0 / 7.0 / 0 / 2.0 / 'Never'), not user inputs; only age, BMI, salt (derived from sodium) and BP-history are derived.
- **Diabetes**: `HbA1c` and `glucose` are **heuristic estimates** from the existing-conditions flag (7.0/5.5 and 160/100), not measurements; `smoking_history` (fixed 'never') is omitted from the table.
- **Deficiency**: `hemoglobin` is fixed at 14.0; only vitamin-C/folate/calcium/iron RDA% are computed from the meal; most other features are hardcoded defaults. | Rewrite §7.6 as a table of **actual** feature columns per model, and mark every hardcoded default; state that obesity is a multiclass model and that several predictors are fixed constants (i.e. the models are used in a simplified, "profile + meal-derived" mode). |
| AL3 | Minor | `07_methodology.md §7.4` | DCI window/fallback verified correct (7-day window, ≥2 days, 55/15/30 macro target). No change. | — |
| AL4 | Minor | `07_methodology.md §7.5` | NIS formula and six RDI nutrients verified correct. No change. | — |
| AL5 | Minor | `07_methodology.md §7.1` | IoU filter `> 0.6` and crop_size 300/224 verified correct. No change. | — |

### 1.6 Results

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| R1 | **Major** | `09_results.md:87` | **Stale test count** "122 passed" (see C1). Actual collected total is 149. | Re-run and fix. |
| R2 | **Major** | `09_results.md` + `system_metrics.json` | **Statistical weakness:** the pipeline and AI benchmarks ran with **n = 2 iterations**; reporting **median and p95 on n = 2** is statistically meaningless (a single run dominates both). PDF ran n = 3, cache n = 10. | Run ≥ 20–30 iterations, report the sample size in the tables, and note n in the caption. |
| R3 | Minor | `09_results.md:9` | The honest caveat (stub vision stages, real XGBoost) is exemplary — keep it. | — |
| R4 | Minor | `09_results.md:28-31` | Interpretation is sound ("relative ordering is meaningful"). No change. | — |

### 1.7 Evaluation

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| E1 | Major | `08_experimental_setup.md:49` | **`matplotlib 3.10` listed as a pinned dependency, but it is absent from `requirements.txt`** (verified). The evaluation module imports it and emits PNGs, so it is a real runtime dependency of `backend/evaluation/`. | Add `matplotlib==3.10.9` to `requirements.txt` (or move to a `requirements-eval.txt`), and correct the sentence "Dependencies are pinned in requirements.txt". |
| E2 | Minor | `08_experimental_setup.md:24-30` | Hardware table too vague to be reproducible (see F7). | Give CPU model / clock / core count. |
| E3 | Good | `08 §8.4`, `README` | Benchmark commands verified against real module names; outputs land in `backend/evaluation/reports/`. No change. | — |
| E4 | Minor | `09 §9.6` | QA rows: 23 (duplicate) and 47 (threshold, parametrized) are individually **correct**; only the "122" total is wrong. | Restructure QA as: total suite (149) + the two targeted subsets (23, 47). |

### 1.8 Tables

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| T1 | Major | `09_results.md` | Numbering "Table 5.x" vs chapter 09 (see F1). | Renumber to 9.x (or restructure chapters). |
| T2 | Minor | `06_database_er_diagram.md` | Incomplete column lists (missing audit columns, see C7). | Either add or annotate as elided. |
| T3 | Minor | `08_experimental_setup.md:15-20` | Model size table verified correct (22 / 126 / 18 MB; XGBoost 0.6–2.8 MB). No change. | — |

### 1.9 Figures

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| Fg1 | Major | All chapters 01–06 | Mermaid diagrams are the only figures and have **no captions, numbers, or cross-references**; no List of Figures. | Add `Figure N.M` captions; reference them in text (e.g. "see Figure 6.1"); add a List of Figures. |
| Fg2 | Minor | `06_database_er_diagram.md:66` | Malformed single attribute `float x1 y1 x2 y2` (see F5). | Split into four attributes. |
| Fg3 | Minor | `02/03` | Sequence diagrams are accurate but participants are numerous; consider keeping one diagram per concern (already done). No change. | — |

### 1.10 References & Citations

| # | Severity | Location | Issue | Correction |
|---|---|---|---|---|
| RC1 | **Critical** | Entire thesis | **No References / Bibliography chapter and no inline citations.** The text invokes YOLO (Redmon et al.), EfficientNet (Tan & Le, 2019), XGBoost (Chen & Guestrin), Ultralytics, ReportLab, RDI/WHO figures, the Indian food-composition database, and Gemini — none are cited. A search for `References|Bibliography|et al|[1]` across `docs/thesis/` returns nothing (the only hits are in `docs/final/03_POWERPOINT_CONTENT.md`). | Add a References chapter and cite at least: Redmon et al. (YOLO), Ultralytics YOLOv8 docs, Tan & Le 2019 (EfficientNet), Chen & Guestrin 2016 (XGBoost), the Indian food-composition source of the CSV, ReportLab docs, and the Gemini / Google Generative AI docs. Use one consistent style (e.g., IEEE or APA). |
| RC2 | **Critical** | `07_methodology.md` | The Literature/Background context (why these models, state of the art) is absent; §7 states choices without scholarly grounding. | Add a Literature Review / Related Work chapter, or at minimum cite the model papers at first mention in §7. |
| RC3 | Minor | `07_methodology.md:29` | "crop_size (300 for B3, 224 for B0)" — factual and correct; consider citing the standard ImageNet normalization used. | Cite PyTorch/ImageNet conventions. |

---

## 2. Chapter-by-chapter review and academic scores

Scoring: 90–100 A, 80–89 B, 70–79 C, 60–69 D, <60 F. Scores weigh
**accuracy** (heavy), completeness, clarity, and academic rigour.

### Chapter 01 — System Architecture — **B+ (82)**
Strong three-tier description; deterministic/AI separation is well explained.
Deducted for: missing `nutrition_coach` route (A1/C3), "Nutrition Assistant
page" terminology drift (C4), incomplete DB subgraph list (C13), no figure
caption, no citations. Corrections: §1.3 C3, C4, C13; §1.2 F2; §1.10 RC.

### Chapter 02 — Sequence Diagram: Meal Analysis — **A− (88)**
Endpoint `/api/analyze-meal`, ordering, and fail-safe logic all verified
correct. Clean. Minor: no figure caption (F2). Corrections: §1.2 F2.

### Chapter 03 — Sequence Diagram: AI Chat — **A− (86)**
Accurate (`/api/ai/chat`, 10-message memory, no ML re-run). Deducted for:
awkward sentence (G1), missing session cap/TTL (C11), no figure caption.
Corrections: §1.1 G1; §1.3 C11; §1.2 F2.

### Chapter 04 — Data Flow Diagram — **A− (88)**
Level-0/Level-1 decomposition is correct and security notes match the code.
Minor: D4 label (C12), no figure caption. Corrections: §1.3 C12; §1.2 F2.

### Chapter 05 — Component Diagram — **B+ (82)**
Service decomposition and contracts verified (including `invalidate`).
Deducted for: missing `nutrition_coach` in the HTTP-layer box (C3),
terminology (C4), no figure caption. Corrections: §1.3 C3/C4; §1.2 F2.

### Chapter 06 — Database ER Diagram — **A− (87)**
All 12 tables, columns, indexes (`idx_meal_user_created`,
`idx_diet_history_user_logged`, `idx_ai_meal_context`), and cascade rules
verified against `models.py` and `models/ai_dietitian.py`. Deducted for: elided
audit columns (C7), malformed `x1 y1 x2 y2` attribute (F5), no figure caption.
Corrections: §1.3 C7; §1.2 F5/F2.

### Chapter 07 — Methodology — **C+ (68)**
The richest chapter: DCI/NIS formulas, thresholds, cache design, and the
coach analytics are all accurate and well referenced to files. Heavily
deducted for: **wrong fusion level set (C2/AL1)**, **misrepresented XGBoost
feature tables (AL2)**, serving-weight file attribution (C5), and **zero
citations** for every named algorithm (RC1/RC2). Corrections: §1.3 C2/C5;
§1.5 AL1/AL2; §1.10 RC1/RC2.

### Chapter 08 — Experimental Setup — **B (78)**
Dataset and model-size tables verified; run commands work. Deducted for:
`matplotlib` not pinned (E1), vague hardware spec (E2/F7), and the low-n
benchmark design that flows into chapter 09 (R2). Corrections: §1.7 E1/E2;
§1.6 R2.

### Chapter 09 — Results — **B− (74)**
Excellent honesty (stub disclosure) and correct values in Tables 5.1–5.5.
Deducted for: **stale "122 passed" (R1)**, **n=2 median/p95 weakness (R2)**,
table numbering "5.x" vs chapter 09 (F1). Corrections: §1.6 R1/R2; §1.2 F1.

### Chapter 10 — Discussion — **B+ (82)**
Advantages and limitations are honest and match the code. Deducted for: no
citations for the comparative claims; §10.2's "rule engine is shallow"
is defensible (longitudinal patterns are consumed by the *coach*, not the
rule engine) but should say so explicitly. Corrections: §1.10 RC; add one
sentence clarifying the rule-engine vs coach scope.

### Chapter 11 — Conclusion — **B (78)**
Clear contribution list. Deducted for: **stale "122 automated tests" (R1)**
repeated from 09, unnumbered headings (F4). Corrections: §1.6 R1; §1.2 F4.

### Chapter 12 — Deployment Guide — **B+ (82)**
Commands verified; `render.yaml` claim (`generateValue: true`, DATABASE_URL)
verified correct. Deducted for: stale `.env.example` paths (C9), CWD
ambiguity (C10), long activation comment (G3). Corrections: §1.3 C9/C10;
§1.1 G3.

### Chapter 13 — User Manual — **B+ (83)**
Clear, accurate walkthrough (file formats, profile fields, endpoints verified).
Deducted for: **duplicate `## 13.7` heading (F3)**, terminology drift (C4).
Corrections: §1.2 F3; §1.3 C4.

### Chapter 14 — Developer Guide — **A− (88)**
Best chapter structurally. Route list includes all 8 routers (consistent with
code), conventions and provider-addition steps are correct. Deducted for:
`AICacheService.PROMPT_VERSION` wording (C8). Corrections: §1.3 C8.

---

## 3. Consolidated issue register (by severity)

| ID | Severity | Chapter(s) | Summary | Fix |
|---|---|---|---|---|
| RC1/RC2 | **Critical** | 07, 10, all | No references / no citations / no literature context | Add References + Literature Review |
| AL1/C2 | **Critical** | 07 | Fusion levels omit "Critical" | Four levels Low/Mod/High/Critical |
| R1/C1 | **Major** | 09, 11 | "122 passed" is stale; actual = 149 collected | Re-run pytest, correct in both places |
| AL2 | **Major** | 07 | §7.6 feature tables misrepresent the models (hardcoded inputs, multiclass obesity) | Rewrite against `prediction_service.py` |
| F1 | **Major** | 09 | "Table 5.x" numbering ≠ chapter 09 | Renumber 9.x or restructure |
| F2 | **Major** | 01–06 | Figures lack captions/numbers/List of Figures | Add captions |
| F3 | **Major** | 13 | Duplicate `## 13.7` heading | Renumber second to 13.8 |
| C3 | **Major** | 01, 05 | `nutrition_coach` router missing from route lists | Add it |
| R2 | **Major** | 09 | n=2 benchmark; median/p95 meaningless | Increase iterations, report n |
| E1 | **Major** | 08 | `matplotlib` not pinned in `requirements.txt` | Add dependency |
| C4 | **Major** | 01, 05, 07, 13 | Nutrition "Assistant"/"Coach" terminology drift | Pick one term |
| C5 | Minor | 07 | Serving-weight scaling attributed to wrong file | Add `routes/meal.py`; describe per-dish weights |
| C6 | Minor | global | UK/US spelling mix | Standardise |
| C7 | Minor | 06 | ER elides audit columns | Annotate or add |
| C8 | Minor | 14 | `PROMPT_VERSION` is module-level, not class-level | Fix wording |
| C9 | Minor | 12 | `.env.example` has stale absolute paths | Make path-agnostic |
| C10 | Minor | 12 | CWD ambiguity for uvicorn command | State project-root CWD |
| C11 | Minor | 03, 07 | Chat session cap (256) / TTL not documented | Add |
| C12 | Nit | 04 | `D4` label vs table name | Align |
| C13 | Nit | 01 | DB subgraph list incomplete | Mark as key tables |
| E2/F7 | Minor | 08 | Vague CPU spec | Name the CPU |
| F4 | Minor | 11 | Unnumbered section headings | Use 11.x |
| F5 | Minor | 06 | `float x1 y1 x2 y2` malformed attribute | Split into four |
| G1 | Minor | 03 | Awkward sentence | Rephrase |
| G4 | Minor | 07 | Loose wording on display names | Tighten |

---

## 4. Priority correction roadmap

1. **Correct the two factual errors first** (they will be probed in viva):
   - Fusion risk levels → include **Critical** (`07_methodology.md:105`).
   - Replace "122 passed" with the verified **149 collected** in `09_results.md` and `11_conclusion.md`.
2. **Rewrite §7.6** to reflect the actual feature engineering (hardcoded
   defaults, multiclass obesity, metre-height input, heuristic HbA1c/glucose).
3. **Add References + inline citations** (minimum set: YOLO, EfficientNet,
   XGBoost, Indian food-composition source, ReportLab, Google Generative AI).
4. **Formatting pass:** renumber tables to 9.x, add Figure captions + List of
   Figures, fix the duplicate `13.7`, standardise section numbering and
   spelling, unify "Nutrition Coach" naming, add `nutrition_coach` to route
   lists in 01/05.
5. **Evaluation hardening:** pin `matplotlib`, raise benchmark iterations to
   ≥ 20 and state n, name the CPU.
6. **Deployment doc:** fix `.env.example` paths and CWD instructions.

---

## 5. Verification appendix (what this review checked)

- **Routes** — `backend/main.py` registers 8 routers; all paths in ch. 02/03/07/12 (`/api/analyze-meal`, `/api/ai/chat`, `/api/nutrition-chat`, `/api/nutrition/analytics`, `/api/report/{meal_id}`) confirmed.
- **Fusion** — `risk_fusion_service.py`: weights 0.25/0.25/0.20/0.15/0.10/0.05; levels Low ≤0.25, Moderate ≤0.50, High ≤0.75, else **Critical**.
- **XGBoost features** — `prediction_service.py`: confirmed hardcoded constants and multiclass obesity (Σ proba[2:]), metre-height input, heuristic HbA1c/glucose, fixed hemoglobin 14.0.
- **DCI/NIS** — `indices_services.py`: 7-day window, ≥2 days → `1 − CV`, fallback 55/15/30 macro target; NIS = mean relative deviation over 6 RDI nutrients.
- **Serving weights** — `routes/meal.py:28-42` (`DEFAULT_SERVING_WEIGHTS`), scaling `scale = weight_g/100.0`.
- **DB** — `models.py` + `models/ai_dietitian.py`: 12 tables; indexes `idx_meal_user_created`, `idx_diet_history_user_logged`, `idx_ai_meal_context` all present; cascade rules confirmed.
- **Tests** — `pytest backend/tests --collect-only`: **149 collected** (thresholds 47 via parametrization, duplicate 23; `test_pipeline.py` contributes 0).
- **Dependencies** — `requirements.txt` has **no matplotlib**; `matplotlib 3.10.9` installed in venv.
- **Benchmarks** — `system_metrics.json`: pipeline iterations **2**, cache 10, pdf 3; table_5_1/5_2/5_3/5_4 values match ch. 09.
- **Render** — `render.yaml`: `SECRET_KEY.generateValue: true` confirmed.
- **Chat store** — `conversation_store.py`: `DEFAULT_MAX_MESSAGES = 10`, `DEFAULT_MAX_SESSIONS = 256`, idle-TTL eviction.
- **Cache** — `ai_cache_service.py`: `context_hash` (SHA-256), `save_response`/`get_cached_response`/`invalidate`, module-level `PROMPT_VERSION`.
- **References** — no References/Bibliography content exists in `docs/thesis/`.
