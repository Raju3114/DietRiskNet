# DietRiskNet — PPT Update Guide

Compares the current presentation content
(`docs/final/03_POWERPOINT_CONTENT.md`) against the **validated final
implementation** and lists exactly what to add or change so the deck matches
the code.

**Biggest change:** the AI layer is now **Ollama-default with Gemini optional**
(no API key required, works offline). Any slide that implies Gemini is the
active provider must be updated, and the multi-provider LLM layer is worth
highlighting as a selling point.

---

## 1. Slides that MUST change (AI provider)

| Slide | Current text (line in `03_POWERPOINT_CONTENT.md`) | Change to |
|---|---|---|
| 5 · Architecture | `AI layer: provider-agnostic LLMClient (Gemini active) with SHA-256 context-hash caching` (line 136) | `AI layer: provider-agnostic LLMClient — Ollama default, Gemini optional; SHA-256 context-hash caching; GET /api/ai/health` |
| 9 · Rules + AI Dietitian | `AI Dietitian (Gemini): summary, …` (line 246) | `AI Dietitian (Ollama by default; Gemini optional): summary, …` |
| 9 · Speaker notes | `…my code, not Gemini. If Gemini fails…` (line 254) | `…my code, not the LLM. If the LLM (Ollama or Gemini) fails…` |
| 10 · AI Modules | `Provider-agnostic LLMClient (Gemini today; OpenAI / Claude / Ollama / Azure swappable…)` (line 273) | `Provider-agnostic BaseLLMProvider — Ollama is the default local provider; Gemini optional; OpenAI/Claude/Azure addable` |
| 10 · Speaker notes | `…not tied to Gemini.` (line 282) | `…not tied to any single provider.` |
| 11 · Coach | `Gemini writes only the narrative…` (line 303) | `Ollama (or Gemini) writes only the narrative…` |
| 11 · Speaker notes | `…Gemini only turns these verified numbers…` (line 307) | `…the LLM only turns these verified numbers…` |

## 2. Numbers that MUST change

| Location | Current | New (validated) |
|---|---|---|
| Slide 13 · Evaluation (line 346) | `149 pytest tests … across 10 files` | `169 pytest tests … across 11 files` (adds 20 mocked Ollama provider tests) |
| Slide 15 · Conclusion (line 403) | `149 tests` | `169 tests` |
| Key-numbers table (line 461) | `Backend tests | 149 collected` | `Backend tests | 169 collected` |

## 3. Suggested additions (optional but recommended)

- **Architecture slide (5):** add a small "LLM Provider Layer" box: `Ollama
  (default) / Gemini (optional)` → `FallbackLLMProvider`; show `/api/ai/health`.
- **New content on slide 9 or 10:** the **no-API-key / fully-offline** claim —
  "AI features run locally with Ollama and no Gemini key." This is a strong
  demonstration point.
- **Slide 6 or 7 (pipeline):** keep the measured note that the AI runs only
  after the meal is persisted and never fails the pipeline.
- **Slide 13 (Evaluation):** mention the deterministic AI cache (miss→hit) and
  that health score is backend-computed (already implied in slide 9).
- **Slide 5 or a dedicated slide:** mention `GET /api/ai/health` reports
  provider/model/status/version — a nice live-demo hook.

## 4. Verify against the validated facts (no invention)

- Detected food in the demo: **Idli @ 0.843** (measured) — use as the sample
  result, do not quote invented mAP/accuracy.
- Ollama version **0.32.5**, model **llama3.2:3b** (measured).
- AI Dietitian latency ~6.7 s and warm chat ~1.8–3.6 s (measured, CPU).
- Backend tests **169 passed / 0 failed**; frontend `tsc` 0 errors; build 17/17.
- Cache: identical context → hit, no re-call.
- Offline: ML pipeline works with Ollama down; AI degrades gracefully; no 500.

## 5. Do NOT include

- No real API keys (use `YOUR_GEMINI_API_KEY_HERE` placeholder).
- No invented accuracy/performance numbers beyond the measured ones above.
- Do not describe Gemini as the primary/only provider.

---

## Summary of edits (quick checklist)

1. ✅ Slide 5 architecture — add provider layer + health endpoint.
2. ✅ Slides 9/10/11 — replace "Gemini" with "Ollama default / Gemini optional".
3. ✅ Slide 13 + key numbers — 149 → **169** tests.
4. ✅ Add "no API key, fully offline" as a highlight.
5. ✅ Keep all numbers measured; no invented metrics.
