"""Persistent AI Dietitian result cache.

Stores the structured output of an LLM provider (Gemini today, Claude /
OpenAI / Ollama later) for a meal so that identical contexts never call
the LLM twice.

Provider-agnostic design: the ``provider`` and ``model`` columns record
which model produced the result, and the list fields are stored as
generic JSON.  Adding a new provider requires NO schema change.

The ``context_hash`` is the cache key (see ``ai_cache_service``).
"""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from backend.utils.datetime_utils import utcnow

from backend.database.database import Base


class AIDietitianResult(Base):
    __tablename__ = "ai_dietitian_results"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(
        Integer,
        ForeignKey("meals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Provider identifiers — enables future providers without schema change.
    provider = Column(String, nullable=False, default="gemini")
    model = Column(String, nullable=True)

    # Structured result (the health_score/level/explanation are computed
    # deterministically by the backend; the remaining text fields come
    # from the LLM).  Storing all three health fields lets a cache hit
    # reconstruct the full response without recomputation.
    summary = Column(Text, nullable=True)
    meal_quality = Column(String, nullable=True)
    health_score = Column(Integer, nullable=True)
    health_level = Column(String, nullable=True)
    health_explanation = Column(Text, nullable=True)
    risk_explanation = Column(Text, nullable=True)

    # List-valued fields stored as JSON.
    recommendations_json = Column(JSON, default=list)
    alternatives_json = Column(JSON, default=list)
    warnings_json = Column(JSON, default=list)
    follow_up_questions_json = Column(JSON, default=list)

    # Cache / provenance metadata.
    prompt_version = Column(String, nullable=True)
    context_hash = Column(String, nullable=False, index=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    meal = relationship("Meal")

    __table_args__ = (
        Index("idx_ai_meal_context", "meal_id", "context_hash"),
    )
