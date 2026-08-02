# DietRiskNet — Landing Page 3D Redesign

**Scope:** Frontend **visual** redesign of the public landing page (`/`) only.
Backend, API contracts, ML pipeline, Ollama, and application functionality are
**untouched**. The premium Forest Green + Warm Ivory + Champagne Gold theme and
the Light / Dark / System architecture are preserved.

---

## 1. Design problem

The previous landing page was a single, centered text column with large empty
vertical regions (`py-20`, `mb-24`, `mb-28`), a flat static 7-card pipeline row,
three sparse bottom cards, a white "Initialize Health Profile" CTA, and
inaccurate "Vision-Language Food Recognition" / "Clinical diagnostics system"
wording that did not match the actual YOLOv8 + EfficientNet-B3 pipeline.

## 2. New visual concept

Apple-style product presentation × premium health-tech SaaS × subtle pseudo-3D
depth. A two-column hero with a lightweight CSS 3D "Dietary Intelligence Core",
a connected pipeline flow, richer technology panels, and a strong final CTA —
all with restrained champagne-gold accents. Terminology corrected to
**"AI-Powered Dietary Intelligence"** and **"dietary risk analytics"** (no
medical-diagnosis claims).

## 3. Hero redesign

- Asymmetric two-column hero (~88vh desktop): copy left, 3D visual right.
- Eyebrow badge, large headline *"Understand Your Meals. Discover Your Dietary
  Risk. Improve What Comes Next."* (forest-green gradient highlight), concise
  description, primary CTA **Analyze Your Meal** (`/register`) and secondary
  CTA **Explore the Methodology** (`/about`), and a quiet technology strip
  (YOLOv8 • EfficientNet-B3 • XGBoost • DCI • NIS • Local AI).

## 4. 3D intelligence visualization

Pure CSS/React/SVG (no Three.js/WebGL). A `perspective` container with a
`preserve-3d` scene:

- glass sphere core with radial gradients, inset highlights, and an animated
  ECG line (SVG);
- slow rotating outer ring with a gold dot, inner dashed ring;
- six floating glass mini-cards at different depths (Food Detected · Nutrition ·
  DCI · NIS · Risk · AI Coach) showing **illustrative** values, clearly labelled
  "Illustrative analysis";
- subtle desktop **mouse parallax** (±8°) on the scene, disabled on tablet/mobile
  and under `prefers-reduced-motion`.

## 5. Pipeline redesign

The flat 7-card row became a **6-stage flow** (Upload → Detect → Classify →
Analyze → Predict → Explain) with an animated gradient connector line on
desktop; stages stack vertically on mobile. Each stage: number, icon, title,
one-line description; hover lifts the card and tints the border green/gold.

## 6. Technology section

Replaced the three sparse cards with three premium feature panels
(01 Computer Vision, 02 Dietary Intelligence, 03 Explainable Guidance), each
with a visual mini-diagram (data bars), gold tech-label, and hover lift.

## 7. Animation system

- Continuous, slow: floating cards, core pulse, breathing glow, rotating rings,
  ECG dash.
- Entrance + scroll reveal via framer-motion (`whileInView`, one-shot).
- `@media (prefers-reduced-motion: reduce)` disables all landing animations.
- No bouncing, neon, or large continuous motion.

## 8. Light mode

Warm ivory background with a subtle forest-green radial glow, a faint
data-grid mask, and a restrained champagne-gold corner glow. White cards,
forest-green primary, muted sage/gold accents — all via the existing semantic
tokens.

## 9. Dark mode

Independent design: deep forest-charcoal with a muted emerald glow and
restrained gold illumination. Cards become layered dark-green surfaces; ivory
typography; the 3D core uses dark glass with an emerald sphere and gold ring.

## 10. Responsive behavior

- Desktop: two-column hero.
- Tablet (≤1023px): single-column, core below the copy.
- Mobile (≤767px): stacked copy → CTA → core; pipeline becomes vertical; mouse
  parallax disabled; core size reduced.
- `overflow-x: hidden` on the root — no horizontal overflow.

## 11. Accessibility

- `prefers-reduced-motion` respected (animations/transitions off).
- Decorative visuals use `aria-hidden="true"`.
- Semantic headings, keyboard-focusable links/buttons, visible hover/focus
  states, and risk/tech wording kept accurate (no fabricated metrics, no
  medical-diagnosis claims).

## 12. Performance considerations

No new runtime dependencies; no Three.js/WebGL/videos/large images. The 3D
effect uses CSS transforms + one small inline SVG; animations are GPU-friendly
(transform/opacity only). Cards labelled "Illustrative" so no fabricated values
are presented as a real user analysis.

## 13. Files modified

**Created**
- `frontend/components/landing/landing.css` — scoped landing styles (`.lr-*`).
- `frontend/components/landing/LandingNav.tsx`
- `frontend/components/landing/HeroSection.tsx`
- `frontend/components/landing/IntelligenceCore.tsx`
- `frontend/components/landing/PipelineFlow.tsx`
- `frontend/components/landing/TechnologyPanel.tsx`
- `frontend/components/landing/FinalCTA.tsx`

**Modified**
- `frontend/app/page.tsx` — now composes the landing components; corrected
  terminology; softened footer claim; preserved the logged-in redirect and
  `/login` / `/register` / `/about` routing.

## 14. TypeScript result

`npx tsc --noEmit` → **0 errors (PASS)**.

## 15. Build result

`npm run build` → **success — all routes compile, including `/`, `/login`,
`/register`, `/about` (PASS)**. Live dev server verified: the new hero text and
landing components render on `/`, and `/login` / `/register` / `/about` return
HTTP 200.

---

*No API keys or secrets are included in this document.*
