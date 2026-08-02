# Ollama LLM Provider Guide — DietRiskNet

**Scope:** how DietRiskNet's AI subsystem now runs on **multiple LLM providers**,
with **Ollama as the default local provider** (no API key required) and **Gemini
as an optional cloud provider**.

---

## 1. Architecture

The AI subsystem was refactored into a **provider-agnostic** layer. All AI
features — AI Dietitian, meal-specific chat, and AI Nutrition Assistant —
depend only on a single interface; no business logic references a concrete
provider.

```
                          ┌──────────────────────────────────────────┐
                          │            AI features                  │
                          │  MealAIService · ChatAIService ·         │
                          │  NutritionAssistantService               │
                          └────────────────────┬─────────────────────┘
                                               │  .enabled / .generate_json /
                                               │  .chat / .health_check
                          ┌────────────────────▼─────────────────────┐
                          │          BaseLLMProvider (ABC)           │
                          └────────────────────┬─────────────────────┘
                                               │
              ┌────────────────────────────────┼────────────────────────────────┐
              │                                │                                │
   ┌──────────▼──────────┐         ┌───────────▼───────────┐       ┌───────────▼──────────┐
   │  OllamaProvider      │         │  GeminiProvider       │       │  FallbackLLMProvider │
   │  (DEFAULT, local)    │         │  (OPTIONAL, cloud)    │       │  (wraps primary +   │
   │  http://localhost:11434        │  Google Gemini API    │       │   fallback)         │
   └──────────┬──────────┘         └───────────┬───────────┘       └─────────────────────┘
              │                                │
   ┌──────────▼──────────┐         ┌───────────▼───────────┐
   │  LLMProviderFactory │         │  get_llm_client()     │  <- backward-compatible
   │  selects by         │         │  (alias)              │
   │  LLM_PROVIDER       │         └───────────────────────┘
   └─────────────────────┘
```

**Components**

| Component | File | Responsibility |
|---|---|---|
| `BaseLLMProvider` | `backend/services/llm/base.py` | Abstract interface: `enabled`, `generate_json()`, `chat()`, `generate()`, `health_check()`. `LLMClient` kept as a backward-compatible alias. |
| `OllamaProvider` | `backend/services/llm/ollama_provider.py` | **Default** provider. Talks to a local Ollama server via its REST API (`/api/generate`, `/api/version`, `/api/tags`). No API key. |
| `GeminiProvider` | `backend/services/llm/gemini_client.py` | Optional cloud provider (renamed from `GeminiClient`, kept as alias). Requires `GEMINI_API_KEY`. |
| `LLMProviderFactory` | `backend/services/llm/factory.py` | Selects the provider from `LLM_PROVIDER`; builds `FallbackLLMProvider` for `gemini` so requests degrade to Ollama. |
| `FallbackLLMProvider` | `backend/services/llm/factory.py` | Tries the primary provider, then the fallback on `LLMProviderError`. Never returns HTTP 500. |
| `get_llm_client()` | `backend/services/llm/factory.py` | Backward-compatible helper used by services and benchmarks. |

---

## 2. Provider flow

1. A service (`MealAIService`, `ChatAIService`, `NutritionAssistantService`)
   calls `get_llm_client()` (once, cached in the service singleton) and gets a
   `BaseLLMProvider`.
2. Before generating, the service checks `client.enabled`:
   - **Ollama** → always `True` (local; configured by default).
   - **Gemini** → `True` only when `GEMINI_API_KEY` is set.
3. The service calls `client.generate_json(system_prompt, user_prompt)` (or
   `chat(...)`). The provider returns a parsed dict / text.
4. If a provider raises `LLMProviderError` (timeout, connection refused,
   quota, invalid key, malformed JSON), the **caller** catches it and degrades
   gracefully — `ai_dietitian: null`, a friendly chat reply, or the rule-based
   engine. **Never an HTTP 500.**
5. With `LLM_PROVIDER=gemini`, `FallbackLLMProvider` automatically retries a
   failed Gemini call against local Ollama before the caller ever sees the
   error.

---

## 3. Configuration

All settings are read from the environment or the root `.env` file
(`backend/config.py`). The app works with **no API key** when a local Ollama
server + model are available.

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Provider selection: `ollama` (default) or `gemini` (optional). |
| `OLLAMA_URL` | `http://localhost:11434` | Local Ollama server URL. |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model used by Ollama (must be pulled first). |
| `OLLAMA_TIMEOUT` | `120` | Request timeout in seconds for Ollama calls. |
| `GEMINI_API_KEY` | *(empty)* | Gemini key; **optional**. Empty → Gemini disabled. |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name. |
| `GEMINI_TIMEOUT` | `15` | Gemini request timeout in seconds. |

**Examples**

```ini
# Default: local Ollama, no API key
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Optional: Gemini cloud with automatic fallback to Ollama
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
OLLAMA_MODEL=llama3.2:3b
```

---

## 4. Installing Ollama

**Windows (no admin required — portable build):**

```bash
mkdir -p "$HOME/ollama-local" && cd "$HOME/ollama-local"
curl -L -o ollama.zip https://ollama.com/download/ollama-windows-amd64.zip
# extract (Python):
python -c "import zipfile; zipfile.ZipFile('ollama.zip').extractall('.')"
./ollama.exe serve          # start the server (background)
./ollama.exe --version      # verify
```

**Windows (winget installer):** `winget install --id Ollama.Ollama` — the
installer registers a background service so `ollama serve` is automatic.

**Verify the server:**

```bash
curl http://localhost:11434/api/version
# {"version":"0.32.5"}
```

---

## 5. Downloading models

```bash
ollama pull llama3.2:3b     # ~2 GB
ollama list                 # verify installed models
```

The first generation after a pull loads the model into memory (can take
tens of seconds on CPU); subsequent calls are much faster.

---

## 6. Supported models

`OLLAMA_MODEL` accepts any model name available to your Ollama server. Common
lightweight choices that run well on CPU:

| Model | Size | Notes |
|---|---|---|
| `llama3.2:3b` | ~2 GB | **Default**; good balance of speed and quality. |
| `llama3.2:1b` | ~1.3 GB | Fastest; lower quality. |
| `mistral` | ~4.1 GB | Strong instruction following. |
| `phi3` | ~2.2 GB | Compact, capable. |
| `gemma2` | ~5.5 GB (2b variant ~1.6 GB) | Google's open model family. |

To use a different model, pull it and set `OLLAMA_MODEL` in `.env`, e.g.
`OLLAMA_MODEL=phi3`.

---

## 7. Provider selection

`LLMProviderFactory.create_provider()` reads `LLM_PROVIDER`:

| `LLM_PROVIDER` | Result |
|---|---|
| `ollama` (or unset) | `OllamaProvider` — local, no key. |
| `gemini` | `FallbackLLMProvider(GeminiProvider, OllamaProvider)` — Gemini primary, Ollama fallback. |
| anything else | `ValueError` at startup (clear configuration error). |

The factory is provider-agnostic — adding `openai`, `claude`, or `azure_openai`
is a one-branch change in `factory.py` plus a new `BaseLLMProvider` module.

---

## 8. Fallback behaviour

- **`LLM_PROVIDER=gemini` + Gemini fails** (quota, invalid/expired key, timeout,
  network) → `FallbackLLMProvider` logs `LLM primary 'gemini' failed ... trying
  fallback 'ollama'` and serves the request from local Ollama. The caller never
  sees a failure.
- **Ollama not running / model missing** → `OllamaProvider` raises
  `LLMProviderError` → the AI services return the existing graceful fallback
  (`ai_dietitian: null`, a friendly "temporarily unavailable" chat reply, or
  rule-based recommendations). **Never an HTTP 500.**
- **No Gemini key at all** → `GeminiProvider.enabled=False`; with
  `LLM_PROVIDER=gemini`, the factory still falls back to Ollama.

---

## 9. Health endpoint

`GET /api/ai/health` reports the active provider without authentication:

```json
{
  "provider": "ollama",
  "model": "llama3.2:3b",
  "status": "ok",
  "latency_ms": 12.3,
  "version": "0.32.5",
  "detail": "model_installed"
}
```

- `status` ∈ `ok` / `unconfigured` / `error` / `unavailable`.
- The endpoint **never raises** — provider failures are returned in the payload.

---

## 10. Testing performed

**Provider unit / integration**

- `BaseLLMProvider` interface implemented by both providers; `LLMClient` and
  `GeminiClient` aliases keep existing code/tests working.
- `OllamaProvider` JSON and plain-text generation verified against a live
  `llama3.2:3b` server.
- `GeminiProvider` still functions (config, retry/backoff, JSON parsing).
- **Automatic fallback verified:** with `LLM_PROVIDER=gemini` (quota-limited
  key), `generate_json` first failed on Gemini then returned a real response
  from Ollama (`{'reply': 'fallback works'}`).

**End-to-end (Ollama only, no Gemini key)**

| Check | Result |
|---|---|
| Backend starts | ✅ HTTP 200 |
| Frontend starts | ✅ HTTP 200 |
| Ollama running (`llama3.2:3b`) | ✅ |
| `/api/ai/health` → `ollama / ok / model_installed` | ✅ |
| Login | ✅ |
| Upload + meal analysis (Idli) | ✅ |
| AI Dietitian (real response) | ✅ health score, summary, recommendations |
| Meal-specific chat | ✅ real reply |
| AI Nutrition Assistant (conversational) | ✅ real replies incl. personalisation |
| Personalized Nutrition Coach | ✅ analytics from meal history |
| History | ✅ |
| Trends | ✅ |
| PDF report | ✅ valid 2-page PDF |
| No Gemini API key required | ✅ |

**Regression**

- Backend `pytest`: **149 passed, 0 failed**.
- Frontend `npx tsc --noEmit`: 0 errors.
- Frontend `npm run build`: production build succeeds.

**Performance observations**

- First request loads models into memory (Ollama + EfficientNet) — slowest
  call; subsequent calls are faster.
- `llama3.2:3b` on CPU returns a structured dietitian JSON in ~10–30 s; plain
  chat replies similarly. Generation time depends on prompt length and
  hardware. The frontend's default 15 s API timeout can be exceeded on slow
  CPU runs — use a larger model timeout or warm up the models for a smooth
  demo.
- Small local models occasionally return JSON that does not exactly match the
  requested schema; the services coerce/fall back gracefully (e.g. a canned
  "I could not generate an answer" reply) instead of failing.

---

## 11. Files

**Created**
- `backend/services/llm/ollama_provider.py`
- `docs/final/OLLAMA_PROVIDER_GUIDE.md`

**Modified**
- `backend/services/llm/base.py` — `BaseLLMProvider` interface (+ `LLMClient` alias)
- `backend/services/llm/gemini_client.py` — `GeminiProvider` (+ `GeminiClient` alias), `chat()`, `health_check()`
- `backend/services/llm/factory.py` — `LLMProviderFactory`, `FallbackLLMProvider`
- `backend/config.py` — `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`; `LLM_PROVIDER` default `ollama`
- `backend/routes/ai_chat.py` — `GET /api/ai/health`
- `backend/services/meal_ai_service.py`, `chat_ai_service.py`, `nutrition_assistant_service.py` — migrated to `BaseLLMProvider` (type hints/docstrings only)
- `backend/evaluation/benchmark_ai.py` — deterministic fake client unless `LLM_BENCHMARK_REAL=1`
- `requirements.txt` — pinned `httpx`
- `.env.example`, `.env` — Ollama/Gemini configuration
