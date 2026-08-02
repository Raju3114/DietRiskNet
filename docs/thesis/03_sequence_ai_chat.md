# 03 — Sequence Diagram: AI Chat

The meal-specific AI chat (`POST /api/ai/chat`) loads the PERSISTED meal
analysis (no ML re-computation), maintains an in-memory rolling
conversation (max 10 messages), and answers via the LLM provider.

```mermaid
sequenceDiagram
    participant U as Browser
    participant P as AIChatPanel (frontend)
    participant R as FastAPI /api/ai/chat
    participant S as ChatAIService
    participant DB as Database
    participant G as LLM Provider (Ollama default / Gemini optional)

    U->>P: type question + Send
    P->>R: POST /api/ai/chat {meal_id, message}

    R->>S: chat(user_id, meal_id, message)

    S->>S: get_or_create_session(key=user+meal)
    S->>DB: build_context_from_meal (foods, nutrition, dci, nis, predictions, fusion, rule recs, ai_summary, health_score)
    DB-->>S: structured context (READ ONLY - no recompute)

    S->>G: generate_json(system prompt + context + history + question)
    G-->>S: {"reply": "..."}

    S->>S: append {user, model} to rolling history (max 10)
    S-->>R: reply string

    alt provider error / no key / timeout
        S-->>R: LLMProviderError
        R-->>P: 200 {"reply": "temporarily unavailable..."}
    else meal not owned / missing
        R-->>P: 404 Meal not found
    end

    R-->>P: 200 {"reply": "..."}
    P-->>U: render assistant bubble
```

## Notes

- The session key is `(user_id, meal_id)` — the conversation remembers
  the previous meal within the session.
- History is **in-memory only** (never persisted to the database) and
  truncated to the most recent 10 messages.
- The service reads the meal from the DB; it never re-runs YOLO,
  EfficientNet, nutrition, or disease prediction.
