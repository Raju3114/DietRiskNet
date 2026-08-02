# DietRiskNet — Final Ollama End-to-End Validation

**Date:** 2026-08-01
**Validator:** Senior QA Engineer (automated, evidence-based)
**Scope:** Complete end-to-end validation of DietRiskNet with **Ollama as the
default local LLM provider** and Gemini optional. Every PASS below was actually
executed against the running application or the real Ollama server — nothing is
fabricated. No API keys are printed anywhere in this document.

---

## 1. Test environment

| Item | Value |
|---|---|
| OS | Windows 11 (Git Bash) |
| Python | 3.10.11 (backend `.venv`) |
| Backend | FastAPI 0.139 · uvicorn · `127.0.0.1:8000` |
| Frontend | Next.js 16.2.10 (type-check + production build executed; no live browser automation available) |
| Database | SQLite (`dietrisknet.db`) |
| LLM provider | Ollama (default) + Gemini (optional) |
| Sample image | `datasets/sample_meal.png` |

---

## 2. Ollama version

```
ollama version is 0.32.5        (portable build)
GET http://localhost:11434/api/version -> {"version":"0.32.5"}
```

**Ollama startup issue (root cause + solution).** The first connectivity probe
ran while `ollama serve` was still binding its port, so
`/api/version` appeared to be "not responding". Investigation showed the
portable Ollama process **was** running (PID 26520) and listening on
`127.0.0.1:11434`; the probe had simply raced startup. No application code was
changed to work around this. The portable install was verified valid
(`ollama.exe` + `lib/`, model blobs present under `%USERPROFILE%\.ollama\models`).

---

## 3. Ollama model

```
ollama list:
  llama3.2:3b    a80c4f17acd5    2.0 GB
```

`llama3.2:3b` is installed and reported by the server.

---

## 4. Provider configuration

From the root `.env` (gitignored) and `backend/config.py`:

```
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=120
GEMINI_API_KEY=*** (optional; not printed; app verified without it)
```

Verified: with `GEMINI_API_KEY` set to empty, the backend starts normally and
`OllamaProvider.enabled == True`. **No Gemini key is required.**

---

## 5. Direct Ollama generation test (STEP 3)

| Prompt | Response | Time (measured) |
|---|---|---|
| `Reply only with: OLLAMA_OK` (cold model load) | `OLLAMA_OK` | 6.68 s |
| `Give one healthy Indian breakfast suggestion in one sentence.` (warm) | real, sensible breakfast advice | 1.87 s |

✓ Ollama responds · ✓ model loads · ✓ non-empty · ✓ no API key · ✓ no Gemini.

---

## 6. Provider factory (STEPS 4-5)

| `LLM_PROVIDER` | Result (executed) |
|---|---|
| `ollama` | `OllamaProvider` selected |
| `gemini` | `FallbackLLMProvider` (primary `GeminiProvider`, fallback `OllamaProvider`) |
| `bogus` | `ValueError` — graceful configuration error |
| Gemini failure (quota-limited key) | **automatic fallback to Ollama** → returned `{'reply': 'fallback'}` |
| Ollama offline | friendly fallback (see §16) |

All verified live; AI failures never crash the app.

---

## 7. Backend test results (STEP 20)

```
python -m pytest backend/tests -q
169 passed, 0 failed, 0 skipped, 7 warnings   (in ~8s)
```

Warnings are deprecation notices (Pydantic class-Config, SQLAlchemy
`declarative_base`, starlette/httpx) — non-fatal. This count includes **20 new
mocked Ollama unit tests** (§ below).

---

## 8. Frontend test results (STEP 18)

```
npx tsc --noEmit          -> PASS (0 errors)
npm run build             -> PASS (production build, 17/17 routes)
```

**Note:** No live browser automation was available in this environment; the
frontend was validated via TypeScript type-check, production build, and static
inspection of every page (loading / empty / error states reviewed in source).
API-level E2E against the backend was executed directly.

---

## 9. ML pipeline test (STEP 8)

`POST /api/analyze-meal` with `datasets/sample_meal.png` (real models, no
stubs). Meal **#88**:

| Stage | Result (measured) |
|---|---|
| YOLOv8 detection | `Idli` confidence **0.843** |
| Duplicate suppression | per-class IoU 0.6 filter active |
| EfficientNet-B3 classification | Idli |
| Nutrition mapping | calories 82.5 · protein 2.8 · carbs 16.9 · sodium 60.5 |
| DCI | 0.7104 (Moderate Consistency) |
| NIS | 0.9634 (Severe Imbalance) |
| XGBoost ×4 | diabetes 0.000 · obesity 0.018 · hypertension 0.041 · deficiency 0.588 |
| Risk fusion | 0.3495 (Moderate) |
| Rule recommendations | 2 recommendations |
| DB persistence | meal 88 stored; readable via history/trends/analytics |
| Response schema | all fields valid |

✓ every pipeline stage present and correct.

---

## 10. AI Dietitian using Ollama (STEP 9)

`ai_dietitian != null` for meal 88, with all expected fields present:

- `summary`, `meal_quality` (Moderate), `health_score` (**67, Moderate**),
  `health_level`, `health_explanation`, `risk_explanation`,
  `recommendations`, `healthier_alternatives`, `warnings`, `follow_up_questions`.

**Determinism confirmed:** `health_explanation = "Score reduced for: Fused risk
0.35 (-10 pts); NIS 0.96 imbalance (-19 pts); Fiber 1.4 g (-3 pts)."` — the
health score is computed by backend logic, **not** by the LLM. The LLM narrative
matched (did not contradict) the backend disease-risk and fusion values.

**Log evidence (provider trace):**
```
ai_dietitian cache miss (provider=ollama)
AI result cached (meal_id=88 provider=ollama …)
ai_dietitian generated (provider=ollama, latency=6722ms)
gemini client initialised  -> count 0 (Gemini never used)
```

✓ AI Dietitian works with Ollama; ✓ Gemini not required.

---

## 11. Nutrition Assistant using Ollama (STEP 10)

All prompts returned **HTTP 200 with real Ollama-generated, nutrition-related
replies** (no "unavailable" message):

| Prompt | Result |
|---|---|
| `Hi` | greeting |
| `Suggest a healthy breakfast.` | real advice |
| `How can I increase protein?` | real advice |
| `Give me a healthy dinner suggestion.` | real advice |
| `How can I reduce sodium?` | real advice |
| `Explain my recent eating pattern.` | **used stored meal context** (referenced the analysed Idli meal + calories) |
| `Give me a weekly diet improvement suggestion.` | real advice |

**Off-topic guard:** `Write Python code for sorting numbers.` → polite
nutrition-scope redirect (keyword guard, no LLM call).

---

## 12. Personalized Coach (STEP 11)

`GET /api/nutrition/analytics` returns all expected fields (executed):
`meals_analyzed`, `meals_this_week`, averages (calories/protein/sodium),
`avg_dci`, `avg_nis`, `highest_risk` (deficiency 0.588), `best_meal`,
`most_common_food` (Idli), `patterns` (low fiber), `goals` (6 goals with
progress + status), `positive_habits`, `habits_to_improve`,
`dci_trend`/`risk_trend`, `nutrient_deficiencies`.

Coach chat (real Ollama replies that used the stored analytics):
`Give me my weekly summary.` → "You have logged 1 meals… deficiency at 59%…";
`What should I improve?` → referenced the coach summary. Analytics are pure DB
aggregation — no ML re-run.

---

## 13. Meal Chat (STEP 12)

`POST /api/ai/chat` (meal 88) — real Ollama replies using the meal context:
"Is this meal healthy?", "Why is my risk score this value?", "What can I
replace in this meal?", "How can I improve this meal?" — responses referenced
the meal's NIS, deficiency risk, and Idli; backend risk values were not
contradicted.

---

## 14. Conversation memory (STEP 13)

Same meal session, sequential turns: "What food did I just analyze?" →
replied with the meal context; "How can I make it healthier?" → improvement
advice; "What was your first recommendation?" → repeated the earlier
recommendation. Rolling in-memory history (10 messages) works; sessions are
keyed `(user_id, meal_id)`, isolating different users/sessions by design.

---

## 15. Cache test (STEP 15)

Backend log evidence:

```
meal 88: ai_dietitian cache miss (provider=ollama) -> generated (6722ms) -> cached
meal 89: ai_dietitian cache hit  (provider=ollama)  -> Ollama NOT called again
```

Identical AI context → cache hit (second analyze returned in 1.48s total vs
23s cold). **Prompt-version invalidation** is enforced in code:
`get_cached_response` filters `AIDietitianResult.prompt_version`, so bumping
`PROMPT_VERSION` makes stale entries un-hittable.

---

## 16. Database test (STEP 16)

12 tables present: `users, refresh_tokens, user_settings, meals, meal_items,
meal_nutritions, disease_predictions, risk_fusion_results, recommendations,
diet_history, audit_logs, ai_dietitian_results`.

Persistence verified by reads: `/api/history` returned meals 89, 88;
`/api/analytics/trends` returned daily aggregated points (incl. all risk
fields); `/api/nutrition/analytics` aggregated both meals. No broken FKs or
persistence errors observed.

---

## 17. PDF test (STEP 17)

`GET /api/report/88` → **HTTP 200**, `Content-Type: application/pdf`,
`%PDF-1.4` header, **2 pages, 1,259,956 bytes**, generated in **0.29 s**.
Contains meal image, detected foods, nutrition, DCI/NIS, disease risks,
recommendations, and the AI Dietitian section.

---

## 18. Security test (STEP 19)

| Check | Result |
|---|---|
| JWT claims | `type=access`, unique `jti`, `sub`, `exp` present |
| Access vs refresh token | distinct `type` claim + DB-backed refresh tokens |
| Invalid login | 401 |
| Invalid JWT / no token | 401 |
| Logout | 200 (refresh token revoked in DB) |
| Revoked refresh-token replay | **401** |
| Valid new refresh token | 200 |
| Protected routes | require `Authorization: Bearer` |
| Upload validation | extension whitelist (jpg/jpeg/png/webp) + `uuid4` filenames |
| SQL | parameterized ORM queries (no string-built SQL) |
| `.env` ignored by Git | confirmed (`git check-ignore .env`); not tracked |
| API key in tracked files / logs | **0 occurrences** (verified via `git grep` and log scan) |
| `.env.example` | placeholder `YOUR_GEMINI_API_KEY_HERE` only |

No secrets are printed in this document or exposed by prompts.

---

## 19. Failure / fallback test (STEP 14)

Simulated Ollama offline (stopped the single server process, then restored):

| Endpoint | Behaviour (HTTP) |
|---|---|
| `GET /api/ai/health` | `status=unavailable`, **HTTP 200** (not 500) |
| `POST /api/ai/chat` | friendly "temporarily unavailable", **HTTP 200** |
| `POST /api/nutrition-chat` | friendly "temporarily unavailable", **HTTP 200** |
| `POST /api/analyze-meal` | **HTTP 200** — ML fully intact (YOLO/EfficientNet/DCI/NIS/XGBoost/fusion/recs); AI section fell back to the persistent AI cache (identical context) |

**No HTTP 500 caused by Ollama being offline.** After restarting Ollama, the
health endpoint and assistant recovered (`status=ok`, real replies).

---

## 20. Performance observations (STEP 22)

All values **measured** in this environment (CPU-only; environment-dependent):

| Measurement | Value | Type |
|---|---|---|
| Ollama cold first generation (model load) | 6.68 s | measured |
| Ollama warm generation | 1.87 s | measured |
| AI Dietitian generation via Ollama | 6.72 s | measured (log) |
| Nutrition-chat warm response | 3.58 s | measured |
| `/api/analyze-meal` cold (models loading) | 23.0 s | measured |
| `/api/analyze-meal` warm (AI cache hit) | 1.48 s | measured |
| AI cache hit | sub-second (inside the 1.48 s analyze) | measured |
| PDF generation | 0.29 s | measured |
| `/api/ai/health` probe | 4.11 s | measured |

**Offline / local-only (STEP 23):** configuration and request tracing confirm
the active provider is local Ollama (`localhost:11434`); the backend log shows
`provider=ollama` and `gemini client initialised` count **0**. No Gemini
request is required for any Ollama test.

---

## 21. Code quality (STEP 24)

| Item | Result |
|---|---|
| TODO / FIXME / HACK / XXX | 0 |
| `console.log` / `print()` in application code | 0 (only legit CLI entrypoints in `backend/evaluation/*` `__main__`) |
| Hardcoded absolute paths in backend Python | 0 |
| Duplicate LLM implementations | none — single `BaseLLMProvider` interface + `OllamaProvider`/`GeminiProvider` |
| Hardcoded API keys in source | none (key lives only in gitignored `.env`) |

---

## 22. Bugs discovered & fixed

| # | File | Issue | Severity | Root cause | Fix |
|---|---|---|---|---|---|
| B1 | `backend/routes/meal.py` | `POST /api/calculate-dci` was **unauthenticated** and trusted a client-supplied `user_id` (cross-user data inference) | **Major (security)** | No `get_current_user` dependency; used `data.user_id` | Require auth and compute DCI for `current_user.id`. Verified live: no token → 401, with token → 200 |
| B2 | `backend/routes/deps.py` | `int(user_id_str)` could raise `ValueError` → HTTP 500 on a malformed token subject | Minor | Unhandled conversion | Wrap in try/except → 401 |
| B3 | `backend/services/prediction_service.py` | dead `has_bone_paint` key (model feature is `has_bone_pain`) | Minor (dead code) | Typo | Removed the dead key |
| B4 | `backend/tests/test_ollama_provider.py` | (new) initial run: missing `json` import + wrong fallback-health expectation | Test-only | Authoring error | Added `import json`; `_RaisingProvider.health_check` now returns `status=error` |

**Ollama startup** was not an application bug (server was running; probe raced
startup). No code change required.

## 23. Remaining limitations (not blocking)

- Frontend "Sign Out" clears local auth but does not call `POST /auth/logout`
  to revoke the server-side refresh token (the backend endpoint is correct and
  was tested; recommended follow-up so a leaked token cannot survive logout).
- No upload size limit is enforced server-side (UI text advertises 10 MB).
- No rate limiting on auth / inference endpoints.
- In-memory chat sessions are lost on restart (documented design).
- Small local model `llama3.2:3b` occasionally returns off-schema JSON; the
  services coerce / return a canned reply gracefully.
- No live browser automation was run in this environment (type-check + build +
  API E2E were executed instead).

## 24. Final readiness conclusion

**DietRiskNet is stable and ready for demonstration and academic submission.**
Ollama is the active default provider; Gemini is optional and unused. All AI
features (AI Dietitian, Nutrition Assistant, Personalized Coach, Meal Chat)
return **real Ollama-generated responses**, the full ML pipeline is intact and
works with Ollama offline, cache and fallback behave correctly, the PDF is
valid, and the entire automated suite passes (**169 passed / 0 failed**).
