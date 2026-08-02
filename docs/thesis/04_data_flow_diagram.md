# 04 — Data Flow Diagram (DFD)

## Level 0 — Context diagram

```mermaid
graph LR
    U[User] -->|meal image + notes| S[DietRiskNet System]
    S -->|analysis JSON + AI advice + PDF| U
    G[LLM Provider (Ollama default / Gemini optional)] -.->|LLM calls (JSON)| S
    S -.->|structured context| G
```

## Level 1 — Main processes

```mermaid
graph TD
    U[User]

    P1[P1 - Authenticate / Register]
    P2[P2 - Meal Analysis Pipeline]
    P3[P3 - AI Dietitian + Cache]
    P4[P4 - AI Chat]
    P5[P5 - PDF Report]

    D1[(Users / Settings)]
    D2[(Meals / Items / Nutrition)]
    D3[(Predictions / Fusion / Recommendations)]
    D4[(AIDietitianResults cache)]
    D5[(Uploaded images)]

    G[LLM Provider (Ollama default / Gemini optional)]

    U -->|credentials / tokens| P1
    P1 -->|user profile| D1

    U -->|image + notes| P2
    P2 -->|saved image| D5
    P2 -->|meal + items + nutrition| D2
    P2 -->|dci/nis/predictions/fusion/recs| D3
    P2 -->|analysis JSON| U

    P2 -->|structured context| P3
    P3 -->|context hash| D4
    P3 -->|cache hit/miss| G
    G -->|AI JSON| P3
    P3 -->|ai_dietitian (nullable)| U
    P3 -->|cached result| D4

    U -->|meal_id + question| P4
    P4 -->|load persisted analysis| D2
    P4 -->|history (in-memory)| P4
    P4 -->|prompt| G
    G -->|reply| P4
    P4 -->|reply| U

    U -->|meal_id| P5
    P5 -->|load meal + AI| D2
    P5 -->|load AI result| D4
    P5 -->|PDF bytes| U
```

## Data descriptions

| Data store | Contents |
|------------|----------|
| `D1` Users / Settings | email, password hash, demographics, existing conditions |
| `D2` Meals / Items / Nutrition | meal record, per-item bounding boxes + nutrients, aggregated nutrition |
| `D3` Predictions / Fusion / Recommendations | 4 disease risks, fusion score, rule recommendations |
| `D4` AIDietitianResults cache | AI summary/quality/score + list fields, keyed by context hash |
| `D5` Uploaded images | meal photos under `backend/uploads/` |

## Security notes

- User-supplied image → saved under a UUID filename (no path traversal).
- Only structured, display-safe fields are sent to the LLM provider
  (never images, bounding boxes, tensors, email, or names).
- LLM provider failures are isolated: `ai_dietitian` is null; chat returns
  a friendly message; the PDF still generates from persisted data.
