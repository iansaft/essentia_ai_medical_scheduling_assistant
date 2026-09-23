---
name: Essentia AI Medical Scheduling Assistant
description: Restrained clinical luxury scheduling UI: aged brass accent on warm vellum, Roman serif brand moments, rigid geometry.
colors:
  brand: "#b89b58"
  brand-light: "#d4c295"
  brand-dark: "#8c733d"
  brand-press: "#7a6334"
  surface: "oklch(0.995 0.006 90)"
  raised: "oklch(0.999 0.003 90)"
  canvas: "oklch(0.972 0.008 90)"
  line: "oklch(0.92 0.012 90)"
  line-strong: "oklch(0.87 0.015 90)"
  ink: "oklch(0.22 0.02 80)"
  ink-muted: "oklch(0.5 0.015 80)"
  ink-faint: "oklch(0.68 0.012 85)"
  ink-inverse: "oklch(0.99 0.005 90)"
  danger: "oklch(0.5 0.19 25)"
  danger-soft: "oklch(0.965 0.025 25)"
  danger-line: "oklch(0.88 0.07 25)"
  success: "oklch(0.5 0.13 155)"
  success-soft: "oklch(0.965 0.03 155)"
  warning: "oklch(0.52 0.11 70)"
  warning-soft: "oklch(0.965 0.04 85)"
  warning-line: "oklch(0.88 0.07 85)"
  info: "oklch(0.5 0.13 250)"
  info-soft: "oklch(0.965 0.03 250)"
typography:
  display:
    fontFamily: "Cinzel, Playfair Display, ui-serif, Georgia, serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.2em"
  headline:
    fontFamily: "Cinzel, Playfair Display, ui-serif, Georgia, serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.05em"
  title:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "normal"
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.12em"
rounded:
  sm: "2px"
  full: "9999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "20px"
components:
  button-primary:
    backgroundColor: "{colors.brand-dark}"
    textColor: "{colors.ink-inverse}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px"
    height: "44px"
    width: "44px"
  button-primary-hover:
    backgroundColor: "{colors.brand-press}"
  button-secondary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.sm}"
    padding: "12px"
    height: "44px"
    width: "44px"
  input-text:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "10px 12px"
  card:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "16px"
  chip-status:
    backgroundColor: "{colors.info-soft}"
    textColor: "{colors.info}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "4px 8px"
  header-tile:
    backgroundColor: "{colors.brand-dark}"
    textColor: "{colors.ink-inverse}"
    rounded: "{rounded.sm}"
    size: "40px"
---

# Design System: Essentia AI Medical Scheduling Assistant

## 1. Overview

**Creative North Star: "The Bronze Instrument"**

This system treats the interface as a precision instrument machined from aged brass and warm paper: every surface is flat stock, every division is a hairline, and gold appears only where the instrument requires force (primary action, selection, focus). Restrained clinical luxury means sophistication through subtraction. No decoration earns a pixel unless it carries hierarchy or state.

The palette is deliberately quiet so the scheduling task stays loud. Cinzel appears only at brand moments (header wordmark, empty-state titles); Inter owns every label, control, datum, and markdown body. Geometry is identity: rigid corners (`rounded-sm`, 2px), 1px rules, wide-tracked uppercase labels, and a thin gold divider as the sole ornamental gesture.

It explicitly rejects the anti-references in PRODUCT.md: generic healthcare SaaS (white + teal/mint gradients, rounded-2xl everything, stock photo cards), consumer chat toys (bubbly radii, purple AI gradients, anthropomorphic avatars, bouncing motion), dark "premium" dashboards with neon accents, landing-page patterns inside the app (hero metrics, gradient text, glassmorphism, side-stripe callouts), and over-decorated or invented affordances for standard tasks.

**Key Characteristics:**
- Restrained: aged brass is the single accent, never ambient decoration
- Crisp and quiet controls: dry, sober, Linear/Stripe-earned familiarity
- Flat surfaces separated by hairlines; elevation only for floating chat chrome
- Roman serif (Cinzel) strictly at brand moments; Inter everywhere else
- Rigid 90° geometry, wide-tracked labels, thin horizontal rules
- Deterministic honesty: status is text + color, never color alone

## 2. Colors

Warm vellum neutrals with a single aged-brass accent; semantic states stay muted and always pair with icon or text.

### Primary
- **Aged Brass** (#b89b58): Logo-derived accent for focus rings, selection wash, hairline dividers at 40–50% opacity, and the global `:focus-visible` outline. Never a large fill for body text.
- **Burnished Bronze** (#8c733d): Workhorse brand surface. Primary button backgrounds, user chat bubbles, header tile, panel section icons. Dark enough for `ink-inverse` text at AA.
- **Tincture Press** (#7a6334): Hover/active press state for Burnished Bronze surfaces. Darkens on interaction; never a resting color.
- **Pale Gilt** (#d4c295): Soft brand for `::selection` background and focus ring tint (`ring-brand-light/60`). Decorative support only.

### Neutral
- **Warm Vellum Sheet** (oklch(0.995 0.006 90)): App shell/header sticky surface (`surface`).
- **Parchment Stock** (oklch(0.999 0.003 90)): Raised cards, inputs, panel bodies (`raised`). Near-white without pure #fff.
- **Ledger Canvas** (oklch(0.972 0.008 90)): Page background and recessed wells (`canvas`).
- **Hairline Sand** (oklch(0.92 0.012 90)): Default borders and dividers (`line`).
- **Rule Sand** (oklch(0.87 0.015 90)): Input borders and stronger structural edges (`line-strong`).
- **Walnut Ink** (oklch(0.22 0.02 80)): Primary text (`ink`). Warm near-black, never #000.
- **Slate Umber** (oklch(0.5 0.015 80)): Secondary text and labels (`ink-muted`).
- **Ghost Sand** (oklch(0.68 0.012 85)): Placeholder and hint text (`ink-faint`).
- **Inverse Parchment** (oklch(0.99 0.005 90)): Text/icons on Burnished Bronze (`ink-inverse`).

### Tertiary
- **State semantics only:** danger (oklch(0.5 0.19 25)), success (oklch(0.5 0.13 155)), warning (oklch(0.52 0.11 70)), info (oklch(0.5 0.13 250)), each with `-soft` tint fills and optional `-line` borders. Status badges use soft + text; alerts add icon and `role="alert"`.

### Named Rules
**The One Accent Rule.** Gold/bronze is the single accent for primary actions, selection, and focus, never decoration for its own sake. Aged Brass does not fill large surfaces.
**The No-Warning-Gold Rule.** Amber warnings must not borrow brand gold. Warnings use the warning tokens and always ship an icon; status is never color alone.
**The No-Pure-Neutrals Rule.** Never #000 or #fff. Every neutral carries the brand's warm hue (chroma ~0.005–0.02).

## 3. Typography

**Display Font:** Cinzel (fallback Playfair Display, ui-serif, Georgia, serif)
**Body Font:** Inter (fallback ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif)
**Label/Mono Font:** Inter (no separate mono in this system)

**Character:** Cinzel is the Roman seal: uppercase, wide-tracked, reserved for brand voice. Inter is the clinical workhorse: neutral, dense, legible at 11–14px control sizes. The pairing separates identity from instrumentation.

### Hierarchy
- **Display** (Cinzel 600, 0.875rem / 14px, tracking 0.2em, line-height 1.25): Header wordmark `ESSENTIA AI`, uppercase only.
- **Headline** (Cinzel 600, 0.875rem, tracking ~0.05em wide, line-height 1.4): Empty-state titles in chat (e.g. patient prompt above the gold divider).
- **Title** (Inter 600, 0.875rem, line-height 1.4): Panel headers, appointment service names, section titles.
- **Body** (Inter 400, 0.875rem, line-height 1.5): Chat markdown (via prose-stone), composer text; max measure stays within chat column (~65–75ch in prose blocks).
- **Label** (Inter 600, 0.6875–0.75rem, tracking 0.12–0.14em, uppercase): Status pills, connection badge, micro-labels.
- **Caption** (Inter 400, 0.6875–0.75rem, line-height ~1.4): Hints (`Enter envia…`), metadata under titles (`text-xs text-ink-muted`).

### Named Rules
**The Seal Rule.** Cinzel only at brand moments: header wordmark and empty-state headings. Inter for every label, control, datum, and markdown body. Type serves hierarchy, not costume.
**The Tracking Rule.** Uppercase labels carry 0.12em+ letter-spacing; display wordmark carries 0.2em. Never set uppercase Inter or Cinzel tight.

## 4. Elevation

Flat by default. Depth is tonal (canvas → raised → surface) plus 1px Hairline Sand borders. Shadows are rare and structural: floating chat chrome and side-panel cards may use Tailwind's `shadow-sm` so they lift off the canvas without looking glossy. No blur glass, no stacked elevation scales.

### Shadow Vocabulary
- **Panel lift** (`box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05)`, Tailwind `shadow-sm`): Chat shell, appointments card, patient selector, typing indicator bubble. Ambient and minimal.
- **None:** Header (hairline + 90% surface + backdrop-blur only), buttons, inputs, badges, list rows.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest. `shadow-sm` only on floating panels; never on rows, chips, or nested children. If a shadow reads as a drop-shadow poster, the blur is wrong for this system.

## 5. Components

Controls are crisp and quiet: dry borders, bronze only for the committed action, no bounce, no glow beyond the focus ring.

### Buttons
- **Shape:** rigid corner (2px, `rounded-sm`); icon buttons square (`size-9` / `size-11`).
- **Primary (Send, Enviar áudio):** Burnished Bronze fill (#8c733d), Inverse Parchment icon/text, 44px square or `px-3 py-1.5` label buttons; `transition`.
- **Hover / Active:** Tincture Press (#7a6334) on hover (darkens, AA-safe). Never lighten toward Pale Gilt for small text on gold.
- **Focus:** `outline 2px solid brand` global + `focus-visible:outline-brand` / offset on primary; inputs use border shift to Aged Brass + `ring-2 ring-brand-light/60`.
- **Secondary / Ghost (Mic, Refresh, Descartar):** Parchment Stock fill, 1px Rule Sand border, ink-muted icon; hover washes to Ledger Canvas. Disabled: `opacity-40` or `opacity-50`, `cursor-not-allowed`.
- **Danger inline (Parar recording):** lives on danger-soft strip; text danger; optional `focus-visible:outline-danger`.

### Chips (Status / Connection)
- **Style:** soft tint fill + saturated text, no border; rectangular (`rounded-sm`), not pill.
- **Status (Appointments):** scheduled → info-soft/info; completed → success-soft/success; cancelled → danger-soft/danger; no_show → warning-soft/warning. Uppercase Label type, tracking 0.12em, `px-2 py-1`, 11px semibold. Text always present (never color alone).
- **Connection (Header):** success-soft or warning-soft with Wifi icon, uppercase tracking 0.14em.

### Cards / Containers
- **Corner Style:** 2px (`rounded-sm`).
- **Background:** Parchment Stock (`raised`) for panels; chat message stream uses Ledger Canvas (`canvas`); header uses Warm Vellum at 90% opacity + backdrop-blur.
- **Shadow Strategy:** Panel lift only (`shadow-sm`); see Elevation.
- **Border:** 1px Hairline Sand (`border-line`); header bottom rule is `border-brand/40`.
- **Internal Padding:** 16px (`p-4` / `px-4 py-3`); list rows `p-4` separated by `divide-y divide-line`.

### Inputs / Fields
- **Style:** Parchment Stock fill, 1px Rule Sand border, 2px radius, `px-3 py-2.5`, body 14px; placeholder Ghost Sand.
- **Focus:** border → Aged Brass, `ring-2 ring-brand-light/60`, no layout shift.
- **Disabled:** Ledger Canvas fill, not-allowed cursor.
- **Select (Patient):** same field chrome; native select, full width.

### Navigation
- **App header:** single bar, `min-h-16`, Warm Vellum/90 + blur, bottom hairline `border-brand/40`. Left: 40px Burnished Bronze tile (2px radius) + Cinzel uppercase wordmark + Inter muted subtitle. Right: connection chip. No tab bar; the app is one screen.

### Signature Components
- **Brand tile + wordmark:** 40×40 bronze square with Activity icon; `ESSENTIA AI` in Cinzel 600 uppercase tracking 0.2em.
- **Gold hairline divider:** short centered `border-t border-brand/50` (e.g. width 4rem) under empty-state titles. The logo's thin rule, used once per empty state.
- **Message bubbles:** user = Burnished Bronze + inverse text, right-aligned, max-width 82%; agent = Parchment Stock + hairline + `shadow-sm`, left-aligned; prose-stone inside. Avatars: 32px circles (full radius only here); user avatar bronze, agent avatar raised + border.
- **Recording strip:** informational strip with pulsing danger dot, timer, and status label only (no inline Stop). The secondary action slot toggles: Mic (neutral) while idle → Stop on `info-soft`/`info` (same tone as scheduled status) while recording → Discard (Trash) on `danger-soft`/`danger` (same tone as cancelled status) after stop → Mic again after discard or send. Primary Enviar stays bronze.

## 6. Do's and Don'ts

### Do:
- **Do** use Burnished Bronze (#8c733d) + Inverse Parchment for every primary action and the user bubble; verify AA for text on bronze.
- **Do** keep corners rigid (`rounded-sm`, 2px); full radius only on avatars and the recording pulse dot.
- **Do** separate layers with 1px Hairline Sand or `border-brand/40` hairlines; wide-track uppercase labels (0.12em+).
- **Do** reserve Cinzel for header wordmark and empty-state titles; Inter for all controls, data, and markdown.
- **Do** pair every status color with text (and icon where the state is failure/warning); use `role="alert"` for failures.
- **Do** honor `prefers-reduced-motion`; keep motion state-only (spinner, typing dots, recording pulse).
- **Do** show explicit async states (Processando, loading rows, disabled composer) without implying a mutation succeeded until FastAPI history confirms it.

### Don't:
- **Don't** use generic healthcare SaaS: white + teal/mint gradients, `rounded-2xl` everything, stock photo cards.
- **Don't** use consumer chat toys: bubbly radii, purple AI gradients, anthropomorphic avatars, bouncing decorative motion.
- **Don't** build dark "premium" dashboards with neon accents (wrong ambient light and wrong brand).
- **Don't** use landing-page patterns inside the app: hero metrics, gradient text (`background-clip: text`), glassmorphism, side-stripe callouts (`border-left` > 1px as accent).
- **Don't** over-decorate controls or invent affordances; the category/status bar stays Linear/Stripe-style earned familiarity.
- **Don't** put white or small light text on Aged Brass (#b89b58); primary fills stay on Burnished Bronze.
- **Don't** use em dashes (or `--`) in UI copy; use commas, colons, parentheses, or periods.
- **Don't** animate CSS layout properties; no bounce/elastic easing on controls.
