# 06 — Database ER Diagram

The system uses SQLAlchemy ORM over SQLite (dev) / PostgreSQL (Docker).
There are **12 tables**. All child rows cascade on delete.

```mermaid
erDiagram
    users ||--o{ meals : "owns"
    users ||--o{ user_settings : "has (1:1)"
    users ||--o{ refresh_tokens : "issues"
    users ||--o{ diet_history : "tracks"
    users ||--o{ audit_logs : "records"

    meals ||--o{ meal_items : "contains"
    meals ||--|| meal_nutritions : "aggregates (1:1)"
    meals ||--|| disease_predictions : "predicts (1:1)"
    meals ||--|| risk_fusion_results : "fuses (1:1)"
    meals ||--o{ recommendations : "recommends"
    meals ||--|| diet_history : "maps to (1:1)"
    meals ||--o{ ai_dietitian_results : "caches (0..n)"

    users {
        int id PK
        string email UK
        string password_hash
        string full_name
        datetime created_at
        datetime updated_at
    }
    refresh_tokens {
        int id PK
        int user_id FK
        string token UK
        datetime expires_at
        boolean is_revoked
    }
    user_settings {
        int id PK
        int user_id FK UK
        int age
        string gender
        float height
        float weight
        string activity_level
        json existing_conditions
        json rdi_custom
    }
    meals {
        int id PK
        int user_id FK
        string image_path
        float dci
        string dci_level
        float nis
        string nis_level
        float risk_fusion_score
        string risk_fusion_level
        string notes
        datetime created_at
    }
    meal_items {
        int id PK
        int meal_id FK
        string name
        float confidence
        float x1 y1 x2 y2
        float weight_g
        float calories protein carbs fats sugar fiber sodium calcium iron vitamin_c folate
    }
    meal_nutritions {
        int id PK
        int meal_id FK UK
        float calories protein carbs fats sugar fiber sodium calcium iron vitamin_c folate
    }
    disease_predictions {
        int id PK
        int meal_id FK UK
        float diabetes_risk
        float obesity_risk
        float hypertension_risk
        float deficiency_risk
    }
    risk_fusion_results {
        int id PK
        int meal_id FK UK
        float fused_score
        string risk_level
    }
    recommendations {
        int id PK
        int meal_id FK
        string content
        string explanation
        string category
    }
    diet_history {
        int id PK
        int user_id FK
        int meal_id FK UK
        datetime logged_date
    }
    audit_logs {
        int id PK
        int user_id FK
        string action
        string ip_address
        string user_agent
        datetime timestamp
    }
    ai_dietitian_results {
        int id PK
        int meal_id FK
        string provider
        string model
        string summary
        string meal_quality
        int health_score
        string health_level
        string health_explanation
        string risk_explanation
        json recommendations_json
        json alternatives_json
        json warnings_json
        json follow_up_questions_json
        string prompt_version
        string context_hash
        datetime created_at
        datetime updated_at
    }
```

## Indexes

- `idx_meal_user_created` — `(meals.user_id, meals.created_at)`
- `idx_diet_history_user_logged` — `(diet_history.user_id, diet_history.logged_date)`
- `idx_ai_meal_context` — `(ai_dietitian_results.meal_id, ai_dietitian_results.context_hash)`

## Notes

- `ai_dietitian_results` is provider-agnostic: `provider` (`gemini`,
  `openai`, `claude`, `ollama`) + `model` columns let future LLMs reuse
  the same schema. The `context_hash` is the cache key.
- `health_score`, `health_level`, `health_explanation` are stored so a
  cache hit reconstructs the full AI response without recomputation.
- Table creation uses `Base.metadata.create_all()` (no Alembic); adding
  the `AIDietitianResult` model registers its table automatically.
