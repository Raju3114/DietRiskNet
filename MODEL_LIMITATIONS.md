# DietRiskNet — Model & Estimate Limitations

> **Read this before interpreting any risk value in the application.**
>
> DietRiskNet produces **disease-risk *estimates*** for educational and
> personal-awareness purposes. It does **not** diagnose, treat, or provide
> medical advice for any condition. Every number shown in the app is an
> AI-assisted indicator built from partial inputs, generic reference data,
> and models that were not validated on the user's population. This document
> states, in plain terms, what each model can and cannot tell you.

---

## 1. Scope of use

| Intended use | Out of scope |
|---|---|
| Personal, educational awareness of dietary patterns | Diagnosis of diabetes, obesity, hypertension, or nutritional deficiency |
| Longitudinal self-tracking of meal consistency | Treatment, medication, or medical advice |
| Supporting a conversation with a qualified clinician | Replacing a clinician or laboratory measurement |

The risk percentages are **relative indicators**, not the probability that a
specific individual will develop a disease.

---

## 2. Vision pipeline (YOLOv8 + EfficientNet)

The food recognition stack runs two models in sequence:

1. **YOLOv8 detector** — localises food regions in a meal photo (18 object
   classes). Duplicate detections of the same class are removed when their
   bounding boxes overlap by more than 60% IoU.
2. **EfficientNet-B3** (fallback B0) **classifier** — labels each crop into one
   of 118 food classes. Only classifications with confidence ≥ 0.45
   (`CLASSIFIER_CONFIDENCE_THRESHOLD`) are accepted; everything else is
   discarded, so an unrecognised image never becomes a fabricated meal.

### Limitations

- **Fixed class vocabulary.** The detector knows 18 categories and the
  classifier 118 food classes. Anything outside those — regional dishes,
  packaged products, mixed/composite meals, non-Indian cuisines — will be
  mislabelled or rejected.
- **Portion size is estimated, not measured.** Serving weights come from a
  static lookup table (`DEFAULT_SERVING_WEIGHTS`); any food without a table
  entry defaults to **100 g**. The app does *not* estimate portion size from
  the image, so calorie and nutrient totals carry portion-size uncertainty.
- **Single, top-down photo.** Recognition is optimised for a clear,
  top-down, well-lit meal photo. Overlapping food, sauces, mixed bowls, dark
  or blurry images, and heavy garnish degrade accuracy.
- **Confidence ≠ correctness.** A high classification confidence only means
  the model is self-assured; it can be confidently wrong on out-of-distribution
  images. The 0.45 threshold is conservative against non-food, but does not
  guarantee the label is the true food.

---

## 3. Nutrition database

Nutrients are mapped from a static Indian-food nutrition table
(`nutrition/indian_food_nutrition_processed.csv`), with values stored **per
100 g** and scaled linearly by the (estimated) serving weight.

### Limitations

- **Static, coarse database.** Values are representative per-100 g figures,
  not laboratory measurements of the photographed meal. The same curry will
  vary with recipe, brand, and cooking method.
- **No record for every food.** When a recognised food has no matching
  nutrition record, the app flags `nutrition_available = false` and treats
  that item's nutrients as *unknown* (not zero-health). If *every* item lacks
  a record, DCI / NIS / risk are suppressed entirely rather than fabricated.
- **Linear scaling assumption.** Nutrients scale linearly with weight. In
  reality, oils, gravies, and toppings are unevenly distributed, so the
  linear model is an approximation.

---

## 4. XGBoost disease-risk models

Four independent XGBoost classifiers produce per-disease risk estimates:

| Model | Trained-on feature set |
|---|---|
| Diabetes Mellitus | Gender, age, hypertension/heart-disease history, smoking, BMI, HbA1c, blood glucose |
| Obesity Index | Gender, age, height, weight, family history, eating/activity habits |
| Hypertension | Age, salt intake, stress, BP history, sleep, BMI, medication, family history |
| Nutritional Deficiency | Age, gender, BMI, RDA %, hemoglobin, physiological symptoms |

### Limitations — hard-coded default inputs

The app collects only age, gender, height, weight, activity level, and a small
set of existing conditions. **The vast majority of model features are supplied
as fixed defaults**, because they are not collected anywhere in the product:

| Model | Defaulted feature | Fixed value |
|---|---|---|
| Diabetes | Smoking history | `never` |
| Diabetes | HbA1c level | `5.5` (or `7.0` if diabetes is a listed condition) |
| Diabetes | Blood glucose | `100` (or `160` if diabetes is a listed condition) |
| Obesity | Family history of obesity | `yes` |
| Obesity | NCP (meals/day), FAF (activity), TUE (screen time), CH2O (water) | `3.0`, `1.0`, `1.0`, `2.0` |
| Obesity | CAEC, CALC, MTRANS | `Sometimes`, `Sometimes`, `Public_Transportation` |
| Hypertension | Stress score, sleep duration | `3.0`, `7.0` |
| Hypertension | Medication, family history | `0` |
| Deficiency | Smoking, alcohol, exercise, diet, sun exposure, income, region | `Never`, `Low`, `Moderate`, `Mixed`, `Moderate`, `Medium`, `Tropical` |
| Deficiency | All serum/RDA values not derivable from the meal | fixed percent-RDA placeholders |

Consequences:

- The four risk values are **dominated by a small number of real inputs**
  (demographics + current meal nutrients) wrapped in many fixed placeholders.
  Two different users with identical demographics and the same meal will get
  very similar scores regardless of their real smoking, sleep, or stress.
- The **transparency note on the predictions page is accurate**: outputs are
  "based on available profile, dietary, and **model-default** inputs."
- These are the largest honesty risk in the product. Scores must be framed as
  estimates, never as measurements.

### Other limitations

- **Public dataset training.** Models were trained on public clinical /
  survey datasets (e.g. diabetes/obesity/BP risk-factor datasets), not on
  the target population or on diet-logged users. Distribution shift is
  expected and unquantified.
- **BMI shortcut.** Several models consume BMI, which is computed from
  self-reported height/weight (defaults `170 cm` / `70 kg` when unset).
- **Existing-condition encoding is coarse.** A listed condition flips one or
  two indicator features; it is not a substitute for a clinical workup.
- **No per-user calibration.** Outputs are raw model probabilities; no
  calibration, personalisation, or uncertainty interval is applied.

---

## 5. DCI — Dietary Consistency Index

DCI measures **day-to-day consistency of total calorie intake** over the last
7 days (coefficient of variation of daily calories):

```
CV   = std(daily_calories) / mean(daily_calories)
DCI  = clamp(1 − CV, 0, 1)
```

### Limitations

- **Needs history.** DCI is `null` ("Insufficient Data") unless the user has
  at least **2 distinct valid days** of meals within the last 7 days. It is
  never computed from a single meal and is never fabricated as a perfect
  score. New users will see "No meals logged yet" until enough history exists.
- **Calories only.** DCI ignores macro composition, meal timing regularity,
  and nutrient quality. Two diets with identical daily calories — one balanced,
  one junk-food — can score the same.
- **7-day window.** Consistency outside the rolling 7-day window is invisible.
- **User-dependent window availability.** The window is the user's own meal
  history; irregular loggers get less data, so their DCI is more sensitive to
  the few meals they did log.

---

## 6. NIS — Nutritional Imbalance Score

NIS measures a single meal's relative deviation from a **calorie-proportional
share** of the daily RDI:

```
meal_fraction = min(1, meal_calories / daily_calorie_target)
NIS           = clamp(mean(|actual[k] − meal_rdi[k]| / meal_rdi[k]), 0, 1)
```

### Limitations

- **Generic RDI.** The RDI table is a fixed, generic adult target
  (2000 kcal, 60 g protein, etc.). It is not personalised for age, gender,
  activity, or clinical goals, and it only covers 6 nutrients (calories,
  protein, carbs, fat, sodium, fiber) — micronutrients such as vitamins and
  minerals are not included in NIS.
- **Meal-level, not daily.** It scores a single meal against its calorie
  share. A snack-heavy day can produce a balanced-looking NIS while a single
  large meal can look imbalanced. NIS says nothing about the whole day.
- **Unknown-calorie meals.** When a meal has no usable calories, a default
  fraction of 1/3 (three-meals-per-day convention) is assumed. This is a
  placeholder, not a measurement.
- **Direction-blind.** Deviations are absolute, so both *over*- and
  *under*-consumption inflate the score.

---

## 7. Risk fusion

The unified risk score is a weighted average of the *available* components:

```
Fused = (0.25·(1−DCI) + 0.25·NIS + 0.20·Diabetes + 0.15·Obesity
         + 0.10·Hypertension + 0.05·Deficiency) / (sum of available weights)
```

### Limitations

- **Fixed, manually-chosen weights.** The weights in
  `DietRiskNet_RiskFusion_Config.json` are designer decisions, not learned or
  validated weights. They encode a judgement (dietary consistency and
  imbalance matter as much as any single disease model).
- **Different time scales mixed.** DCI is longitudinal (7 days), NIS is
  meal-level, and the XGBoost outputs are demographic/meal-driven. Averaging
  them implies a comparability that is only an approximation.
- **Missing-component renormalisation.** When DCI (or any component) is
  unavailable, the remaining weights are renormalised proportionally. This
  preserves the *relative* configured weights without fabricating the missing
  value, but it means the fused score means something slightly different
  depending on which components were available.
- **Averages hide drivers.** A "Moderate" fused score can arise from
  contradictory inputs (high DCI consistency but high hypertension risk, or
  vice-versa). Always read the per-component cards, not just the fused number.

---

## 8. AI Dietitian / LLM narrative

The "AI Dietitian" summary is generated by an LLM (Ollama locally, or
Gemini when configured) from the same meal + index + prediction data.

### Limitations

- **Not clinically validated.** The narrative is instruction-constrained
  ("never provide medical diagnoses; frame guidance as dietary advice") but
  is otherwise **unverified** output. It can state plausible-sounding but
  wrong guidance.
- **Nondeterministic.** Different runs can yield different wording for the
  same meal.
- **Fails open.** If the LLM is unavailable, errors, or times out, the app
  silently falls back to the rule-based output and returns `ai_dietitian =
  null`. There is no user-facing indication of which path produced the text.
- **Local-model quality varies.** Ollama's default `llama3.2:3b` is a small
  model; long or ambiguous prompts can degrade coherence.

---

## 9. Data, privacy, and operational bounds

- **Self-reported data.** All demographic inputs are self-reported and
  unverified (height, weight, existing conditions).
- **No retraining pipeline.** Weights are fixed at release; there is no
  fine-tuning loop and no feedback mechanism to improve them over time.
- **CPU-only inference.** Inference runs single-threaded on CPU
  (`torch.set_num_threads(1)`), prioritising low memory for deployment over
  throughput or GPU acceleration.
- **Uploaded images retained.** Meal photos are stored and linked to meal
  records; they are not used for model training.
- **Chat memory is in-memory.** Conversations are not persisted across
  restarts.

---

## 10. How the application already compensates

These behaviours in the code are deliberate honesty guards (not bugs):

1. **DCI / NIS / risk are `null` when data is insufficient** — never
   fabricated as "perfect health". The UI shows "No Data" / "Insufficient
   Data" / "N/A" and explains "No meals logged yet".
2. **Predictions and fusion are `null` when no item had usable nutrition.**
3. **`nutrition_available = false`** flags foods the classifier recognised
   but that have no nutrition record, so their zero nutrients are not
   treated as measured values.
4. **Risk fusion renormalises missing components** rather than substituting
   a default DCI/NIS value.
5. **The predictions page carries an explicit transparency note**: risk
   estimates are "AI-assisted indicators based on available profile, dietary,
   and model-default inputs" and "are not medical diagnoses".
6. **XGBoost inference reorders features to the trained column order** and
   fails safely (with a logged internal error) if a required feature is
   missing, instead of silently misaligning columns.

---

*This document is part of the DietRiskNet transparency workstream. It should
be kept in sync whenever model inputs, thresholds, or fusion weights change.*
