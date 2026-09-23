# Product

## Register

product

## Users

Primary users are clinic staff and patients interacting with the Essentia AI Medical Scheduling Assistant in a demonstrative setting. Clinic coordinators/receptionists evaluate whether the conversational scheduling flow feels trustworthy and efficient; patients (or evaluators role-playing as patients) use chat and audio to request appointments while watching the deterministic appointment history stay in sync. Context of use: desktop-first, well-lit daytime environments (clinic front desk or home), task-focused sessions where the interface must disappear into the scheduling workflow. This repo is also a technical case study for an AI Analyst role, so craft and clarity of the integration boundaries matter.

## Product Purpose

A presentation and interaction layer for the Essentia AI Medical Scheduling Assistant: patient selection, text/audio conversation with an n8n AI Agent, and a read-only appointment history synchronized from FastAPI after every completed turn. Success looks like: the full scheduling conversation works end-to-end, async states are explicit, failures never lie about domain mutations, and the UI reflects the Essentia pharma brand without inventing scheduling rules client-side.

## Brand Personality

Sophisticated, restrained, precise. Three words: elegant, clinical, trustworthy. The visual identity is a dark gold/bronze (#b89b58, #8c733d) on white with Roman serif display moments (Cinzel), wide tracking on labels, thin horizontal rules, and rigid 90°/45° geometry. Emotional goals: confidence in the brand, calm during conversation, zero gimmick.

## Anti-references

- Generic healthcare SaaS: white + teal/mint gradients, rounded-2xl everything, stock photo cards.
- Consumer chat toys: bubbly radii, purple AI gradients, anthropomorphic avatars, bouncing decorative motion.
- Dark "premium" dashboards with neon accents (wrong ambient light and wrong brand).
- Landing-page patterns inside the app: hero metrics, gradient text, glassmorphism, side-stripe callouts.
- Over-decorated controls or invented affordances for standard tasks (the category bar is Linear/Stripe-style earned familiarity).

## Design Principles

1. Brand shows up in restraint: gold/bronze is the single accent for primary actions, selection, and focus, never decoration for its own sake.
2. The tool disappears into the task: familiar product affordances, explicit async states, no motion that does not convey state.
3. Deterministic trust: the UI never implies a mutation succeeded unless FastAPI history confirms it; honesty over polish when uncertain.
4. Geometry is identity: rigid corners (rounded-sm), thin rules, and wide-tracked labels carry the logo DNA without harming legibility.
5. Type serves hierarchy, not costume: Cinzel only at brand moments; Inter for every label, control, datum, and markdown body.

## Accessibility & Inclusion

Target WCAG 2.2 AA for text contrast and keyboard operation. All interactive controls need visible focus-visible styles (brand-colored ring), accessible names (already established via aria-label/aria-labelledby), and status never conveyed by color alone (badges pair color with text; alerts use role="alert"). Recording and audio failures must degrade to a fully functional text chat. Reduced-motion: honor prefers-reduced-motion for smooth-scroll and decorative pulses. Body and control text must pass contrast on gold/bronze surfaces (verify #8c733d + light text, avoid white on #b89b58 for small text).
