# BRAND.md — SanTrapik Brand Identity & Design System

---

## 1. Brand Essence & Story

### 1.1 The Name: SanTrapik
The name **SanTrapik** is a play on the quintessential Filipino commuter question:
> **"Saan trapik?"** *(Where is the traffic?)*

For millions of Filipinos navigating Metro Manila every day, knowing that EDSA or C-5 is congested is not news — congestion is the default assumption. The real questions every commuter asks are:
- *Why is it stuck right now?*
- *Is there an accident, flood, or construction up ahead?*
- *How much delay will it cost me?*
- *When will it ease up?*

SanTrapik elevates this daily question from helpless frustration into **actionable traffic intelligence**.

### 1.2 Brand Tagline
> **"Understand your route — not just where to go."**  
> *(Secondary: "AI-Powered Metro Manila Traffic Intelligence & Incident Relief")*

### 1.3 Brand Personality & Voice
- **Pragmatic & Honest:** We don't sugarcoat traffic conditions. If EDSA is at a standstill with a 45-minute delay, we state it plainly.
- **Empathetic to the Commuter:** Designed for people who lose hours of their lives daily in Manila traffic. Every screen respects their time and attention.
- **Scientifically Transparent:** We strictly separate verifiable facts (MMDA incident logs, actual sensor speeds) from AI forecasts. Predictions are always clearly labeled as predictions with confidence intervals.
- **Calm & High-Tech:** Amidst real-world chaos and noise, the SanTrapik interface is clean, dark-mode first, and telemetry-focused — reminiscent of a modern flight deck or traffic control center.

---

## 2. Color Palette & Semantic Tokens

SanTrapik utilizes a dark-mode first design system optimized for high contrast, low eye fatigue during night driving or commutes, and unmistakable semantic clarity.

### 2.1 Base Surface & Structural Colors (Dark Mode)
| Token Name | Hex Code | Tailwind Equivalent | Role & Application |
| :--- | :--- | :--- | :--- |
| `surface-bg` | `#080C14` | `slate-950` | Primary app background (deep midnight obsidian) |
| `surface-panel` | `#0F172A` | `slate-900` | Cards, sidebars, bottom sheets |
| `surface-card` | `#1E293B` | `slate-800` | Nested component containers, segment items |
| `surface-elevated`| `#334155` | `slate-700` | Hover states, active borders, dropdown menus |
| `border-subtle` | `rgba(255,255,255,0.08)` | `border-white/10` | Divider lines and card outlines |
| `text-primary` | `#F8FAFC` | `slate-50` | Primary headlines, key metrics, route titles |
| `text-secondary`| `#94A3B8` | `slate-400` | Subtitles, helper text, timestamps |
| `text-muted` | `#64748B` | `slate-500` | Inactive icons, subtle metadata |

### 2.2 Semantic Traffic Telemetry Colors
These colors are strictly reserved for traffic conditions on maps, badges, and progress meters.

| Traffic State | Hex Code | Tailwind Token | Meaning & Speed Threshold |
| :--- | :--- | :--- | :--- |
| **Normal** 🟢 | `#10B981` | `emerald-500` | Free-flowing, $\ge 80\%$ baseline speed |
| **Moderate** 🟡 | `#F59E0B` | `amber-500` | Moving with slight friction, $50\% - 79\%$ speed |
| **Heavy** 🟠 | `#F97316` | `orange-500` | Significant slowdowns, $25\% - 49\%$ speed |
| **Severe** 🔴 | `#EF4444` | `rose-500` | Crawl / standstill, $< 25\%$ speed, active obstruction |

### 2.3 AI & Predictive Accent Palette
To maintain strict visual separation between **observed reality** and **model predictions**, all AI-generated predictions use a distinct electric palette:

| Token Name | Hex Code | Tailwind Token | Application |
| :--- | :--- | :--- | :--- |
| `ai-primary` | `#6366F1` | `indigo-500` | AI Relief prediction cards, sparkle badges |
| `ai-glow` | `rgba(99, 102, 241, 0.25)` | `indigo-500/25` | Glowing indicator rings for predicted relief |
| `ai-cyan` | `#06B6D4` | `cyan-500` | Confidence interval meter, model version pill |

---

## 3. Typography System

The typography is built around clean modern sans-serif fonts paired with tabular monospaced numbers for precise telemetry readings.

### 3.1 Font Families
- **Primary Interface Font:** `Inter` or `Outfit` (Google Fonts)
  - Geometric, clean, and highly legible across both high-DPI desktop screens and budget smartphone displays.
- **Telemetry & Numbers:** `JetBrains Mono` or `Inter font-mono` with `font-feature-settings: 'tnum'`
  - Used for timestamps (`21:42`), speeds (`14 km/h`), countdowns (`+32 min`), and confidence percentages (`82%`).

### 3.2 Type Scale
| Role | Size | Weight | Example Usage |
| :--- | :--- | :--- | :--- |
| **Display Heading** | 2rem (32px) | Bold (700) | Main App Logo, Major Travel Time |
| **Section Title** | 1.25rem (20px)| SemiBold (600) | "Route Summary", "Incident Diagnostics" |
| **Metric Value** | 1.5rem (24px) | Bold (700) / Mono | `+32 min`, `11 km/h`, `10:20 PM` |
| **Body Primary** | 0.938rem (15px)| Regular (400) | Incident descriptions, road names |
| **Caption / Metadata**| 0.75rem (12px) | Medium (500) | "Reported 14m ago", "Source: MMDA" |

---

## 4. UI/UX Components & Visual Language

### 4.1 The Route Intelligence Card
The centerpiece of SanTrapik. It does not just display time; it diagnoses the journey:

```text
┌─────────────────────────────────────────────────────────────┐
│  ROUTE VIA EDSA                                [ 🔴 SEVERE ]│
│  Estimated: 1h 24m   •   Normal: 52m   •   Delay: +32m      │
├─────────────────────────────────────────────────────────────┤
│  ⚡ WHY IS IT DELAYED?                                      │
│  [ Accident ] 2-vehicle collision at Ortigas Flyover SB     │
│  Reported: 9:42 PM (18 mins ago)  •  Status: Active         │
├─────────────────────────────────────────────────────────────┤
│  ✦ AI CONGESTION RELIEF PREDICTION                          │
│  Expected Relief: 10:20 PM (~38 mins remaining)             │
│  Confidence: 82% [========--]  •  Model v1.0.2              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Observed vs. Predicted Badge Convention
Every data card must make clear whether the information is an **Observed Fact** or an **AI Estimate**:

- **Observed Badge:**
  `[ 🔴 11 km/h · Observed 9:54 PM ]` (Solid Slate background, dot indicator)
- **AI Prediction Badge:**
  `[ ✦ Expected Relief: 10:20 PM (82% conf) ]` (Electric Indigo pill, sparkle icon)

### 4.3 Interactive Map Aesthetics (MapLibre GL JS)
- **Base Tile:** Dark monochrome or muted slate vector tiles (Carto Dark or OSM Dark-styled).
- **Road Arterials:** High-contrast lines colored dynamically according to the semantic traffic palette (`#10B981`, `#F59E0B`, `#F97316`, `#EF4444`).
- **Active Incident Pins:**
  - Car Crash: Red pulsing circle with vehicle collision icon
  - Roadwork: Amber diamond with shovel/cone icon
  - Flooding: Blue-cyan wave icon with water level meter
- **Route Line:** 6px glowing vector line with traffic-colored sub-segments showing the real-time speed of each block.

---

## 5. Mobile-First Commuter UX

Over 70% of traffic checks happen while on the go. SanTrapik must provide:
1. **Zero Login Delay:** The app opens directly to the map and route query bar. Zero welcome carousels, zero sign-up modals.
2. **One-Tap Metro Manila Quick-Routes:**
   Instant shortcuts for major commuter corridors:
   - *QC to Makati*
   - *Manila to BGC*
   - *Caloocan to Pasay*
   - *Alabang to Ortigas*
3. **Adaptive Responsive Layout:**
   - **Mobile:** Full-screen interactive map with an expandable draggable bottom sheet for route intelligence and incident timelines.
   - **Desktop / Tablet:** Split-screen layout — 420px telemetry intelligence panel on the left, full interactive map with heatmap toggle on the right.
4. **Data Freshness Indicator:**
   A discrete pulsing radar dot in the header:
   `🟢 Telemetry Live (Updated 1m ago)`
