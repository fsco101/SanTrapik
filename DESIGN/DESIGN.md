---
name: Obsidian Telemetry
colors:
  surface: '#0f131c'
  surface-dim: '#0f131c'
  surface-bright: '#353942'
  surface-container-lowest: '#0a0e16'
  surface-container-low: '#181c24'
  surface-container: '#1c2028'
  surface-container-high: '#262a33'
  surface-container-highest: '#31353e'
  on-surface: '#dfe2ee'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#dfe2ee'
  inverse-on-surface: '#2c3039'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00885d'
  on-tertiary-container: '#000703'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0f131c'
  on-background: '#dfe2ee'
  surface-variant: '#31353e'
  surface-bg: '#080C14'
  surface-panel: '#0F172A'
  surface-card: '#1E293B'
  surface-elevated: '#334155'
  border-subtle: rgba(255, 255, 255, 0.08)
  traffic-normal: '#10B981'
  traffic-moderate: '#F59E0B'
  traffic-heavy: '#F97316'
  traffic-severe: '#EF4444'
  ai-primary: '#6366F1'
  ai-glow: rgba(99, 102, 241, 0.25)
  ai-cyan: '#06B6D4'
  text-primary: '#F8FAFC'
  text-secondary: '#94A3B8'
  text-muted: '#64748B'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.025em
  display-lg-mobile:
    fontFamily: Outfit
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2.25rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Outfit
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.015em
  body-lg:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-md:
    fontFamily: Inter
    fontSize: 0.938rem
    fontWeight: '400'
    lineHeight: 1.375rem
  body-sm:
    fontFamily: Inter
    fontSize: 0.813rem
    fontWeight: '400'
    lineHeight: 1.25rem
  telemetry-display:
    fontFamily: JetBrains Mono
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: 2rem
    letterSpacing: -0.03em
  telemetry-lg:
    fontFamily: JetBrains Mono
    fontSize: 1.25rem
    fontWeight: '700'
    lineHeight: 1.5rem
    letterSpacing: -0.02em
  telemetry-md:
    fontFamily: JetBrains Mono
    fontSize: 0.938rem
    fontWeight: '600'
    lineHeight: 1.25rem
  telemetry-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Inter
    fontSize: 0.688rem
    fontWeight: '700'
    lineHeight: 0.875rem
    letterSpacing: 0.08em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-base: 1rem
  space-lg: 1.25rem
  space-xl: 1.5rem
  space-2xl: 2rem
  space-3xl: 3rem
  sidebar-width: 26.25rem
  sheet-collapsed-height: 4.5rem
  gutter: 1rem
  panel-gap: 0.75rem
---

## Brand & Style

The design system establishes a high-performance, dark-mode first telemetry aesthetic inspired by modern avionics flight decks and metropolitan transit operation command centers. Designed for commuters and logistics operators navigating congested metropolitan arterials, the interface prioritizes immediate legibility, reduced cognitive friction, and strict differentiation between observed sensor reality and machine-learning predictions.

The aesthetic philosophy draws from a fusion of **Tactical Minimalism** and **Technical Glassmorphism**:
- Ultra-deep obsidian surfaces absorb environmental glare during night commutes and high-stress driving conditions.
- Strict visual hierarchy relies on luminous semantic signal colors rather than decorative artwork, treating route data and incident diagnostics as mission-critical instrumentation.
- AI forecasting states are treated with an electric, luminescent spectral signature (deep indigo and cyan), clearly delineating algorithmic projections from ground-truth telemetry.
- Micro-textures, low-opacity borders, and structural tabular alignments create an atmosphere of engineering precision, scientific transparency, and calm control amidst urban chaos.

## Colors

The chromatic architecture operates on three disciplined planes: **Base Obsidian Infrastructure**, **Semantic Telemetry Signals**, and **Electric Predictive Intelligence**.

### Structural Surfaces & Neutrals
- `surface-bg` (`#080C14`): The foundational infinite canvas, minimizing OLED power consumption and suppressing peripheral screen glow.
- `surface-panel` (`#0F172A`): First-order containers, persistent drawers, and flight-deck navigation shells.
- `surface-card` (`#1E293B`): Nested telemetry modules, route breakdowns, and incident diagnostics containers.
- `surface-elevated` (`#334155`): Hover surfaces, active segment rings, flyout layers, and modal drawers.
- `border-subtle` (`rgba(255, 255, 255, 0.08)`): Ghost divisions maintaining structural containment without high-contrast clutter.

### Semantic Traffic Signal Tiers
Chromatic saturation in the traffic spectrum is reserved strictly for real-time velocity states and cannot be used for decorative styling:
- **Normal** (`#10B981`): Free-flowing arterials ($\ge 80\%$ baseline velocity).
- **Moderate** (`#F59E0B`): Rolling friction, minor density wave ($50\% - 79\%$ baseline).
- **Heavy** (`#F97316`): Severe bottlenecks, queuing delays ($25\% - 49\%$ baseline).
- **Severe** (`#EF4444`): Crawl, gridlock, active lane blockage ($< 25\%$ baseline).

### AI & Prediction Matrix
Algorithmic projections are visually insulated from ground truth. Predictions use `ai-primary` (`#6366F1`) and `ai-cyan` (`#06B6D4`) paired with `ai-glow` backdrops. If a metric or badge is rendered in indigo or cyan, the user immediately identifies it as forward-looking modeled intelligence rather than an active roadside sensor check.

## Typography

The typographical system enforces a deliberate dual-engine structure:

1. **Human Interface & Wayfinding (`Outfit` & `Inter`)**:
   - `Outfit` brings architectural, geometric authority to route titles, section headers, and primary diagnostics.
   - `Inter` governs all narrative text, incident context, and system dialogs, delivering optical clarity across varying device sizes.

2. **Instrumental Telemetry (`JetBrains Mono`)**:
   - Every speed reading (`14 km/h`), duration adjustment (`+32 min`), timestamp (`21:42`), confidence rating (`82%`), and lane code is rendered strictly in `JetBrains Mono`.
   - All telemetry values must feature tabular numbering (`font-variant-numeric: tabular-nums`) to prevent layout jitter during real-time streaming updates.
   - Sub-label metadata and section categorizers utilize uppercase high-tracking labels (`label-caps`) to mirror military avionics HUD ergonomics.

## Layout & Spacing

The layout model is designed around map-centric situational awareness using a **Split Control Console** on large viewports and an **Elastic Floating Sheet** on mobile viewports.

### Breakpoint Strategy
- **Mobile (`< 768px`)**: Full-bleed spatial map canvas. The interface operates through a dynamic floating query bar anchored to top-safe areas and a gesture-driven bottom sheet holding route intelligence and telemetry logs.
- **Tablet (`768px - 1023px`)**: Map-centric canvas with an absolute floating intelligence overlay panel (`380px` width) docked to the left edge with `16px` margins.
- **Desktop (`>= 1024px`)**: Fixed dual-tier command console. A persistent `sidebar-width` (`420px` / `26.25rem`) telemetry rail docks on the left, flanked by a 100vh interactive MapLibre canvas on the right. An optional collapsible incident flyout attaches to the inner map boundary.

### Rhythm & Density
The grid is built on a tight `4px` base increment with an operational standard of `8px` (`space-sm`) and `16px` (`space-base`). Density is kept deliberately compact to display multiple diagnostic fields (corridor speeds, collision clearance progress, confidence tiers) without vertical scrolling.

## Elevation & Depth

Depth is established through stacked dark obsidian tiers and precise luminous rim illumination, avoiding heavy drop shadows that blur in low-light environments.

### Tonal Stratification
- **Ground 0 (Base Map Canvas)**: Deep slate map vectors rendered at `#080C14`.
- **Level 1 (Structural Rail & Sheet)**: `#0F172A` with a 1px solid border of `rgba(255, 255, 255, 0.08)`.
- **Level 2 (Diagnostic Cards & Segment Rows)**: `#1E293B` nested within `#0F172A`, separating independent route segments.
- **Level 3 (Interactive Controls & Dropdowns)**: `#334155` elevated with subtle directional rim lights.

### Optical Highlights & AI Auroras
- **Standard Containment**: Micro-borders use `rgba(255, 255, 255, 0.06)` to `rgba(255, 255, 255, 0.12)`.
- **Active Traffic Alert Glow**: Severe incident badges emit a diffused warning ring: `box-shadow: 0 0 16px rgba(239, 68, 68, 0.25)`.
- **AI Prognostic Aura**: Machine learning prediction components employ a localized spectral aura: `box-shadow: 0 0 24px rgba(99, 102, 241, 0.20), inset 0 0 0 1px rgba(99, 102, 241, 0.4)`.
- **Glass Frosting**: Floating overlays and map chips leverage `backdrop-filter: blur(12px)` over `#0F172A` with an 85% alpha channel to maintain continuous orientation of underlying map geometry.

## Shapes

The design system implements a **Soft-Precision geometry** (`roundedness: 1` / `0.25rem` to `0.5rem` baseline). This balances contemporary dashboard software conventions with the rigorous, squared-off instrumentation of aeronautical consoles.

- **Base Components (Badges, Buttons, Inputs)**: `0.25rem` (4px) or `0.375rem` (6px) corner radius.
- **Surface Panels & Route Cards**: `0.5rem` (8px) corner radius.
- **Telemetry Indicators & Pill Status Badges**: Fully rounded (`9999px`) only for discrete binary state pills (e.g., `● Telemetry Live`).
- **Data Graphs & Segment Meters**: Crisp square-ended bar tracks with `2px` micro-fillets to preserve data accuracy without round-off distortion.

## Components

### Buttons
- **Primary AI Action Button**: Background `#6366F1`, text `#FFFFFF`, radius `0.375rem`. Hover state scales lightness with a localized `rgba(99, 102, 241, 0.35)` glow.
- **Telemetry Ghost Button**: Transparent surface, border `1px solid rgba(255, 255, 255, 0.15)`, text `#F8FAFC`. On hover: surface `#1E293B` and border `rgba(255, 255, 255, 0.3)`.
- **Quick-Corridor Corridor Pills**: Compact pills featuring monospaced shorthand indicators (e.g., `[EDSA] QC → BGC`), text `#94A3B8`, background `#0F172A`, active state highlighted with `border-color: #6366F1`.

### Badges & Diagnostic Chips
- **Observed Telemetry Badge**: Surface `#1E293B`, border `1px solid rgba(255, 255, 255, 0.1)`. Features a solid colored dot corresponding to semantic condition (`#10B981`, `#F59E0B`, `#F97316`, or `#EF4444`) followed by monospaced speed and observation time.
- **AI Prognosis Badge**: Surface `rgba(99, 102, 241, 0.12)`, border `1px solid rgba(99, 102, 241, 0.4)`, text `#C7D2FE`. Prefixed with the distinctive electric sparkle glyph (`✦`).
- **Telemetry Live Pulsar**: Micro-badge featuring an emerald indicator dot paired with an oscillating ripple animation (`ping` utility) showing real-time socket connection.

### Route Intelligence Card
- Built on a `#0F172A` base with an inner `#1E293B` sub-grid.
- **Header**: Primary destination title in `Outfit` (Bold), right-aligned severity status badge.
- **Time Metric Cluster**: Monospaced numbers displaying calculated travel time, normal baseline time, and net differential (+/- minutes highlighted in relevant traffic color).
- **Incident Accordion**: Sub-panel displaying obstruction classification (`Accident`, `Flood`, `Roadwork`), exact landmark, agency source tag (`MMDA`, `Skyway Ops`), and verified time stamp.
- **AI Prediction Footer**: Bordered with a distinct top divider using `rgba(99, 102, 241, 0.25)`. Houses the forecasted clearing time (`JetBrains Mono`), linear confidence bar (`06B6D4`), and algorithm version.

### Segment Velocity Bar
- Multi-segment progress bar visually displaying route segment health.
- Segment widths represent distance weighting; fill colors use strict traffic telemetry tokens (`traffic-normal`, `traffic-moderate`, `traffic-heavy`, `traffic-severe`).
- Interactive hover or tap invokes a micro-tooltip showing average segment velocity (e.g., `Guadalupe to Buendia: 8 km/h`).

### Form Inputs & Search Telemetry
- **Route Search Field**: Full-width `#0F172A` field, `1px solid rgba(255, 255, 255, 0.12)` border. On focus: border becomes `1px solid #6366F1` with an inner glow. Placeholder text set to `text-muted` (`#64748B`). Left-aligned with custom terminal-inspired origin and destination waypoint pins.