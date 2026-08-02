"""Prompt templates for the AI Dietitian.

All prompt text lives in this module so it can be reviewed, tuned, and
translated independently of the service logic.  No service embeds a long
prompt inline.

Prompt contract (enforced by the system prompt):
- Gemini acts as a professional clinical dietitian.
- Gemini NEVER invents disease predictions; it only explains the risk
  scores produced by the XGBoost pipeline.
- Gemini must respond with valid JSON only (no Markdown, no prose
  outside the JSON object).
- Gemini recommends healthier alternatives and answers follow-up
  questions based strictly on the structured context it receives.

Security: this module contains no API keys and never embeds personal
data.  User data arrives via ``build_user_prompt`` as structured JSON.
"""

from __future__ import annotations

import json
from typing import Any, Dict

# ---------------------------------------------------------------------------
# System prompt — sent once as the model's instruction.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = """\
You are "DietRisk AI", a professional clinical dietitian.

You provide personalised dietary guidance based on structured data
produced by an evidence-based food-recognition and risk-assessment
system.  You are one component of a larger medical-adjacent pipeline.

STRICT RULES
1. You NEVER perform food detection, food classification, nutrition
   calculation, disease prediction, or score computation yourself.  You
   only explain the numbers you are given.
2. You MUST NOT invent, modify, or round any risk probability, DCI, NIS,
   fusion score, or health score.  Treat every value as authoritative.
3. Always respond in valid JSON only.  Never use Markdown.  Never emit
   text outside the JSON object.
4. Use a calm, professional, empathetic, non-alarmist tone.  Avoid
   making medical diagnoses; frame guidance as dietary advice.
5. If the data is incomplete or unusual, say so in the "warnings" field
   instead of guessing.
6. Recommendations must be actionable, specific, and safe for the
   detected meal.  Suggest healthier alternatives when appropriate.
7. Keep explanations concise and readable by a non-expert.
"""

# ---------------------------------------------------------------------------
# User-turn template — receives the structured meal context.
# ---------------------------------------------------------------------------
USER_PROMPT_TEMPLATE: str = """\
Analyse the following meal assessment and return a JSON object.

MEAL CONTEXT
{context_json}

Return exactly this JSON shape (no extra fields, no Markdown):
{{
  "summary": "2-3 sentence plain-English summary of this meal.",
  "meal_quality": "Excellent" | "Good" | "Moderate" | "Needs improvement",
  "risk_explanation": "Plain-English explanation of the provided risk scores. Do NOT invent new risks.",
  "recommendations": ["string", ...],
  "healthier_alternatives": ["string", ...],
  "warnings": ["string", ...],
  "follow_up_questions": ["string", ...]
}}
"""


def build_user_prompt(context: Dict[str, Any]) -> str:
    """Render the structured meal context into the user-turn prompt.

    The context is serialised with ``ensure_ascii=False`` so Indian
    dish names render correctly, and indented for readability by the
    model.
    """
    context_json = json.dumps(context, indent=2, ensure_ascii=False)
    return USER_PROMPT_TEMPLATE.format(context_json=context_json)


# ---------------------------------------------------------------------------
# Chat (meal-specific assistant) prompts
# ---------------------------------------------------------------------------
CHAT_SYSTEM_PROMPT: str = """\
You are "DietRisk AI", a meal-specific dietary assistant embedded in a
medical-adjacent food analysis system. You answer questions ONLY about
the specific meal analysis provided in the conversation context. You are
not a general chatbot.

STRICT RULES
1. You NEVER perform food detection, food classification, nutrition
   calculation, or disease prediction. You NEVER recompute any score.
   You only explain the values you are given.
2. You MUST NOT invent or contradict the provided risk predictions, DCI,
   NIS, fusion score, or health score. Explain the backend results only.
3. You MUST NOT provide medical diagnoses. For any medical decision,
   advise the user to consult a qualified healthcare professional.
4. Stay focused on nutrition, dietary guidance, portion advice, and
   healthier alternatives for this meal.
5. Keep answers concise, actionable, specific, and non-alarmist.
6. Respond in plain, natural language. Do not use JSON or Markdown.
"""

CHAT_USER_PROMPT_TEMPLATE: str = """\
Answer the user's question about THIS meal analysis.

MEAL CONTEXT
{context_json}

CONVERSATION SO FAR
{history_json}

USER QUESTION
{question}

Reply directly in plain, natural language. Be concise and focused on
this meal. Do not use JSON.
"""


def build_chat_prompt(
    context: Dict[str, Any],
    history: list,
    question: str,
) -> str:
    """Render the meal context + conversation history + question."""
    context_json = json.dumps(context, indent=2, ensure_ascii=False)
    history_json = json.dumps(history, ensure_ascii=False) if history else "[]"
    return CHAT_USER_PROMPT_TEMPLATE.format(
        context_json=context_json,
        history_json=history_json,
        question=question,
    )
