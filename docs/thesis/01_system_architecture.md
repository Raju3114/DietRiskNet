# 01 — System Architecture

DietRiskNet is a three-tier, modular medical-AI system. The frontend
(Next.js) talks to a FastAPI backend over a REST API; the backend
orchestrates a deterministic ML pipeline (YOLOv8 → EfficientNet →
nutrition → DCI/NIS → XGBoost → risk fusion → rule engine), then an
optional LLM layer — **Ollama by default, Gemini optional** — that powers
the AI Dietitian, meal chat, and AI Nutrition Assistant, plus a PDF report. A
relational database (SQLite locally, PostgreSQL in Docker) persists every
meal analysis.

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js 16)"]
        UI[Pages: Landing / Login / Register / Upload / Dashboard / Analysis / Predictions / Recommendations / Trends / History / Profile / Nutrition / Research / About]
        AIUI[AIDietitianCard]
        CHAT[AIChatPanel]
        NUTRIUI[Nutrition Assistant page]
        SIDE[Sidebar + ProtectedRoute + ClientProviders]
        STORE[Zustand store + React Query]
    end

    subgraph API["FastAPI Backend"]
        ROUTES[Routes: auth / meal / prediction / user / ai_chat / report / nutrition_chat / nutrition_coach]
        ML[ML Pipeline Services]
        IND[Indices: DCI + NIS]
        PRED[XGBoost Disease Prediction x4]
        FUSION[Risk Fusion]
        RULES[Rule Recommendation Engine]
        AISVC[MealAIService + HealthScore]
        CHATSV[ChatAIService]
        NUTRI[NutritionAssistantService]
        CACHE[AICacheService]
        REPORT[ReportService - PDF]
        LLM[LLMClient (Ollama default / Gemini optional)]
    end

    subgraph Models["Computer Vision Models"]
        YOLO[YOLOv8 Detection]
        EFF[EfficientNet-B3 Classification]
    end

    subgraph Data["Data"]
        NUTR[(Indian Food Nutrition CSV - 1014 dishes)]
        DB[(Database: users, meals, nutrition, predictions, fusion, recommendations, ai_dietitian_results)]
    end

    UI --> API
    AIUI --> ROUTES
    CHAT --> ROUTES
    ROUTES --> ML
    ROUTES --> IND
    ROUTES --> PRED
    ROUTES --> FUSION
    ROUTES --> RULES
    ROUTES --> AISVC
    ROUTES --> CHATSV
    ROUTES --> NUTRI
    ROUTES --> REPORT
    ML --> YOLO
    ML --> EFF
    ML --> NUTR
    AISVC --> CACHE
    AISVC --> LLM
    CHATSV --> LLM
    CHATSV --> CACHE
    NUTRI --> LLM
    NUTRI --> DB
    ML --> DB
    IND --> DB
    PRED --> DB
    FUSION --> DB
    RULES --> DB
    AISVC --> DB
    REPORT --> DB
```

## Module responsibilities

| Module | Responsibility |
|--------|----------------|
| **Frontend** | Auth UI, meal upload, dashboard, analysis visualisation (bounding boxes), predictions, recommendations, AI Dietitian card, AI chat panel, AI Nutrition Assistant page, PDF download |
| **NutritionAssistantService** | General nutrition / meal-planning assistant with optional meal-history personalisation |
| **NutritionAnalyticsService** | Deterministic dietary analytics (averages, DCI/NIS, risk trend, patterns, smart goals) from stored meal history |
| **FastAPI routes** | HTTP boundary, validation, auth (JWT), orchestration |
| **YOLOv8** | Food region detection → bounding boxes |
| **EfficientNet-B3** | Crop classification → 118 food classes |
| **Nutrition service** | CSV lookup (exact → alias → normalised → fuzzy) |
| **DCI / NIS** | Dietary Consistency / Nutritional Imbalance indices (threshold-based) |
| **XGBoost ×4** | Diabetes, obesity, hypertension, deficiency risk probabilities |
| **Risk fusion** | Weighted fusion of DCI, NIS, and the four risks |
| **Rule engine** | Threshold-triggered explainable recommendations |
| **MealAIService** | Deterministic health score + LLM summary/alternatives/warnings (Ollama default, Gemini optional) |
| **AICacheService** | Persistent cache of AI results keyed by context hash |
| **ChatAIService** | Meal-specific conversation (rolling 10-message history) |
| **ReportService** | ReportLab PDF generation |
| **Database** | 12 relational tables (see ER diagram) |

## Key properties

- **Deterministic ML core**: YOLO/EfficientNet/XGBoost outputs are
  repeatable; the AI layer only consumes their structured output.
- **Fail-safe AI**: if the LLM provider (Ollama default, Gemini optional)
  is unavailable/disabled, the API returns
  `ai_dietitian = null` and the rule-based recommendations stand.
- **Backward compatible**: `ai_dietitian` is an optional field; every
  original response field is unchanged.
- **Caching**: identical meal contexts never re-invoke the LLM.
