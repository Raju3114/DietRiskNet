# DietRiskNet — Viva Preparation (50+ Questions & Answers)

Answers are concise and grounded in the actual implementation. **Know your
numbers:** 118 food classes · 1,014 dishes × 11 nutrients · 4 XGBoost models ·
IoU 0.6 · DCI 0.85/0.70/0.50 · NIS 0.2/0.4/0.6/0.8 · fusion 0.25/0.25/0.20/0.15/0.10/0.05 ·
12 tables · 169 tests · Ollama `llama3.2:3b` (default) · Gemini optional.

---

## A. YOLOv8 (Detection)

**Q1. Why YOLOv8 for food detection?**
A. One-stage detector — one forward pass predicts boxes and classes in real
time. Ultralytics gives a clean API and strong pretrained weights for our
CPU-only deployment. We use 18 food-related detection classes.

**Q2. What does the detector output?**
A. Bounding boxes `(x1,y1,x2,y2)` with class names and confidence scores.

**Q3. How do you stop one dish being counted twice?**
A. A per-class IoU filter (`_remove_duplicate_detections`) removes
lower-confidence boxes overlapping a higher-confidence box of the same class
by IoU > 0.6, keeping the highest-confidence detection.

**Q4. Why 0.6 for the IoU threshold?**
A. A tuned midpoint — high enough to suppress genuine duplicates, low enough
not to drop distinct nearby foods.

**Q5. What if the detector finds nothing?**
A. `analyze-meal` falls back to treating the whole image as one region for
classification, then continues the pipeline.

## B. EfficientNet (Classification)

**Q6. Why EfficientNet-B3?**
A. Compound scaling of width/depth/resolution gives strong accuracy per FLOP —
a good CPU trade-off. We use 118 Indian food classes.

**Q7. What is the fallback architecture?**
A. If the B3 weights are missing, we load EfficientNet-B0 (crop size 224 vs
300 for B3), detected from the state-dict stem width.

**Q8. How is each crop classified?**
A. Resized to the model crop size, normalized (ImageNet stats), passed through
the network, softmax → top class + confidence.

## C. XGBoost (Disease Prediction)

**Q9. Why XGBoost for risk prediction?**
A. Gradient-boosted trees excel on small structured tabular features, are fast,
and give probabilities we can fuse and explain.

**Q10. Which four models do you use?**
A. Diabetes, obesity, hypertension, nutritional deficiency — four independent
binary/multi-class classifiers.

**Q11. What features feed them?**
A. Profile (age, gender, BMI/height/weight, existing conditions) plus
meal-derived nutrition (sodium, calories, fiber) and engineered RDA percentages.

**Q12. Are the features all real inputs?**
A. Several are heuristic/hardcoded (e.g. estimated HbA1c from conditions,
stress/sleep defaults, hemoglobin fixed). This is documented as a limitation —
a simplified "profile + meal-derived" mode.

**Q13. How is obesity risk computed?**
A. The obesity model is multiclass; risk = sum of the overweight+obese class
probabilities.

## D. DCI & NIS

**Q14. What is DCI?**
A. Dietary Consistency Index — `1 − CV` of daily calories over the last 7
days (≥2 days of history), else a single-meal macro-balance fallback against
55/15/30 carbs/protein/fat.

**Q15. What is NIS?**
A. Nutritional Imbalance Score — mean relative deviation from RDI across six
nutrients (Calories, Protein, Carbs, Fat, Sodium, Fiber).

**Q16. Why a threshold classifier instead of intervals?**
A. Interval ranges are ambiguous at shared boundaries (a value can match two
levels and depend on dict order). Point thresholds make classification
deterministic and order-independent.

**Q17. DCI thresholds?** A. 0.85 / 0.70 / 0.50 → High / Moderate / Low / Very Low.
**Q18. NIS thresholds?** A. 0.2 / 0.4 / 0.6 / 0.8 → Balanced / Mild / Moderate / High / Severe.

## E. Risk Fusion

**Q19. How is the fused risk computed?**
A. `0.25·(1−DCI) + 0.25·NIS + 0.20·diabetes + 0.15·obesity + 0.10·hypertension + 0.05·deficiency`, bounded to [0,1].

**Q20. Why those weights?**
A. DCI/NIS and diabetes dominate (metabolic drivers); deficiency contributes
least. The weights live in a JSON config, so they are tuneable without code.

**Q21. What are the risk levels?** A. ≤0.25 Low, ≤0.50 Moderate, ≤0.75 High, else Critical.

## F. Nutrition Mapping

**Q22. What is the nutrition source?**
A. A curated CSV of 1,014 Indian dishes × 11 nutrients (calories, carbs,
protein, fats, free sugar, fiber, sodium, calcium, iron, vitamin C, folate).

**Q23. How does lookup work?**
A. Four tiers: exact → alias/synonym → deterministic normalization → fuzzy
(`difflib`). A `display_name` maps redundant modifiers for a cleaner UI.

**Q24. How are values scaled?**
A. CSV values are per 100 g; each item is scaled by its serving weight
(`DEFAULT_SERVING_WEIGHTS`, e.g. idli 60 g, dosa 180 g; fallback 100 g).

## G. Recommendations

**Q25. How do ExplainDiet rules fire?**
A. Threshold triggers with evidence: sodium > 800 mg, free sugar > 15 g,
calories > 800 kcal, fiber < 2 g, and elevated risk scores — each producing a
category + content + clinical explanation.

**Q26. What is the health score?**
A. A deterministic [0–100] score computed by the backend (fusion penalty ≤30,
NIS ≤20, DCI/calories/sodium/sugar/fiber penalties) — the LLM only narrates it.

## H. Ollama

**Q27. Why make Ollama the default provider?**
A. Fully local, private, offline, and **no API key** — ideal for a capstone and
for avoiding cloud costs.

**Q28. How does the app talk to Ollama?**
A. `OllamaProvider` calls the local REST API (`/api/generate`,
`/api/version`, `/api/tags`) at `http://localhost:11434` with model
`llama3.2:3b`.

**Q29. How is the provider selected?**
A. `LLM_PROVIDER` env var → `LLMProviderFactory`. `ollama` default, `gemini`
optional; unknown values raise a clear configuration error.

**Q30. What happens if Ollama is offline?**
A. AI features degrade gracefully — `ai_dietitian: null`, friendly chat reply,
rule-based output. `GET /api/ai/health` reports `unavailable`. **No HTTP 500.**

## I. LLMs / Prompting

**Q31. Why a provider-agnostic interface?**
A. `BaseLLMProvider` lets us swap Ollama/Gemini/OpenAI without touching business
logic; services depend only on the interface.

**Q32. How do you prevent LLM hallucination of nutrition/risk?**
A. The LLM only receives structured, computed ML output and is never asked to
compute numbers; the health score and risks come from deterministic backend
logic. Prompts constrain it to explain, not invent.

**Q33. How do you get structured output?**
A. Ollama `format: "json"` and Gemini `response_mime_type=json`; responses are
parsed/coerced with safe defaults.

**Q34. What is the AI cache?**
A. `AIDietitianResult` rows keyed by a SHA-256 hash of the full context +
`prompt_version`, so identical contexts never call the LLM twice.

## J. AI Dietitian

**Q35. When does the AI Dietitian run?**
A. Only after the meal + nutrition + predictions are persisted, so it can never
break the pipeline.

**Q36. What does it return?** A. Summary, meal quality, deterministic health
score/level/explanation, risk explanation, recommendations, healthier
alternatives, warnings, follow-up questions.

**Q37. Can the AI change the disease risk?**
A. No — it only explains the precomputed values; the deterministic core is
authoritative.

## K. Chatbot / Nutrition Assistant / Coach

**Q38. How does meal chat work?**
A. `POST /api/ai/chat` loads the persisted meal context (no ML re-run), keeps a
rolling 10-message in-memory history keyed `(user_id, meal_id)`, and answers
via the LLM.

**Q39. How is the Nutrition Assistant different?**
A. It is general-purpose and works with zero meals; it can include stored meal
history for personalisation and uses a keyword guard for off-topic questions.

**Q40. What does the Personalized Coach do?**
A. Deterministic analytics over the last 14 meals (averages, DCI/NIS, risk
trend, patterns, smart goals with 0–1 progress) injected into the chat context.
No ML re-run.

**Q41. How do you ensure nutrition-related answers?**
A. A system prompt plus an off-topic keyword guard; unrelated topics get a
polite redirect.

## L. Database

**Q42. How many tables and which?**
A. 12: users, refresh_tokens, user_settings, meals, meal_items, meal_nutritions,
disease_predictions, risk_fusion_results, recommendations, diet_history,
audit_logs, ai_dietitian_results.

**Q43. How is auth persisted?** A. Refresh tokens stored in `refresh_tokens`
with expiry and `is_revoked`; access tokens are stateless JWTs.

**Q44. How are deletes handled?** A. ORM `cascade="all, delete-orphan"` +
`ondelete=CASCADE` FKs, so child rows cascade.

## M. FastAPI / Backend

**Q45. Why FastAPI?** A. Async, typed with Pydantic, auto OpenAPI docs, easy DI.

**Q46. How is auth enforced?** A. `HTTPBearer` + `get_current_user` dependency
decodes the JWT (`type=access`) and loads the user; malformed/expired → 401.

**Q47. How is upload validated?** A. Extension whitelist (jpg/jpeg/png/webp) +
UUID filenames; files are saved to a dedicated uploads directory.

## N. Next.js / Frontend

**Q48. How does the frontend talk to the backend?**
A. `services/api.ts` (`apiFetch`) with JWT header, 15 s timeout, and a
one-time token refresh on 401; a self-healing base URL fallback.

**Q49. How is auth state stored?** A. Zustand + `persist` (localStorage) for
tokens; ProtectedRoute redirects unauthenticated users to `/login`.

**Q50. Which pages exist?** A. Landing, Login, Register, Dashboard, Upload,
Analysis, Predictions, Recommendations, Trends, History, Nutrition (coach +
assistant), Profile, Research, About.

## O. Security

**Q51. How are passwords stored?** A. bcrypt (passlib) hash; never plaintext.
**Q52. What protects against token replay?** A. Access/refresh `type` claims,
`jti` uniqueness, expiry, and DB-backed revocation of refresh tokens.
**Q53. Where do secrets live?** A. Gitignored `.env`; `.env.example` uses
placeholders; no keys in source, docs, or logs.
**Q54. Are queries injection-safe?** A. Yes — SQLAlchemy ORM/filter produces
parameterized SQL.

## P. Testing & Evaluation

**Q55. How is the project tested?**
A. 169 backend tests (thresholds, duplicate detection, AI cache, chat, coach,
assistant, report, evaluation, and 20 mocked Ollama provider tests) + frontend
`tsc` + production build.

**Q56. How is the AI benchmark made deterministic?**
A. By default a fake client is used; `LLM_BENCHMARK_REAL=1` measures the real
configured provider (Ollama).

**Q57. What metrics does the evaluation module report?** A. Per-stage latency
(mean/median/p95), memory, CPU, cache hit-rate, PDF size — NOT model accuracy.

## Q. Limitations & Novelty

**Q58. Main limitations?** A. Pre-trained models without reported retraining
accuracy; CPU-only; some hardcoded XGBoost inputs; no rate limiting/migrations;
in-memory chat; small local model may return off-schema JSON.

**Q59. What is genuinely novel here?**
A. The integration (vision → regional nutrition → disease-risk → grounded AI),
the **deterministic order-independent threshold classifier** for DCI/NIS, the
**fail-safe grounded AI layer**, and a **provider-agnostic LLM architecture**
(Ollama default, Gemini optional) with automatic fallback.
