# Conference Web — UI Kit

Interactive recreation of the NAMD 2026 Fall Conference marketing site. Built from the provided branding guide, logos, and mobile hero imagery.

## Files
- `index.html` — Entry; renders the full site with client-side page switching.
- `site.css` — Site-level styles layered on `colors_and_type.css`.
- `Chrome.jsx` — `TopBar`, `SiteHeader`, `SiteFooter`.
- `Hero.jsx` — `Hero`, `StatsBar`, `AboutSection`.
- `Program.jsx` — `AgendaSection` (with day tabs), `SpeakersSection`.
- `Register.jsx` — `RegisterSection` with tier selection + confirmation state.
- `Sponsors.jsx` — Tiered sponsor grid on dark blue.

## Click-through
- Nav between Overview / Agenda / Speakers / Register / Sponsors.
- Agenda day tabs (Day 1 / 2 / 3).
- Register form — fill and submit to see confirmation state.

## Notes
Hero background uses `assets/hero-mobile-2.png` (convention center) as stand-in. Speaker portraits are initial-tile placeholders — swap to real photos when provided. Sponsor names are illustrative.
