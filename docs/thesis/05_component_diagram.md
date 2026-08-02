# 05 — Component Diagram

## Backend components

```mermaid
graph TD
    subgraph Backend["FastAPI Backend"]
        subgraph Routes["HTTP layer"]
            AUTH[Auth routes]
            MEAL[Meal routes]
            PRED[Prediction routes]
            USER[User routes]
            AIC[ai_chat routes]
            NUTRI_R[Nutrition chat routes]
            REP[Report routes]
        end

        subgraph Services["Business logic"]
            AUTH_SVC[auth_service]
            ML[ml_services - YOLO + EfficientNet]
            NUTR[nutrition_service]
            IND[indices_services - DCI + NIS]
            PRED_SVC[prediction_service - XGBoost]
            FUSION[risk_fusion_service]
            RULES[recommendation_service]
            USVC[user_services]
            AISVC[meal_ai_service]
            CHATSV[chat_ai_service]
            NUTRIT[nutrition_assistant_service]
            CONV[conversation_store]
            CACHE[ai_cache_service]
            HEALTH[health_score_service]
            REPORT[report_service]
        end

        subgraph LLM["Provider layer (pluggable)"]
            LLMBASE[LLMClient interface]
            OLLAMA[OllamaProvider (default)]
            GEMINI[GeminiProvider (optional)]
            FACTORY[LLMProviderFactory]
        end

        subgraph Shared["Cross-cutting"]
            AUTHUTIL[auth_utils - JWT]
            LOGGER[logger]
            CLASSIFY[classification - threshold engine]
        end

        AUTH --> AUTH_SVC
        MEAL --> ML
        MEAL --> NUTR
        MEAL --> IND
        MEAL --> PRED_SVC
        MEAL --> FUSION
        MEAL --> RULES
        MEAL --> USVC
        MEAL --> AISVC
        AIC --> CHATSV
        NUTRI_R --> NUTRIT
        REP --> REPORT

        AISVC --> HEALTH
        AISVC --> CACHE
        AISVC --> LLMBASE
        CHATSV --> CONV
        CHATSV --> LLMBASE
        NUTRIT --> CONV
        NUTRIT --> LLMBASE
        LLMBASE --> OLLAMA
        LLMBASE --> GEMINI
        FACTORY -.-> OLLAMA
        FACTORY -.-> GEMINI
        LLMBASE -.-> FACTORY

        IND --> CLASSIFY
    end

    subgraph Frontend["Next.js Frontend"]
        AICARD[AIDietitianCard]
        AIPANEL[AIChatPanel]
        NUTPAGE[Nutrition page]
        API[services/api.ts]
        STORE[lib/store.ts - Zustand]
        PROT[ProtectedRoute]
    end

    API --> MEAL
    API --> AIC
    API --> NUTRI_R
    API --> REP
    API --> AUTH
    AICARD --> API
    AIPANEL --> API
    NUTPAGE --> API
    PROT --> STORE
```

## Key component contracts

| Component | Depends on | Contract |
|-----------|-----------|----------|
| `meal_ai_service` | `health_score_service`, `ai_cache_service`, `LLMClient` | returns `AIDietitianResponse` or `None` |
| `chat_ai_service` | `ai_cache_service`, `LLMClient`, persisted meal | returns `reply: str` or raises `LLMProviderError` |
| `ai_cache_service` | `AIDietitianResult` model | `context_hash` / `save_response` / `get_cached_response` / `invalidate` |
| `report_service` | persisted meal + `AIDietitianResult` | returns PDF bytes |
| `LLMClient` (interface) | — | `enabled`, `generate_json(system, user) -> dict` |

## Provider pluggability

**Ollama is the default local provider** (`OllamaProvider`) and **Gemini is
optional** (`GeminiProvider`). When Gemini is selected and fails, requests
automatically fall back to local Ollama (`FallbackLLMProvider`). New LLM
providers (OpenAI, Claude, Azure OpenAI) implement the `LLMClient`
interface and are registered in `LLMProviderFactory`. No business-logic
change is required.
