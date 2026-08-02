# Phase 5 — Final Repository Audit, Evidence Freeze & Capstone Checkpoint

> **Scope.** Audit of the DietRiskNet working tree ahead of the final capstone
> commit. This phase changes nothing: no model, threshold, formula, weight,
> mapping, UI, or Phase 4 evidence was modified. No commit was made.
> Phase 4 is **PASS** and its quantitative results are treated as **frozen
> evidence**.

---

## 1. Executive Summary

The repository is in a **clean, auditable, submission-ready state**:

- All model weights are **already Git-tracked** (178 MB) and were **not**
  modified; B3 is the confirmed deployed classifier.
- **No blocking secret or privacy risk** is present in any file intended for
  commit (the only real credential lives in `.env`, which is gitignored).
- The **software regression passes in full**: pytest **189 passed**, TypeScript
  clean, ESLint clean, production build **17 routes**.
- Reproducibility is **PASS with warnings**: the optional Ollama/LLM layer
  depends on a portable `runtime/ollama/` tree (3.7 GB) that is **not** in git
  and must be transferred separately — the core ML pipeline does not need it.
- A small number of **stale documentation contradictions** must be corrected
  before thesis submission (mostly an old "EfficientNet-B0 / 360 classes"
  description in two project docs, plus a 3-level vs 4-level risk-fusion
  wording in the thesis methodology).

**Overall Phase 5 audit: PASS WITH WARNINGS.**

---

## 2. Phase 4 Evidence Freeze

The following files were read and treated as immutable for this audit:

- `docs/final/07_PHASE3_MODEL_HONESTY_REPORT.md`
- `docs/final/08_PHASE4_FINAL_EVALUATION_REPORT.md`
- `docs/evaluation/phase4_metrics.json`
- `docs/evaluation/phase4_validation.json`
- `MODEL_LIMITATIONS.md`

Frozen headline values (verified): classifier 118 classes · nutrition mapping
**87/118 → 73.73 %** · classifier mean confidence **0.826** · non-food max
**0.036** · acceptance threshold **0.45** · E2E **92 / 82 ok / 9 safe-reject /
1 nutrition-unavailable / 0 unexpected failures** · pytest **189 passed** ·
formal Top-1/Top-3/Top-5/F1 and YOLO mAP **N/A**.

---

## 3. B3/B0 Architecture Resolution

**Conclusion: EfficientNet-B3 is the primary and actually-loaded deployed
classifier. EfficientNet-B0 is a compatibility fallback only.** — **VERIFIED.**

| Question | Evidence |
|---|---|
| Architecture attempted first | B3 — `settings.FOOD_CLASSIFIER_MODEL` defaults to `DietRiskNet_FoodClassifier_EfficientNetB3.pth` (`backend/config.py`) |
| Checkpoint actually loaded in normal startup | **B3** — runtime load confirmed: "Loading Food Classifier (DietRiskNet_FoodClassifier_EfficientNetB3.pth) … Detected architecture: efficientnet_b3 … crop_size = 300 … 118 classes" |
| State-dict architecture check | B3 checkpoint `conv_stem.weight` → 40 channels (b3); B0 checkpoint → 32 channels (b0). Verified by inspection. |
| Conditions that trigger B0 | Only when the configured B3 file is **missing** from `MODELS_DIR` and the B0 file exists → a `ml_logger.warning` and B0 is loaded (crop_size 224). |
| Separate B0 checkpoint? | Yes — `DietRiskNet_FoodClassifier_EfficientNetB0.pth` (18 MB) is a distinct file. |
| Can the deployed system silently run B0? | Only if B3 is absent at load time; it logs a warning (not fully silent). With B3 present, B0 is never used. |
| Architecture used in Phase 4 E2E | **B3** — the E2E harness uses the same `classifier_service` / config with B3 present (verified in this audit). |
| Thesis wording | See below. |

**Do-not-cite note.** The B3 checkpoint contains a training-time `best_acc ≈
0.8863` (epoch 19), but the underlying evaluation split cannot be reliably
reconstructed. It is **not** reported as formal held-out classifier accuracy;
Phase 4's Top-1/Top-3/Top-5/F1 remain **N/A**.

**Recommended thesis wording:** "DietRiskNet uses EfficientNet-B3 as its
deployed food classification model. An EfficientNet-B0 checkpoint is retained
only as an implementation fallback."

---

## 4. Repository Working-Tree State

`git status --porcelain --untracked-files=all` at audit time:

- **Modified tracked files: 45** (all pre-existing working changes from Phases
  2–4: backend source, frontend source, tests, config templates, docs, and the
  two DCI/NIS config JSONs).
- **Untracked files: ~260** across new source, tests, evaluation harnesses and
  evidence, documentation, scripts, `.claude` config, `runtime/ollama/` (DLLs +
  model blobs), and three root debug images.
- **Ignored/not-shown (gitignored):** `backend/.venv/` (2.3 GB),
  `frontend/node_modules/` (525 MB), `frontend/.next/` (700 MB),
  `__pycache__/`, `.pytest_cache/`, `*.db` (including `dietrisknet.db`, `test.db`),
  `backend/uploads/*` (92 user-uploaded images, 21 MB), `.env`, logs.
- **Already tracked binaries:** all model weights in `backend/trained_models/`
  (178 MB) — **not** modified, **not** to be untracked.

---

## 5. File Classification Summary

| Class | Items | Decision |
|---|---|---|
| A. Source code | Modified + new backend/frontend source (routes, services, llm/, components/, app/) | **KEEP / commit** |
| B. Tests | `backend/tests/*` (14 files, incl. new) + `test_pipeline.py` | **KEEP / commit** |
| C. Documentation | `README.md`, `HOW_TO_RUN.md`, `MODEL_LIMITATIONS.md`, `docs/evaluation.md`, `docs/final/*`, `docs/thesis/*` | **KEEP / commit** |
| D. Evaluation evidence | `docs/evaluation/**` (JSON/CSV/PNG), `backend/evaluation/reports/**`, `backend/evaluation/**` harnesses | **KEEP / commit** |
| E. Config template | `.env.example`, `docker-compose.yml`, `requirements.txt`, `scripts/*.bat` | **KEEP / commit** |
| F. Model artifact | `backend/trained_models/*` (already tracked, 178 MB) | **REVIEW** — keep tracked; no action |
| G. Generated build/cache | `.next/`, `node_modules/`, `.venv/`, `__pycache__/`, `.pytest_cache/` | **DO NOT COMMIT** (already ignored) |
| H. DB/runtime state | `dietrisknet.db`, `test.db` | **DO NOT COMMIT** (ignored) |
| I. User uploads | `backend/uploads/*` (92 images) | **DO NOT COMMIT** (ignored) |
| J. Secret/credential | `.env` (real Gemini key) | **DO NOT COMMIT** (ignored) |
| K. Temporary/debug | `reg_bad.png`, `reg_bad.txt`, `reg_green.png` | **REVIEW/REMOVE or ignore** |
| L. Unknown / manual | `.claude/settings*.json`, `runtime/ollama/`, `frontend/.vercel/`, `docs/evaluation/_meal_timestamps.json`, `docs/evaluation/multifood/*.png` | **MANUAL REVIEW** (§16) |

---

## 6. Secret and Privacy Audit

Scanned: `.env`, `.env.example`, `backend/config.py`, `docker-compose.yml`,
`backend/utils/auth_utils.py`, `backend/routes/auth.py`,
`backend/services/auth_service.py`, `backend/services/llm/*`,
`backend/services/*cache/*chat*/*meal_ai*`, `.claude/settings*.json`,
`HOW_TO_RUN.md`, `README.md`, `docs/final/GEMINI_CONFIGURATION_REPORT.md`,
`docs/final/OLLAMA_PROVIDER_GUIDE.md`,
`docs/final/PORTABLE_PROJECT_MIGRATION.md`, `scripts/*.bat`,
`frontend/services/api.ts`.

| Path | Risk type | Status | Recommended action |
|---|---|---|---|
| `.env` | **Real Gemini API credential** (`GEMINI_API_KEY`, value `AQ.…` redacted) | Gitignored — **not** in repo | Keep ignored; rotate if ever shared. **Not blocking** for commit. |
| `.env.example` | Placeholder only (`YOUR_GEMINI_API_KEY_HERE`) | Safe | Keep |
| `docker-compose.yml` | Dev-default `postgres:postgres` + dev `SECRET_KEY` | Safe (known dev defaults, already in history) | OK for dev; do not reuse in prod |
| `backend/config.py`, `llm/*`, docs, scripts | References to the env var **name** `GEMINI_API_KEY` (no values) | Safe | Keep |
| `.claude/settings.local.json` | Only permission allowlist (no values) | Safe but machine-specific | Gitignore (§16) |
| `backend/uploads/*` (92 images) | **User-uploaded meal photos** | Gitignored | Keep ignored; not part of commit |
| `dietrisknet.db` | **Application data** (20 user accounts, real emails, 92 meals) | Gitignored | Keep ignored; not part of commit |

**Blocking secret: NO.** No real credential appears in any file intended for
commit. `git check-ignore` confirms `.env` is excluded.

---

## 7. Large File / Model Audit

Tracked model artifacts (all already in Git; **not** to be untracked):

| File | Size | Type | Git status | Recommendation |
|---|---|---|---|---|
| `DietRiskNet_FoodClassifier_EfficientNetB3.pth` | 131.4 MB | PyTorch weights | tracked | Keep tracked; Git LFS preferable for future repos |
| `DietRiskNet_FoodDetector_YOLOv8.pt` | 22.5 MB | YOLO weights | tracked | Keep tracked; LFS preferable |
| `DietRiskNet_FoodClassifier_EfficientNetB0.pth` | 18.2 MB | fallback weights | tracked | Keep tracked; LFS preferable |
| `DietRiskNet_Obesity_XGBoost.pkl` | 2.9 MB | XGBoost | tracked | Keep |
| `DietRiskNet_NutritionalDeficiency_XGBoost.pkl` | 1.8 MB | XGBoost | tracked | Keep |
| `DietRiskNet_Hypertension_XGBoost.pkl` | 0.7 MB | XGBoost | tracked | Keep |
| `DietRiskNet_Diabetes_XGBoost.pkl` | 0.6 MB | XGBoost | tracked | Keep |

**Total tracked weights ≈ 178.1 MB.** For a capstone the committed weights make
the repository self-contained (required for execution without external
download). For long-term repository maintenance, **Git LFS would be
preferable**; **no `git lfs migrate` was run** and none is proposed in Phase 5.

Other large directories (all gitignored or untracked): `backend/.venv` 2.3 GB,
`runtime/ollama` 3.7 GB, `frontend/.next` 700 MB, `frontend/node_modules`
525 MB, `backend/uploads` 21 MB, `dietrisknet.db` 408 KB, `test.db` 148 KB.

---

## 8. Ollama Runtime Audit

**`runtime/ollama/` total size: 3.7 GB** (untracked).

Contents (confirmed by inspection):
- **Ollama executable** — `bin/ollama.exe`.
- **Runtime/DLL libraries** — `bin/lib/ollama/*.dll` (ggml, libllama, MSVC
  runtime, platform-specific CPU builds).
- **CUDA libraries** — `bin/lib/ollama/cuda_v12/*.dll`, `cuda_v13/*.dll`,
  `vulkan/*.dll`.
- **Downloaded LLM model blobs** — `models/blobs/sha256-*` (≈1.9 GB).
- **Model manifests** — `models/manifests/registry.ollama.ai/library/llama3.2/3b`.

**Recommendation (evidence-based):** this directory is a **portable local
Ollama installation + downloaded model cache**. It is fully recreatable /
downloadable (install Ollama, `ollama pull llama3.2:3b`), is ~3.7 GB of binary
third-party runtime, and **should NOT be part of the final source-code commit**.
The setup scripts already handle it as an external transfer item
(`scripts/setup_new_pc.bat` / `start_ollama.bat` document copying or pulling
it). **Recommend adding `runtime/` to `.gitignore`** (documented in §9; not
edited yet).

---

## 9. .gitignore Recommendations

Current `.gitignore` already correctly excludes: `node_modules/`,
`frontend/.next/`, virtual environments, `__pycache__/`, `*.pyc`,
`.pytest_cache/`, `*.db`, `backend/uploads/*`, `backend/logs/*`, `.env`
variants, IDE/OS files, logs, `frontend/lint_output.txt`.

**Recommended additions** (documented here; **not applied** until the audit is
accepted):

```
# Portable Ollama runtime + downloaded model blobs (recreatable)
runtime/

# Local / machine-specific Claude Code overrides
.claude/settings.local.json

# Temporary registration debug artifacts
reg_bad.png
reg_bad.txt
reg_green.png

# Vercel CLI metadata
frontend/.vercel/
```

**Do NOT ignore** (valuable evidence): `docs/evaluation/`,
`backend/evaluation/phase4/`, `docs/final/`, `MODEL_LIMITATIONS.md`,
`HOW_TO_RUN.md`. These are safe to commit.

---

## 10. Documentation Consistency Audit

Baseline = frozen Phase 4 evidence (§2). Contradictions found:

| # | File | Claim | Why it conflicts | Recommended correction |
|---|---|---|---|---|
| 1 | `docs/PROJECT_STRUCTURE.md:111` | "EfficientNet-B0 Classification … into one of **360 food classes**" | Deployed classifier is **B3 with 118 classes**; 360 is obsolete | Update to EfficientNet-B3, 118 classes |
| 2 | `docs/RUN_PROJECT.md:11` | "**EfficientNet-B0** classifier for categorizing **360 unique food items**" | Same as above | Update to B3, 118 classes |
| 3 | `docs/thesis/07_methodology.md:105` | Risk fusion "maps to `Low / Moderate / High`" (3 levels) | Code produces **4 levels incl. Critical** (>0.75) — already flagged as thesis-review item C2 | State "Low / Moderate / High / Critical"; describe the 0.75 boundary |
| 4 | `docs/thesis/09_results.md` (all §9.1–9.5) | Benchmark tables from **stub** vision models (e.g. `yolo_detection 0.002 ms`); QA "122 passed" | Phase 4 used **real models**; current suite is **189 passed**; stub numbers are stale | Replace with Phase 4 real-model results, or clearly mark as an earlier stub run; update test counts |
| 5 | `docs/thesis/09_results.md` | Tables labelled "Table 5.x" | Chapter is 09 (existing review item F1) | Renumber to 9.x |
| 6 | `README.md:5` | "**clinical-grade classifiers** (XGBoost)" | Conflicts with the "not clinically validated" honesty framing | Reword to e.g. "XGBoost disease-risk classifiers" |

**Not contradicted (correct):** `docs/thesis/07_methodology.md` (B3, 118
classes, B0 fallback, crop 300/224), `docs/thesis/08_experimental_setup.md`
(B3 primary), `MODEL_LIMITATIONS.md`, Phase 3/4 reports, `HOW_TO_RUN.md`. No
document cites `88.63%` / `79.87%` / Top-1/3/5 / mAP / clinical validation as
measured — the honest `N/A` framing holds.

**Blocking: NO.** Items 1–5 are **corrections required before thesis
submission**; none contradict frozen Phase 4 evidence (they are stale text, not
wrong metrics).

---

## 11. Reproducibility Audit

Verified `HOW_TO_RUN.md`, `README.md`, `docs/RUN_PROJECT.md`, and
`scripts/{setup_new_pc,start_backend,start_frontend,start_ollama,start_all}.bat`
against the actual project:

| Check | Status |
|---|---|
| Python version | 3.10+ required (uses `X \| None` types); scripts check `python --version`; not pinned in requirements (only package pins) |
| Backend install | `python -m venv backend/.venv` + `pip install -r requirements.txt` — works (verified venv present) |
| Backend startup | `uvicorn backend.main:app` — config auto-resolves `MODELS_DIR` / `NUTRITION_CSV_PATH` to project-relative paths (portable) |
| Database init | Auto-created on startup (`Base.metadata.create_all`) |
| Model paths | Auto-resolved; B3 present and loaded (verified) |
| Nutrition CSV | Auto-resolved (`nutrition/indian_food_nutrition_processed.csv`) |
| Frontend install/start | `npm install` + `npm run dev` — works |
| Env vars | `.env.example` documents all; `.env` optional (defaults work); `SECRET_KEY` insecure-default warning is non-blocking in dev |
| Ollama (optional) | Portable `runtime/ollama/` must be transferred or pulled (`setup_new_pc.bat` documents this) |
| Gemini (optional) | Key in gitignored `.env`; falls back to Ollama, then rule-based |
| Windows path assumptions | Scripts compute `PROJECT_ROOT` from `%~dp0` — portable across drives |

**Status: PASS WITH WARNINGS.** The core ML pipeline and app run from a fresh
clone + venv + `npm install`. The only warning is the **optional LLM layer**:
`runtime/ollama/` (3.7 GB) is not in git and must be copied or the model pulled
before AI features work — this is documented in the scripts. A fresh evaluator
who skips that will still get a fully working ML pipeline (AI features degrade
gracefully to rule-based output).

---

## 12. Backend Regression Results

`python -m pytest backend/tests/ -q` → **189 passed, 0 failed** (7
non-blocking Pydantic v2 deprecation warnings). Matches the Phase 4 baseline.

---

## 13. Frontend Regression Results

| Check | Command | Result |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | **clean** (0 errors) |
| ESLint | `npx eslint .` | **clean** |
| Production build | `npm run build` | **success, 17/17 routes prerendered** |

---

## 14. Proposed Final Commit Contents (SAFE TO COMMIT)

**Backend source** — `backend/config.py`, `backend/main.py`,
`backend/database/models.py`, `backend/schemas/schemas.py`,
`backend/routes/{auth,deps,meal,prediction,ai_chat,nutrition_chat,nutrition_coach,report}.py`,
`backend/services/*.py` (incl. `llm/`, `classification.py`, new AI/cache/report
services), `backend/utils/{auth_utils,datetime_utils}.py`,
`backend/models/ai_dietitian.py`, `backend/prompts/*`,
`backend/exceptions/*`, `backend/trained_models/{DCI,NIS}_Config.json`.

**Frontend source** — `frontend/app/**/*.tsx`, `frontend/components/**/*.tsx`,
`frontend/lib/store.ts`, `frontend/services/api.ts`, `frontend/types/index.ts`,
`frontend/app/nutrition/page.tsx`, `frontend/components/{analysis,auth,landing}/*`.

**Tests** — `backend/tests/**` (15 files incl. `conftest.py`, `test_pipeline.py`).

**Evaluation harness** — `backend/evaluation/*.py`,
`backend/evaluation/phase4/*.py`.

**Evaluation evidence** — `docs/evaluation/**` (JSON/CSV/PNG incl.
`phase4_metrics.json`, `phase4_validation.json`, `multifood/*`),
`backend/evaluation/reports/**`.

**Documentation** — `README.md`, `HOW_TO_RUN.md`, `MODEL_LIMITATIONS.md`,
`docs/evaluation.md`, `docs/final/**`, `docs/thesis/**`.

**Scripts / config templates** — `scripts/*.bat`, `.env.example`,
`requirements.txt`, `docker-compose.yml`.

---

## 15. Files to Exclude (DO NOT COMMIT)

- **Secrets:** `.env` (real Gemini key).
- **Databases:** `dietrisknet.db`, `test.db`.
- **User uploads:** `backend/uploads/*` (92 user meal photos).
- **Runtime binaries:** `runtime/ollama/` (3.7 GB Ollama + CUDA DLLs).
- **Downloaded LLM model blobs:** `runtime/ollama/models/blobs/*`.
- **Caches / build output:** `backend/.venv/`, `frontend/node_modules/`,
  `frontend/.next/`, `__pycache__/`, `.pytest_cache/`,
  `frontend/lint_output.txt`.
- **Temporary debug:** `reg_bad.png`, `reg_bad.txt`, `reg_green.png`.

---

## 16. Files Requiring Manual Decision

| Path | Why it needs a decision | Recommendation |
|---|---|---|
| `.claude/settings.json` | Claude Code project permission allowlist (no secrets). Useful to share, tool-specific. | Commit if the team wants shared tool config; otherwise ignore. Low risk either way. |
| `.claude/settings.local.json` | Machine-local permission overrides (24 KB, session-accumulated). | **Ignore** (add `.claude/settings.local.json`). |
| `runtime/ollama/` | 3.7 GB portable Ollama + model blobs; recreatable. | **Exclude**; ignore via `runtime/`; setup scripts already document transfer. |
| `reg_bad.png` / `reg_bad.txt` / `reg_green.png` | Root-level registration debug artifacts. | Delete or ignore; do not commit. |
| `docs/evaluation/_meal_timestamps.json` | Upload-filename→timestamp map used by the E2E harness for reproducible timestamps (6.8 KB). It is **useful reproducibility evidence** (only filenames, no image content). | **Keep / commit** as evidence. |
| `docs/evaluation/multifood/_P*.png` (5 images) | Synthetic multi-food probe images (~2.4 MB) substantiating the Phase 4 multi-food section. | **Keep / commit** as evidence. |
| `backend/evaluation/reports/*.png` | Generated benchmark charts backing thesis tables 5.1–5.4. | **Keep / commit** as evidence (regenerable, but they are the cited artifacts). |
| `frontend/.vercel/README.txt` | Vercel CLI metadata. | Exclude (ignore `frontend/.vercel/`). |

---

## 17. Remaining Warnings

1. Stale "EfficientNet-B0 / 360 classes" text in `docs/PROJECT_STRUCTURE.md`
   and `docs/RUN_PROJECT.md` (must be corrected before thesis submission).
2. Thesis risk-fusion wording "Low/Moderate/High" (should be 4 levels) and
   `docs/thesis/09_results.md` stub numbers + stale test counts (189 current).
3. `runtime/ollama/` and `frontend/.vercel/` not yet gitignored.
4. `README.md` "clinical-grade classifiers" phrasing — reword for consistency.
5. Model weights (178 MB) are tracked in normal Git — fine for capstone;
   Git LFS preferable going forward.
6. Non-blocking Pydantic v2 deprecation warnings and dev
   `SECRET_KEY`-insecure-default runtime warning.

---

## 18. Blocking Issues

**NONE.**

- No blocking secret (only gitignored `.env`).
- No model, threshold, formula, weight, mapping, UI, or Phase 4 evidence was
  changed.
- No destructive commands were run (`git add/commit/push/reset/clean`,
  `git lfs migrate`, file deletion) — the tree is intact.

---

## 19. Final Recommendation

1. **Correct the 6 documentation contradictions** (§10) before thesis
   submission — none affect frozen Phase 4 evidence.
2. **Apply the `.gitignore` additions** in §9 (documented; approved here before
   editing) so `runtime/`, `.claude/settings.local.json`, `reg_*`,
   `frontend/.vercel/` stay out of the commit.
3. **Commit** the file groups in §14, **exclude** §15, and **decide** §16
   (recommendations above). Keep model weights tracked.
4. Do **not** run `git lfs migrate` or retrain anything in Phase 5.

**The repository is SAFE to create the final capstone commit after the
documentation corrections and `.gitignore` additions are applied.**
