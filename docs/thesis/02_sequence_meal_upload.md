# 02 — Sequence Diagram: Meal Analysis

The following UML sequence diagram shows the complete end-to-end meal
analysis flow for `POST /api/analyze-meal`. The deterministic ML core
runs first and persists results; the AI Dietitian runs only after the
meal is saved, and its failure never breaks the pipeline.

```mermaid
sequenceDiagram
    participant U as Browser
    participant F as Frontend (upload page)
    participant R as FastAPI /api/analyze-meal
    participant D as YOLOv8
    participant C as EfficientNet-B3
    participant N as Nutrition service
    participant I as DCI / NIS
    participant P as XGBoost x4
    participant X as Risk Fusion
    participant L as Rule Engine
    participant A as MealAIService
    participant K as AICacheService
    participant G as LLM Provider (Ollama default / Gemini optional)
    participant DB as Database

    U->>F: select meal image + notes
    F->>R: POST /api/analyze-meal (multipart)
    R->>DB: save upload (uuid filename)

    R->>D: detect(image)
    D-->>R: bounding boxes
    R->>C: classify(crop)
    C-->>R: food class + confidence
    R->>N: lookup(class)
    N-->>R: nutrients (scaled by serving weight)
    R->>I: calculate DCI + NIS
    I-->>R: dci, dci_level, nis, nis_level
    R->>P: predict_all(profile + nutrition)
    P-->>R: 4 risk probabilities
    R->>X: fuse(dci, nis, risks)
    X-->>R: fused_score, risk_level
    R->>L: recommend(...)
    L-->>R: rule recommendations
    R->>DB: save meal, items, nutrition, predictions, fusion, recommendations

    alt LLM provider available (Ollama, or Gemini when configured)
        R->>A: analyze_meal_cached(...)
        A->>K: context_hash(context)
        A->>K: get_cached_response(hash)
        alt cache hit
            K-->>A: cached AIDietitianResponse
        else cache miss
            A->>G: generate_json(system + context prompt)
            G-->>A: structured JSON (summary, recommendations, ...)
            A->>K: save_response(...)
        end
        A-->>R: ai_dietitian dict (or None on error)
    else no API key / error
        R-->>R: ai_dietitian = None (fallback to rule output)
    end

    R-->>F: 200 MealAnalysisResponse (incl. ai_dietitian)
    F-->>U: render bounding boxes, nutrition, DCI/NIS, risks, AI card
```

## Notes

- Every ML stage is deterministic and independent of the AI layer.
- The AI Dietitian (Ollama default, Gemini optional) runs **only after**
  the meal + nutrition + predictions are persisted (requirement: the
  pipeline never fails because of the LLM provider).
- On any LLM provider error the response contains `"ai_dietitian": null`
  and the rule-based recommendations remain intact.
