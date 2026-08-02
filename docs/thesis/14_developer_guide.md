# 14 — Developer Guide

## 14.1 Repository layout

```
backend/
├── main.py                     # FastAPI app, CORS, router registration
├── config.py                   # pydantic Settings (env-driven)
├── database/                   # SQLAlchemy engine + 12 ORM models
├── models/                     # domain models (AIDietitianResult)
├── routes/                     # auth, meal, prediction, user, ai_chat, report, nutrition_chat, nutrition_coach
├── schemas/                    # Pydantic request/response models
├── services/                   # business logic (ML, indices, AI, cache, report)
│   ├── conversation_store.py   # shared rolling in-memory conversation store
│   ├── nutrition_analytics_service.py  # deterministic coach analytics
│   └── llm/                    # provider abstraction: base / ollama / gemini / factory
├── prompts/                    # AI Dietitian + chat + nutrition-assistant templates
├── exceptions/                 # typed LLM errors
├── evaluation/                 # benchmarking module
├── tests/                      # pytest suite
└── trained_models/             # weights + config JSONs
frontend/
├── app/                        # Next.js App Router pages
├── components/                 # Sidebar, ProtectedRoute, AIDietitianCard, AIChatPanel
├── services/api.ts             # API client (auth, token refresh, download)
├── lib/store.ts                # Zustand stores
└── types/index.ts              # TypeScript interfaces
docs/thesis/                    # this thesis documentation
```

## 14.2 Conventions

- **Services** are classes with a module-level singleton
  (`service = XService()`), matching the project pattern.
- **Routes** are thin: they validate via Pydantic, call a service, and
  map errors to HTTP codes.
- **Indices** use the threshold classifier (`classification.py`) —
  configs are data-only (`levels` + `default`), direction lives in code.
- **LLM access** goes through the `BaseLLMProvider` interface via
  `get_llm_client()`; never import a concrete provider
  (`ollama_provider` / `gemini_client`) directly in business logic.
- **Chat memory** uses the shared `ConversationStore` (rolling window,
  in-memory, thread-safe). Both `chat_ai_service` and
  `nutrition_assistant_service` reuse it — do not reimplement history
  logic.
- All dynamic text sent to the LLM / PDF is escaped or display-safe.

## 14.3 Adding a new LLM provider

1. Implement `BaseLLMProvider` in
   `backend/services/llm/<provider>_provider.py`: `enabled` property +
   `generate_json(system_prompt, user_prompt) -> dict` (+ `chat` /
   `health_check`). Raise `LLMProviderError` subclasses on failure.
2. Register it in `backend/services/llm/factory.py`
   (`LLMProviderFactory`).
3. Set `LLM_PROVIDER=<provider>` in the environment.

No business logic in `meal_ai_service` / `chat_ai_service` changes.

## 14.4 Adding a new prompt

Edit `backend/prompts/dietitian_prompt.py`. Bump
`AICacheService.PROMPT_VERSION` so stale cached responses are not served
against the new prompt.

## 14.5 Adding a new disease risk model

1. Add a model path to `backend/config.py`.
2. Add a `predict_<name>` method in `prediction_service.py`.
3. Register it in `predict_all`.
4. Add the probability to `DiseasePrediction` (model + schema) if it
   must be persisted.

## 14.6 Running tests

```bash
python -m pytest backend/tests/ -v          # full backend suite
cd frontend && npx tsc --noEmit             # frontend type check
cd frontend && npm run build                # production build
```

## 14.7 Running benchmarks

```bash
python -m backend.evaluation.system_metrics --iterations 5
# Reports → backend/evaluation/reports/ (CSV, JSON, PNG, markdown tables)
```

## 14.8 Common pitfalls

- **SQLite + FastAPI TestClient**: use `StaticPool` +
  `check_same_thread=False` for in-memory test databases.
- **Stale `.next` cache**: `rm -rf frontend/.next` before judging
  frontend behaviour.
- **ReportLab 5.0**: `ParagraphStyle(name, parent=..., ...)` — do not
  pass `parent` twice.
- **Never** log API keys, prompts, or user PII (see `utils/logger.py`).
