# DietRiskNet — Premium Green & Gold UI Redesign

**Scope:** Frontend **visual** redesign only. Backend, APIs, ML pipeline,
Ollama, authentication, and all business logic are **untouched**.
**Light / Dark / System** appearance modes are preserved and System mode was
made fully functional.

---

## 1. Design objective

Replace the blue-heavy "clinical template" identity with a premium **Forest
Green + Warm Ivory + Champagne Gold** language that communicates nutrition,
health, trust, intelligence, and clinical professionalism — a polished
commercial health/nutrition SaaS look suitable for an academic healthcare
project (not a restaurant, grocery, jewelry, gaming, or neon-AI aesthetic).

## 2. Previous visual identity

- Blue primary (`#2563EB`) everywhere (216 `brand-blue` usages).
- Neon cyan (`#06B6D4`) secondary accent (85 usages).
- Cool gray "charcoal" surfaces; hardcoded brand hexes in `@theme`.
- Light/Dark only; **System mode did not exist** (toggle between two states).

## 3. New visual identity

- **Forest green** (`#12372A` light / `#4F9B76` dark) = primary brand + actions.
- **Warm ivory** surfaces in light mode; **forest-charcoal** surfaces in dark.
- **Champagne gold** (`#C5A46D` / `#C9AB72`) = restrained accent (~5–10%).
- Semantic tokens drive everything; components consume tokens, not raw hex.

## 4. Light-mode palette

| Role | Value |
|---|---|
| Background | `#F8F7F2` (warm ivory) |
| Secondary surface | `#F3F1EA` |
| Cards | `#FFFFFF` |
| Primary / primary hover / deep | `#12372A` / `#1F513D` / `#0D2A20` |
| Champagne gold / soft gold | `#C5A46D` / `#D8C49A` |
| Text / muted text | `#18211D` / `#68756E` |
| Borders | `#E7E4DA` |
| Healthy / warning / high risk | `#27845A` / `#C98A2E` / `#B84A4A` |

## 5. Dark-mode palette

| Role | Value |
|---|---|
| Background / secondary / card / elevated | `#0C1511` / `#111D18` / `#16231D` / `#1A2922` |
| Primary green / hover | `#4F9B76` / `#5FAD86` |
| Champagne gold | `#C9AB72` |
| Text / muted text | `#F4F1E8` / `#A9B5AE` |
| Borders | subtle dark sage (`rgba(180,200,190,0.14)`) |
| Healthy / warning / high risk | soft emerald `#3E9C6C` / warm amber `#D39A45` / muted coral `#C76A6A` |

Dark mode is **independently designed** (not an inversion): very dark forest
surfaces, muted sage borders, restrained gold — an executive health dashboard.

## 6. System-mode behavior

- `theme` state is now `'light' | 'dark' | 'system'` (store).
- `ClientProviders` applies `.dark` for `dark`, and for `system` follows
  `matchMedia('(prefers-color-scheme: dark)')` **and live-updates** on OS
  changes.
- Sidebar / mobile header theme control now **cycles Light → Dark → System**
  with the correct icon (Sun / Moon / Monitor) and label.

## 7. Typography

Unchanged system font (Inter via `--font-sans`). Numeric hierarchy and
uppercase micro-labels retained; no font changes were introduced.

## 8. Gold usage rules

Gold is an **accent only** (~5–10% of the UI):
- Logo wordmark + icon (Sidebar / mobile header).
- Active navigation indicator bar.
- AI Dietitian badge icon and coach badge.
- Thin decorative top border on the Dashboard risk card.
- Chart highlights (one line color).

**Not used for:** whole cards, body text, primary buttons, or risk indicators.
Clinical risk colors (green/amber/red) keep semantic meaning.

## 9. Components redesigned

- **Sidebar:** deep forest green (light) / very dark forest (dark); gold logo
  + gold active indicator; ivory/sage text; refined hover surfaces; adapted
  user capsule, theme cycle, and logout; mobile header matched.
- **Theme tokens:** centralized semantic system in `globals.css`
  (`--background`, `--foreground`, `--card`, `--primary`, `--muted`,
  `--border`, `--gold`, `--sidebar`, brand aliases).
- **Cards/buttons/forms/badges/gauges:** re-skinned via tokens; form defaults
  now theme-aware.
- **Charts:** semantic mid-tone colors readable in both themes.
- **AI Dietitian card:** gold badge accent.
- **Glow/scrollbar:** forest/gold tints.

## 10. Pages redesigned

All pages inherit the new palette via tokens; targeted changes on:
Dashboard (gold risk-card accent), Upload (green CTA via tokens), Analysis
(AI card gold accent), Predictions / Recommendations (semantic risk colors),
History (fixed stray blue), Trends (chart colors), Nutrition Assistant (gold
coach badge), Profile / Auth (token-driven premium forms/surfaces).

## 11. Accessibility

- Risk is never communicated by color alone — text labels (Low / Moderate /
  High) are preserved alongside color.
- Contrast: light text `#18211D` on white/ivory; dark `#F4F1E8` on forest;
  gold used for icons/indicators, not body text (avoids low-contrast gold
  text).
- Focus rings, labels, aria attributes, and semantic HTML preserved.

## 12. Responsive design

Layouts unchanged (Sidebar mobile drawer, responsive grids/breakpoints
preserved). No horizontal overflow introduced; charts use
`ResponsiveContainer`.

## 13. Files modified (frontend only)

- `frontend/app/globals.css` — token system rewrite (light/dark palettes,
  semantic `@theme` mappings, gold/sidebar tokens, glows, scrollbar, forms).
- `frontend/lib/store.ts` — `theme: 'light'|'dark'|'system'`, `setTheme`,
  3-state `toggleTheme`.
- `frontend/components/ClientProviders.tsx` — System-mode implementation.
- `frontend/components/Sidebar.tsx` — premium green sidebar + gold + theme cycle.
- `frontend/app/history/page.tsx` — stray `bg-blue-500` → brand hover.
- `frontend/app/trends/page.tsx` — chart line/area colors.
- `frontend/components/analysis/AIDietitianCard.tsx` — gold AI badge.
- `frontend/app/nutrition/page.tsx` — gold coach badge.
- `frontend/app/dashboard/page.tsx` — gold risk-card accent.

## 14. Screens/pages manually verified

Verified via token audit + `tsc` + production build + static inspection of every
page (Dashboard, Upload, Analysis, Predictions, Recommendations, History,
Trends, Nutrition, Profile, Login, Register, Research, About). **No browser
automation was available**, so no screenshot-level visual pass was performed —
verification was by theme-token consistency, type-check, build, and static
review of each page's class usage (no remaining blue utilities; no white-on-
white or dark-on-dark surfaces in token definitions).

## 15. TypeScript result

`npx tsc --noEmit` → **0 errors (PASS)**.

## 16. Production-build result

`npm run build` → **success, 17/17 routes (PASS)**.

## 17. Backend regression result

`pytest backend/tests -q` → **169 passed / 0 failed (PASS)** — confirms the
frontend redesign did not affect backend behavior.

---

*No API keys or secrets are included in this document.*
