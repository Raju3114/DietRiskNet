# 13 — User Manual

## 13.1 Register & Login

1. Open the app (`http://localhost:3000`).
2. Click **Get Started**, fill in email / password / name, and register.
3. Log in with the same credentials. You land on the **Dashboard**.

## 13.2 Set Up Your Profile

On the **Profile** page enter age, gender, height, weight, and activity
level, and tick any existing conditions (e.g. diabetes, hypertension).
These demographics feed the disease-risk models.

## 13.3 Log a Meal

1. Open the **Upload** page.
2. Drop a photo of your meal (PNG/JPG/JPEG/WEBP) or click to browse.
3. Optionally add meal notes, then click **Analyze Meal**.
4. The system runs detection → classification → nutrition → DCI/NIS →
   disease risk → fusion → recommendations → (AI Dietitian).

## 13.4 Read the Results

- **Analysis page**: bounding-box overlays, per-item nutrition, and
  DCI/NIS indices.
- **Predictions page**: four disease-risk probabilities + fused risk.
- **Recommendations page**: rule-based advice with explanations.
- **AI Dietitian card** (when the LLM provider is available — Ollama by
  default, or Gemini if configured): a circular
  **health score**, meal quality, summary, risk explanation,
  recommendations, healthier alternatives, and warnings.
- **Download Report**: click **Download Report** for a professional PDF.

## 13.5 Ask the AI Dietitian

Below the AI Dietitian card, type a question (or click a suggested
prompt):

- *"How can I reduce sodium?"*
- *"Is this meal good for diabetes?"*
- *"What should I eat for dinner?"*
- *"How can I increase protein?"*

The assistant answers only about the analysed meal and remembers the
conversation during the session. It never replaces professional medical
advice.

## 13.6 AI Nutrition Assistant

Open **Nutrition Assistant** from the sidebar — a general nutrition
coach that works anytime, even before you analyse a meal.

The page shows a **personalized dashboard** built from your meal
history: average calories / protein / carbs / fat, average DCI and NIS,
meals this week, risk trend, most-common food, detected patterns
(e.g. high sodium), positive habits, areas to improve, and smart goals
with progress bars. (It appears once you have analysed at least one
meal.)

- Tap a **quick action** (📊 Weekly Summary, 🎯 My Goals, 📈 Progress, 🥗
  Meal Suggestions, 🛒 Grocery List, 💧 Hydration, ❤️ Improve My Diet) to
  ask instantly.
- Type any nutrition / meal-planning / dietary question, or click a
  suggested prompt to fill the input.
- The assistant keeps the conversation in memory during the session and
  may reference your recent meals to personalise advice.
- It stays focused on nutrition — for unrelated topics it politely
  redirects back to dietary guidance, and it never replaces professional
  medical advice.

## 13.7 Dashboard, Trends & History

- **Dashboard**: today's calorie/macro intake vs. RDI, DCI, NIS, fused
  risk, recent meals, and latest recommendations.
- **Trends**: 7 / 14 / 30-day charts of calories, macros, DCI, NIS, and
  the four disease risks.
- **History**: every logged meal with its food items and indices.

## 13.7 Notes & Limitations

- The AI Dietitian is an explanation layer over the ML pipeline — it
  never performs the diagnosis itself.
- If no LLM provider is available (Ollama not running and Gemini not
  configured), the AI card is hidden and rule-based recommendations are
  shown.
- Use the service for dietary guidance, not as a substitute for
  consultation with a qualified healthcare professional.
