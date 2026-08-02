# DietRiskNet — Viva Preparation Guide

*A complete Q&A bank built from the actual implementation. Adapt the
answers to your own words, but keep the facts accurate to the system.*

---

## How to use this guide

1. Practise each answer out loud — short, structured, confident.
2. Prepare your own **one-line summary** of the project (see Section 1).
3. Know your **numbers**: 149 tests, 12 tables, 27 endpoints, 1,014-dish
   nutrition database, 118 food classes, 4 XGBoost models, IoU threshold 0.6,
   DCI thresholds 0.85/0.70/0.50, NIS thresholds 0.2/0.4/0.6/0.8, 10-message
   chat window, 5-meal coach window (14 for analytics).

---

# Part A — 100 Technical Questions with Model Answers & Follow-ups

## A. YOLOv8 (6)

**Q1. Why did you use YOLOv8 for food detection?**
A. YOLOv8 is a single-shot object detector — one forward pass predicts all
bounding boxes and class probabilities simultaneously, giving real-time
inference. Ultralytics provides a clean API, strong pre-trained weights, and
a good accuracy/speed trade-off for our CPU-only deployment. Our detector is
fine-tuned for 18 food-related classes.
*Follow-up:* What is the difference between one-stage and two-stage detectors?
→ One-stage predicts boxes+classes directly in one pass; two-stage (Faster
R-CNN) proposes regions first, then classifies — more accurate but slower.

**Q2. What exactly does the detector output?**
A. For each food it returns `(x1, y1, x2, y2)` pixel coordinates, a
confidence score, and a class name. These boxes define the crops we pass to
the classifier.

**Q3. How did you handle duplicate detections of the same dish?**
A. YOLO's default NMS kept two highly-overlapping boxes for the same class,
so I added a per-class IoU filter: within a class, boxes are sorted by
confidence and any lower-confidence box overlapping a kept one by more than
0.6 IoU is removed. This stops one dish being counted twice in the calorie
total.
*Follow-up:* What threshold and why? → 0.6 — a middle ground between
aggressively removing duplicates and keeping two distinct items of the same
type that touch on the plate.

**Q4. What is NMS and how does it work?**
A. Non-Maximum Suppression removes overlapping detections of the same object:
boxes are ranked by confidence, the highest is kept, boxes with high IoU to it
are suppressed, and the process repeats.

**Q5. What happens if YOLO detects nothing?**
A. The pipeline falls back to classifying the whole image as one food region
and logs a warning, so the meal is still analysed instead of failing.

**Q6. What is IoU and how do you compute it?**
A. Intersection over Union = (area of overlap) / (area of union) of two boxes,
ranging 0 (no overlap) to 1 (identical). It is computed from the box
coordinates directly in Python.

## B. EfficientNet-B3 (5)

**Q7. Why EfficientNet-B3?**
A. EfficientNets scale depth, width, and resolution together using neural
architecture search, giving state-of-the-art accuracy per FLOP. B3 is a good
middle point — more accurate than B0 yet compact enough (~126 MB) for our
memory-constrained server. We also ship a B0 fallback for low-memory
environments.
*Follow-up:* What is compound scaling? → Scaling all three dimensions
together rather than one at a time.

**Q8. What is the model's task here?**
A. Pure food classification: given a cropped region it predicts one of 118
Indian food classes with a confidence. It does not locate food — that is
YOLO's job.

**Q9. How do you preprocess a crop?**
A. Resize to 300×300 (B3) or 224×224 (B0), convert to a tensor, and run in
eval mode with gradients disabled on the CPU.

**Q10. Why a two-stage cascade instead of one model?**
A. Detection and fine-grained classification are different problems. YOLO is
strong at localisation but was trained on coarse classes; EfficientNet is
better at fine-grained visual recognition. The cascade is modular — each
model can be swapped independently.

**Q11. What is the class space and where is it stored?**
A. 118 food classes stored in `efficientnet_classes.json`, loaded with the
model to map the top logit to a dish name.

## C. Nutrition Analysis (6)

**Q12. Where does your nutrition data come from?**
A. A curated CSV of 1,014 Indian dishes × 11 nutrients (calories, protein,
carbs, fat, sugar, fiber, sodium, calcium, iron, vitamin C, folate).

**Q13. How do you match a classifier output to a nutrition row?**
A. A four-tier lookup: exact dish match → alias/synonym map → deterministic
normalisation → fuzzy matching with `difflib`.

**Q14. How is a single item's nutrition computed?**
A. CSV values are per 100 g; we multiply by `weight/100`, where weight is a
per-dish serving weight (default 100 g), then aggregate all items for the
meal.
*Follow-up:* What are serving weights? → A lookup table per dish (e.g. idli
60 g, samosa 100 g), defaulting to 100 g.

**Q15. What if a food is not found?**
A. The lookup falls through the tiers to a default profile and logs the
fallback — the pipeline never crashes.

**Q16. What is `display_name` and why do you have it?**
A. The classifier/CSV may return names like "Vegetable samosa"; a
display-name table maps redundant modifiers to friendlier labels ("Samosa")
for the UI, while preserving the original name internally.

**Q17. How do you ensure totals are correct?**
A. Aggregation is a pure sum over scaled items; tests assert known inputs
produce expected totals, and duplicate suppression prevents double-counting.

## D. DCI (5)

**Q18. What is DCI and what does it measure?**
A. Dietary Consistency Index, 0–1, measuring how consistent intake is. High
DCI = consistent eating. With ≥2 days of history, `DCI = 1 − CV` (CV =
coefficient of variation of daily calories); otherwise a single-meal
macro-balance fallback against 55/15/30 carb/protein/fat targets.

**Q19. How do you map a DCI score to a level?**
A. Threshold classification: ≥0.85 High, ≥0.70 Moderate, ≥0.50 Low, else
Very Low. Thresholds live in a data-only JSON config; the direction lives in
code.

**Q20. Why did you replace interval ranges with thresholds?**
A. Intervals `[low, high]` overlap at boundaries (a score of 0.85 matched two
levels) and the winner depended on JSON key order. Thresholds use a single
inequality per level, evaluated strictest-first, so every score maps to
exactly one level — deterministic and provable.
*Follow-up:* Prove it. → Each level checks `score >= value` (or `< value`)
against one point; the loop breaks on the first match and a catch-all covers
the rest, so there are no overlaps and no gaps.

**Q21. What does DCI = 1.0 mean?**
A. Perfect consistency — e.g. identical daily calories — mapped to High
Consistency.

**Q22. How does DCI affect risk?**
A. It contributes `0.25 × (1 − DCI)` in the fusion formula — higher
consistency lowers fused risk.

## E. NIS (5)

**Q23. What is NIS?**
A. Nutritional Imbalance Score = mean relative deviation of the meal's
nutrients from recommended daily intakes: `mean(|actual − RDI| / RDI)`.
Lower is better.

**Q24. Which nutrients does NIS consider?**
A. Six: calories, protein, carbs, fat, sodium, fiber — each compared to its
RDI.

**Q25. How is NIS classified?**
A. Thresholds: <0.20 Balanced, <0.40 Mild, <0.60 Moderate, <0.80 High, else
Severe Imbalance.

**Q26. What does NIS = 0 mean?**
A. The meal exactly matches every RDI — perfectly balanced.

**Q27. How does NIS relate to disease risk?**
A. It enters fusion as `0.25 × NIS`; larger imbalance raises fused risk.

## F. XGBoost (6)

**Q28. Why XGBoost for disease prediction?**
A. XGBoost is a gradient-boosted tree ensemble that is fast, robust to
scaling, handles tabular data well, and outputs calibrated probabilities. It
fits our small structured feature vectors and runs in milliseconds on CPU.

**Q29. How many models and for what?**
A. Four independent classifiers: diabetes, obesity, hypertension, and
nutritional deficiency — each returns a risk probability.

**Q30. What features feed the diabetes model?**
A. Engineered features: age, gender, BMI, hypertension/heart-disease history,
and HbA1c/glucose estimates derived from the profile and meal data.

**Q31. How is BMI computed?**
A. `weight_kg / (height_m)²`, with height converted from cm.

**Q32. What does `predict_all` return?**
A. A dict of four risk probabilities
`{diabetes_risk, obesity_risk, hypertension_risk, deficiency_risk}` used by
the fusion engine and stored per meal.

**Q33. What if a model file is missing or prediction fails?**
A. Each predictor returns a fallback probability and logs the error. This is
a known fail-open behaviour (identified in review) — a future improvement is
to fail closed.

## G. Risk Fusion (4)

**Q34. What is the fusion formula?**
A. `Fused = 0.25·(1−DCI) + 0.25·NIS + 0.20·diabetes + 0.15·obesity +
0.10·hypertension + 0.05·deficiency`, then mapped to Low/Moderate/High.

**Q35. Why weighted rather than a simple average?**
A. Weights reflect clinical and data confidence and are configurable in a
JSON file, so they can be tuned without code changes.

**Q36. Why does DCI use `1 − DCI`?**
A. Fusion is a risk score where higher = worse, so high consistency (high
DCI) must reduce risk — hence `1 − DCI`.

**Q37. How is the output used?**
A. The fused score and level are stored per meal, shown on the dashboard and
predictions pages, and included in the PDF report.

## H. Recommendation Engine (4)

**Q38. How does the ExplainDiet rule engine work?**
A. Threshold-triggered rules on nutrients and risks — e.g. sodium > 800 mg or
hypertension risk > 0.4 → "reduce salt"; sugar > 15 g → "whole grains";
calories > 800 → "portion control". Each rule emits category, content, and an
explanation.

**Q39. Why rule-based rather than ML-based?**
A. Rules are deterministic, explainable, and auditable — important for a
medical-adjacent system. Every output is traceable to the input that
triggered it.

**Q40. What happens if no rule fires?**
A. A fallback "Excellent meal balance!" recommendation is emitted so the user
always receives guidance.

**Q41. How do recommendations relate to predictions?**
A. They consume the same predicted risks, so the advice is consistent with
(not contradictory to) the risk scores.

## I. Gemini / AI Dietitian (8)

**Q42. What role does Gemini play?**
A. It is an explanation and personalisation layer only. It receives the
structured ML output (foods, nutrition, DCI, NIS, predictions, fusion, rule
recommendations, user profile) and returns a summary, meal quality, risk
explanation, recommendations, healthier alternatives, warnings, and follow-up
questions.

**Q43. What does Gemini NOT do?**
A. It never performs detection, classification, nutrition calculation, or
disease prediction — those stay with the deterministic pipeline.

**Q44. How is the health score computed?**
A. Deterministically in the backend from DCI, NIS, fusion score, calories,
sodium, sugar, and fiber — Gemini only explains it, it never generates it.
*Follow-up:* Why? → The score must be reproducible and testable; the LLM
cannot be the source of truth for a number.

**Q45. What if Gemini fails or the key is missing?**
A. `ai_dietitian` is set to null and the rule-based recommendations stand.
The meal analysis never returns 500 because of Gemini — fail-safe by design.

**Q46. How do you stop Gemini hallucinating diagnoses?**
A. A strict system prompt forbids diagnosing and contradicting backend
predictions, requires JSON-only output, and the client validates the response
against a fixed schema.

**Q47. How is the AI output cached?**
A. Every response is persisted keyed by a SHA-256 `context_hash` of the full
input context. Identical meals never re-invoke the LLM; `prompt_version`
busts stale cache when the prompt changes.
*Follow-up:* What does the hash cover? → Foods, nutrition, DCI, NIS,
predictions, fusion, rule recommendations, and the user profile.

**Q48. How is the provider abstracted?**
A. A `LLMClient` interface with a `GeminiClient` implementation and a
factory, so OpenAI/Claude/Ollama can be added without touching business logic.

**Q49. Why did you choose Gemini over other LLMs?**
A. Google's SDK, strong structured-JSON output, and affordable quotas.
Architecturally it is just one implementation of the `LLMClient` interface.

## J. AI Chat (4)

**Q50. How is the meal-specific chat different from the AI Dietitian?**
A. The Dietitian is a one-shot analysis explanation; the chat is a
conversational assistant grounded in one persisted meal, with rolling
history.

**Q51. How do you avoid re-running the ML pipeline for chat?**
A. `ChatAIService` loads the persisted meal (foods, nutrition, DCI/NIS,
predictions, fusion, rule recommendations) directly from the database — no
inference is re-run.

**Q52. How is conversation memory managed?**
A. An in-memory, thread-safe `ConversationStore` keyed by `(user_id,
meal_id)`, rolling to the last 10 messages, with session-cap and TTL
eviction. It is never persisted to the database.

**Q53. How do you prevent a user reading another user's meal?**
A. The service verifies `meal.user_id == current_user.id`; otherwise it
raises `MealNotFoundError` → HTTP 404.

## K. AI Nutrition Assistant (5)

**Q54. How does the Nutrition Assistant differ from the meal chat?**
A. It is general — it works with zero meals analysed and covers meal
planning, nutrition education, hydration, grocery lists, and cooking.

**Q55. How do you keep it focused on nutrition?**
A. A keyword guard intercepts obvious off-topic questions (politics,
programming, movies, sports, homework) and returns a polite canned reply
without an LLM call; the system prompt reinforces the scope.

**Q56. How does it personalise when the user has history?**
A. It includes the stored meal history (recent foods, nutrition, DCI/NIS,
risks) in the context — again without re-running any ML.

**Q57. What is the off-topic reply?**
A. "I'm DietRiskNet's AI Nutrition Assistant. I specialize in nutrition,
healthy eating, food, meal planning, and dietary guidance."

**Q58. Why intercept off-topic locally rather than trusting the LLM?**
A. It is deterministic, instant, and free — it saves an LLM call for obvious
cases while the prompt still handles ambiguous ones.

## L. Personalized Nutrition Coach (5)

**Q59. What does the coach add on top of the assistant?**
A. Deterministic analytics over stored meal history: averages, DCI/NIS, risk
trend, patterns, and smart goals with progress.

**Q60. How are patterns like "high sodium" detected?**
A. `NutritionAnalyticsService` counts meals in the last five exceeding
thresholds (e.g. sodium > 800 mg) and phrases a sentence if at least three
meet it.

**Q61. How are smart goals and progress computed?**
A. Goals (reduce sodium, increase protein/fiber, consistency, balance,
hydration) get a 0–1 progress score from current averages vs targets, with an
on-track / in-progress / needs-attention status.

**Q62. Why deterministic analytics instead of asking Gemini to generate them?**
A. Deterministic means reproducible, testable, and free — the dashboard
always reflects the database exactly. Gemini only receives the coach summary
to write personalised advice.

**Q63. Where does the dashboard data come from?**
A. `GET /api/nutrition/analytics`, which aggregates the last 14 meals from
the database — no ML, no LLM.

## M. FastAPI (6)

**Q64. Why FastAPI?**
A. Async support, automatic OpenAPI docs, Pydantic validation, dependency
injection, and fast performance — ideal for a typed REST backend.

**Q65. How do you structure routes and services?**
A. Thin routes that validate and orchestrate, and service classes (with
module singletons) that hold business logic — a clean layering that is easy
to test.

**Q66. How is dependency injection used?**
A. FastAPI's `Depends` for DB sessions (`get_db`) and auth
(`get_current_user`), plus constructor injection of `LLMClient` and
`ConversationStore` for testability.

**Q67. How does error handling work?**
A. Routes catch domain errors (`MealNotFoundError`) → 404, `LLMProviderError`
→ a friendly 200 reply, and unexpected exceptions → 500 with a generic
message that never leaks internals.

**Q68. How do you document the API?**
A. Auto-generated Swagger UI at `/docs` and ReDoc at `/redoc`.

**Q69. Why is the meal pipeline deterministic?**
A. Every stage (detection, classification, nutrition, indices, prediction,
fusion) is a pure function of its inputs — the AI layer is the only
non-deterministic part and it runs last.

## N. Next.js (5)

**Q70. Why Next.js App Router?**
A. File-based routing, server/client component model, and an optimised
production build (17 static pages).

**Q71. How is authentication handled client-side?**
A. `ProtectedRoute` reads the JWT from a persisted Zustand store and
redirects to `/login` when absent; API calls attach the Bearer token and
auto-refresh on 401.

**Q72. How do pages get data?**
A. TanStack React Query for server state (dashboard, history, trends) and a
Zustand store for shared app/auth state and the current analysis.

**Q73. How is dark mode implemented?**
A. Tailwind v4 CSS variables under `.dark`, with a semantic-token system
(`text-foreground`, `muted-foreground`, `charcoal-*`) — no global
`!important` overrides.
*Follow-up:* Why did you change from `!important` overrides? → They violated
the Tailwind contract (`.text-white` should mean white) and caused a
specificity arms race; semantic tokens fixed it.

**Q74. How do you avoid hydration errors with localStorage state?**
A. The persisted Zustand stores rehydrate client-side; components guard with
a mounted flag and only access `window` after mount.

## O. SQLAlchemy / Database (5)

**Q75. How many tables and what are they?**
A. 12: users, user_settings, refresh_tokens, meals, meal_items,
meal_nutritions, disease_predictions, risk_fusion_results, recommendations,
diet_history, audit_logs, ai_dietitian_results.

**Q76. How do relationships and cascades work?**
A. One-to-many with `ondelete="CASCADE"` (deleting a user deletes meals and
children) and ORM relationships with `cascade="all, delete-orphan"`.

**Q77. What indexes exist?**
A. On `(meals.user_id, created_at)`, `(diet_history.user_id, logged_date)`,
and `(ai_dietitian_results.meal_id, context_hash)` for the cache lookup.

**Q78. How is the schema created/migrated?**
A. `Base.metadata.create_all()` on startup — creates new tables but does not
alter existing ones. A recognised limitation (no Alembic), noted as future
work.

**Q79. How do you guard against SQL injection?**
A. All queries use SQLAlchemy's parameterised ORM/Core API — no string-built
SQL with user input.

## P. JWT / Security (6)

**Q80. How does authentication work end-to-end?**
A. Register/login issue an access token (24 h) and a refresh token (7 d,
stored and revocable). Protected routes validate the access token;
`/auth/refresh` issues a new pair and revokes the old refresh token.

**Q81. How is the JWT signed and verified?**
A. HS256 with `SECRET_KEY`; tokens carry `type` and `sub` claims and a unique
`jti`. The verifier checks signature, expiry, type, and extracts the user id.

**Q82. How do you protect the secret?**
A. `SECRET_KEY` is read from the environment; the old default is now a
sentinel that triggers a startup warning.

**Q83. What about refresh-token security?**
A. Refresh tokens are stored in DB, revoked on use and logout, and checked
for `is_revoked` — replaying a used token fails.
*Follow-up:* How did you fix the collision bug? → Two tokens created within
the same second were identical (the `exp` claim has second resolution and
the payload had no random component), violating the unique constraint. I
added a unique `jti` UUID to both tokens.

**Q84. How do you validate file uploads?**
A. Extension whitelist (`.jpg/.jpeg/.png/.webp`) and UUID filenames (no
user-controlled path), preventing path traversal.

**Q85. Is CORS configured?**
A. Yes — localhost dev origins plus a regex for Vercel preview domains, with
credentials.

## Q. Testing (4)

**Q86. How many tests and what do they cover?**
A. 149 backend tests across threshold classification, duplicate detection,
AI caching, chat, PDF, evaluation, and nutrition coach — plus frontend type
check and a production build.

**Q87. How do you test without external dependencies?**
A. In-memory SQLite (`StaticPool` + `check_same_thread=False`) and fake
`LLMClient` implementations, so no Gemini call or heavy model load is needed.

**Q88. How do you verify determinism of classification?**
A. Boundary tests and exhaustive sweeps assert every score in a range maps
to exactly one level with no gaps or overlaps.

**Q89. What is the frontend verification?**
A. `npx tsc --noEmit` (0 errors) and `npm run build` (17/17 pages).

## R. Evaluation (4)

**Q90. What does the evaluation module measure?**
A. Per-stage latency (YOLO, EfficientNet, nutrition, DCI, NIS, prediction,
fusion, rules), AI hit/miss latency, cache performance, PDF generation, and
memory/CPU.

**Q91. What statistics are reported?**
A. Mean, median, and 95th percentile per metric, plus memory (tracemalloc +
RSS) and cache hit-rate.

**Q92. What artefacts are produced?**
A. CSV and JSON reports, matplotlib PNG charts, and dissertation-ready
markdown tables (5.1–5.4).

**Q93. How reproducible are the numbers?**
A. Each run regenerates the reports; a warm-up pass excludes model-loading
time, and single-threaded CPU inference is used throughout.

## S. Deployment (3)

**Q94. How do you deploy locally vs in Docker?**
A. Locally: SQLite + `uvicorn`/`npm run dev`. In Docker: `docker-compose up
--build` runs PostgreSQL, the FastAPI backend, and the Next.js frontend.

**Q95. How is the project deployed to production?**
A. `render.yaml` deploys the backend (Docker) with a PostgreSQL database and
an auto-generated `SECRET_KEY`; the frontend is deployed separately (e.g.
Vercel) with `NEXT_PUBLIC_API_URL` pointing at the backend.

**Q96. What environment variables are required?**
A. `DATABASE_URL`, `SECRET_KEY`, model paths, nutrition CSV path, upload dir,
and optional `GEMINI_API_KEY` / `GEMINI_MODEL` / `GEMINI_TIMEOUT`.

## T. Architecture (4)

**Q97. Draw the end-to-end data flow.**
A. Upload → FastAPI → YOLO detect → crop → EfficientNet classify → nutrition
lookup → DCI/NIS → XGBoost ×4 → risk fusion → rule recommendations →
persisted → (optional) Gemini AI Dietitian + caching → JSON to the frontend.

**Q98. How is the AI layer isolated from the ML core?**
A. Through a structured context interface and the `LLMClient` abstraction;
Gemini only reads ML output and can be swapped or disabled without touching
the pipeline.

**Q99. What design patterns do you use?**
A. Singleton services, dependency injection (constructor + FastAPI
`Depends`), factory (LLM providers), strategy (threshold classifier),
repository (cache, analytics), and adapter (LLM client).

**Q100. What are the main trade-offs you made?**
A. Deterministic+explainable ML core vs. AI flexibility; in-memory chat vs.
persistence; CPU-only vs. GPU; pre-trained models vs. retraining; rule-based
recs vs. learned recs — each chosen for explainability, deployability, and
scope.

---

# Part B — Very Difficult Questions an External Examiner May Ask

1. **"Your obesity model sums class probabilities 2–6. How do you know the
   class ordering?"** → The model is pre-trained on a 7-class obesity
   dataset (0–1 underweight/normal, 2–6 overweight/obese); I verified the
   label order during integration. I can expose `model.classes_` to confirm
   it programmatically.

2. **"How do you prove the DCI/NIS classifier has no overlaps or gaps?"** →
   Each level uses a single inequality against one threshold, evaluated
   strictest-first, plus a catch-all. I proved it with boundary tests at
   every threshold and exhaustive sweeps over the score range.

3. **"If I run the pipeline twice on the same image, will the AI result be
   identical?"** → The ML pipeline is deterministic and identical; the
   Gemini narrative may differ slightly due to temperature, but the
   deterministic health score is fixed and identical contexts reuse the
   cached response.

4. **"Your chat memory is in-memory. What happens in a multi-worker or
   restarted deployment?"** → Sessions are lost on restart and not shared
   across workers. For horizontal scaling I would move to Redis or persist
   bounded sessions. It is a documented limitation.

5. **"How do you handle adversarial prompt injection through meal notes?"** →
   Notes and user text are treated as data, the system prompt fixes the
   assistant's role and output schema, and we parse/validate the response as
   JSON with fixed keys. We never execute model output.

6. **"Why is your health score not clinically validated?"** → It is a
   transparent, deterministic heuristic derived from standard nutritional
   references and the ML risk scores, intended as an education/engagement
   tool, not a clinical instrument. The system always directs users to
   professionals.

7. **"How do you know the diabetes model returning 0.0 is correct?"** → A
   zero for a low-risk profile is plausible, but this flagged a need for a
   sanity check: I would test a deliberately high-risk profile to confirm
   the model responds, and include that as a validation case.

8. **"How do you know YOLO's 18 classes match your 118 EfficientNet
   classes?"** → They are different taxonomies by design: YOLO gives coarse
   localisation classes; EfficientNet does fine-grained dish
   classification. The nutrition alias map bridges the two namespaces.

9. **"What is your baseline? How do you know the system is good?"** → We
   report per-stage latency and verify index/fusion correctness. For clinical
   accuracy we would need external validation against a medical gold
   standard; that is future work.

10. **"Why not fine-tune EfficientNet further or use a Vision-Language
    Model?"** → Pre-trained weights fit our scope and CPU constraints; VLM
    inference is heavier and less deterministic. The architecture supports
    swapping models without redesigning the pipeline.

---

# Part C — Top 20 Most Likely Examiner Questions

1. "What does your project do, in two sentences?"
2. "What is the role of each ML model (YOLO, EfficientNet, XGBoost)?"
3. "Why did you use a two-stage detection + classification cascade?"
4. "What is DCI and how is it computed?"
5. "What is NIS and how is it computed?"
6. "What is the risk-fusion formula and why those weights?"
7. "Why did you replace interval ranges with thresholds?"
8. "How do you prevent double-counting of the same food?"
9. "What role does Gemini play, and what does it NOT do?"
10. "How do you stop the LLM from hallucinating?"
11. "What happens if Gemini is unavailable?"
12. "How is the AI result cached?"
13. "How is the AI Dietitian different from the meal-specific chat?"
14. "What does the Personalized Nutrition Coach compute, and why deterministically?"
15. "How is authentication handled?"
16. "How do you secure refresh tokens?"
17. "How do you test the system without calling external APIs?"
18. "What does the evaluation module produce?"
19. "What are the main limitations of your system?"
20. "What would you improve if you had more time?"

*Prepare confident answers to these twenty first — they are the highest
probability questions.*
