---
name: obsidian-telemetry-ui
description: Use when building, modifying, or reviewing frontend components, MapLibre GL map layers, telemetry cards, and responsive layouts conforming to the Obsidian Telemetry design system
---

# Obsidian Telemetry UI & Frontend Engineering

## Overview
SanTrapik's frontend implements the **Obsidian Telemetry** design system: an avionics-inspired, mission-critical dark mode aesthetic tuned for tactical clarity during high-stress commutes. 

The frontend source of truth is strictly governed by `DESIGN/DESIGN.md` and `DESIGN/code.html`. This skill provides the component architecture rules, MapLibre GL JS performance patterns, strict color tokens, and layout guidelines.

---

## 1. The Obsidian Telemetry Design Tokens

### Structural Surfaces
- `surface-bg`: `#080C14` (Deep canvas, suppresses OLED glare)
- `surface-panel`: `#0F172A` (Sidebar rails, persistent modals, navigation bars)
- `surface-card`: `#1E293B` (Telemetry containers, route segment rows, incident cards)
- `border-subtle`: `rgba(255, 255, 255, 0.08)` (Ghost dividers without visual clutter)

### Semantic Velocity & Commuter Spectrum
Chromatic saturation in the traffic spectrum is reserved strictly for real-time velocity states and route congestion:
- **Normal / Low Congestion** ($\ge 80\%$ baseline): `#10B981` (`emerald-500`)
- **Moderate Congestion** ($50\% - 79\%$ baseline): `#F59E0B` (`amber-500`)
- **Heavy Congestion** ($25\% - 49\%$ baseline): `#F97316` (`orange-500`)
- **Severe / Gridlock** ($< 25\%$ baseline): `#EF4444` (`rose-500`)

### Commuter & Pedestrian Path Tokens
- `path-pedestrian`: `#38BDF8` (`sky-400`, dashed overlay for walking segments)
- `path-transit`: `#818CF8` (`indigo-400`, highlighted corridor line for public transit / busway)
- `badge-walkable`: `bg-emerald-950/80 text-emerald-400 border-emerald-800/50`
- `badge-impassable`: `bg-rose-950/80 text-rose-400 border-rose-800/50`
- `badge-transfer`: `bg-sky-950/80 text-sky-300 border-sky-800/50`

### AI Predictive Spectrum
Modeled intelligence is visually insulated from observed sensor readings:
- `ai-primary`: `#6366F1` (Indigo sparkle)
- `ai-cyan`: `#06B6D4` (Cyan confidence bar)
- `ai-glow`: `box-shadow: 0 0 24px rgba(99, 102, 241, 0.20), inset 0 0 0 1px rgba(99, 102, 241, 0.4)`

---

## 2. The Zero-Emoji Directive (Non-Negotiable)

**CRITICAL RULE:** Do NOT use unicode emojis anywhere in the user interface, badges, labels, logs, documentation, or notifications.
- ❌ **Forbidden**: 🚗 Car, 🏍️ Motorcycle, 🚶 Pedestrian, 🚌 Bus, ⚠️ Warning, ⏳ Delay, 🚨 Accident, 🌧️ Rain.
- ✅ **Required**: Clean text tags, monospaced status badges, and Google Material Symbols:
  - `[CAR]` or `<span className="material-symbols-outlined">directions_car</span>`
  - `[MOTORCYCLE]` or `<span className="material-symbols-outlined">two_wheeler</span>`
  - `[COMMUTER]` or `<span className="material-symbols-outlined">directions_bus</span>`
  - `[WALKING]` or `<span className="material-symbols-outlined">directions_walk</span>`
  - `[TRANSFER]` or `<span className="material-symbols-outlined">transfer_within_a_station</span>`
  - `[LOW CONGESTION]` / `[MODERATE CONGESTION]` / `[HEAVY CONGESTION]` / `[GRIDLOCK]`
  - `[WALKABLE]` / `[FLOOD RISK - IMPASSABLE]` / `[FOOTBRIDGE ACCESS]` / `[HIGH TRAFFIC CROSSING]`
  - `[RECOMMENDED]` / `[SHORTEST PATH]` / `[LEAST TRAFFIC]`
  - `[SEV-1 SEVERE]` / `[VERIFIED]` / `[AI PREDICTION]`

---

## 3. MapLibre GL JS Performance & Multi-Modal Layer Lifecycle

Map instances must never re-render or re-initialize on every React state change. Decouple React state from the MapLibre engine.

### Multi-Modal Route Rendering (Walking Legs vs. Transit Corridors)
When rendering a commuter journey with pedestrian segments:
- **Vehicular & Transit segments**: Solid line colored dynamically by congestion level (`#10B981`, `#F59E0B`, `#F97316`, `#EF4444`).
- **Pedestrian walking segments**: Tactical dashed line (`line-dasharray: [2, 2]`) with cyan/sky coloring (`#38BDF8`) to immediately communicate walkability.

```typescript
// frontend/src/components/map/useMapRouteLayer.ts
import { useEffect } from "react";
import type { Map, GeoJSONSource } from "maplibre-gl";

export function updateMapRoute(map: Map | null, routeGeoJson: GeoJSON.FeatureCollection) {
  if (!map || !map.isStyleLoaded()) return;

  const source = map.getSource("route-source") as GeoJSONSource | undefined;
  if (source) {
    // In-place memory buffer update - NO map tear-down or flicker
    source.setData(routeGeoJson);
  } else {
    map.addSource("route-source", {
      type: "geojson",
      data: routeGeoJson
    });

    // Dark casing for tactical contrast
    map.addLayer({
      id: "route-casing",
      type: "line",
      source: "route-source",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": "#000000",
        "line-width": 8,
        "line-opacity": 0.6
      }
    });

    // Solid line for motorized/transit corridor segments
    map.addLayer({
      id: "route-line",
      type: "line",
      source: "route-source",
      filter: ["!=", ["get", "mode"], "walking"],
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": ["get", "color"], // Dynamic traffic segment color
        "line-width": 5
      }
    });

    // Dashed line for pedestrian walking legs
    map.addLayer({
      id: "route-walking-line",
      type: "line",
      source: "route-source",
      filter: ["==", ["get", "mode"], "walking"],
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": "#38BDF8", // Cyan/sky for pedestrian leg
        "line-width": 4,
        "line-dasharray": [2, 2]
      }
    });
  }
}
```

---

## 4. Responsive Viewport Architecture & Commuter Console

```text
DESKTOP (>= 1024px): Split Dual-Tier Commuter Console
┌────────────────────────────┬────────────────────────────────────────────────────────┐
│  Sidebar Telemetry Rail    │  Interactive 100vh MapLibre Canvas                    │
│  Width: 420px              │                                                        │
│  - Commuter Waypoint Query │  - Real-Time Traffic Vector Lines (Transit & Walk)     │
│  - Multi-Modal Route Card  │  - Snapped Incident & Hazard Beacons                   │
│  - Segment Velocity Bar    │  - Footbridge & Station Transfer Nodes                 │
│  - AI Relief Forecast Bar  │  - Pulsing Chokepoint Alerts                           │
└────────────────────────────┴────────────────────────────────────────────────────────┘

MOBILE (< 768px): Elastic Bottom Commuter Sheet
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  Floating Origin / Destination Pill Bar (Commuter Hubs & Stops)                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Full-Bleed Map Canvas with Walk/Transit Path Layers                                │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ▲ Swipe Up: Elastic Telemetry Sheet (Congestion Level, Walk Time, Forecast)        │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Segment Velocity Bar & Commuter Telemetry Standard

The `SegmentVelocityBar` visualizes the health of each segment along the commuter's journey:
- **Relative Distance Width**: Each block's width represents its relative distance fraction: $\frac{d_i}{\sum d}$.
- **Distinct Walking Blocks**: Walking legs use a diagonal hashed or cyan pattern to distinguish walking effort from motorized delay.
- **Congestion Spectrum**: Motorized/transit blocks strictly map to segment traffic condition (`#10B981`, `#F59E0B`, `#F97316`, `#EF4444`).
- **Interactive Tooltip**: Hover/tap triggers a high-contrast micro-tooltip:
  - *Walking segment*: `Guadalupe Station to EDSA Footbridge: 420m (5 mins) [WALKABLE]`
  - *Transit segment*: `Guadalupe to Buendia Busway: 8.2 km/h (84% Congestion) [HEAVY CONGESTION]`

---

## 6. Frontend Quality & Design Checklist

1. [ ] **Fidelity to `DESIGN/`**: Verify components match `DESIGN/DESIGN.md` and `DESIGN/code.html`.
2. [ ] **No Unicode Emojis**: Verify search across `frontend/src/` returns 0 occurrences of emojis.
3. [ ] **Commuter Congestion Clarity**: Verify route cards explicitly display congestion level (`[LOW CONGESTION]`, `[MODERATE]`, `[HEAVY]`, `[GRIDLOCK]`).
4. [ ] **Pedestrian Path Differentiation**: Verify walking legs are visually distinct (dashed line) from motorized transit segments.
5. [ ] **Zero Map Destruction**: MapLibre canvas container must never re-mount when swapping corridors or routes.
6. [ ] **Build Verification**: `npm run build` passes with zero TypeScript warnings or errors (`tsc -b`).
7. [ ] **Monospaced Numbers**: All speed numbers, times, and coordinates use `JetBrains Mono` or `font-mono`.
