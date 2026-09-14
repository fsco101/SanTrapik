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

### Semantic Velocity Spectrum
Chromatic saturation in the traffic spectrum is reserved strictly for real-time velocity states:
- **Normal** ($\ge 80\%$ baseline): `#10B981` (`emerald-500`)
- **Moderate** ($50\% - 79\%$ baseline): `#F59E0B` (`amber-500`)
- **Heavy** ($25\% - 49\%$ baseline): `#F97316` (`orange-500`)
- **Severe** ($< 25\%$ baseline): `#EF4444` (`rose-500`)

### AI Predictive Spectrum
Modeled intelligence is visually insulated from observed sensor readings:
- `ai-primary`: `#6366F1` (Indigo sparkle)
- `ai-cyan`: `#06B6D4` (Cyan confidence bar)
- `ai-glow`: `box-shadow: 0 0 24px rgba(99, 102, 241, 0.20), inset 0 0 0 1px rgba(99, 102, 241, 0.4)`

---

## 2. The Zero-Emoji Directive (Non-Negotiable)

**CRITICAL RULE:** Do NOT use unicode emojis anywhere in the user interface, badges, labels, logs, documentation, or notifications.
- ❌ **Forbidden**: 🚗 Car, 🏍️ Motorcycle, ⚠️ Warning, ⏳ Delay, 🚨 Accident, 🌧️ Rain.
- ✅ **Required**: Clean text tags, monospaced status badges, and Google Material Symbols:
  - `[CAR]` or `<span className="material-symbols-outlined">directions_car</span>`
  - `[MOTORCYCLE]` or `<span className="material-symbols-outlined">two_wheeler</span>`
  - `[RECOMMENDED]` / `[SHORTEST PATH]` / `[LEAST TRAFFIC]`
  - `[SEV-1 SEVERE]` / `[VERIFIED]` / `[AI PREDICTION]`

---

## 3. MapLibre GL JS Performance & Layer Lifecycle

Map instances must never re-render or re-initialize on every React state change. Decouple React state from the MapLibre engine.

### GeoJSON Source Updating (Zero Flicker)
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
    // Initialize source and colored line layers
    map.addSource("route-source", {
      type: "geojson",
      data: routeGeoJson
    });

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

    map.addLayer({
      id: "route-line",
      type: "line",
      source: "route-source",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": ["get", "color"], // Dynamic traffic segment color
        "line-width": 5
      }
    });
  }
}
```

---

## 4. Responsive Viewport Architecture

```text
DESKTOP (>= 1024px): Split Dual-Tier Console
┌────────────────────────────┬────────────────────────────────────────────────────────┐
│  Sidebar Telemetry Rail    │  Interactive 100vh MapLibre Canvas                    │
│  Width: 420px              │                                                        │
│  - Waypoint Query Form     │  - Real-Time Traffic Vector Lines                      │
│  - Route Intelligence Card │  - Snapped Incident Beacons                            │
│  - Comparison Alternatives │  - Pulsing Radar Warnings                              │
│  - AI Relief Forecast Bar  │                                                        │
└────────────────────────────┴────────────────────────────────────────────────────────┘

MOBILE (< 768px): Elastic Bottom Telemetry Sheet
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  Floating Origin / Destination Pill Bar (Anchored Top-Safe Area)                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  Full-Bleed Map Canvas                                                              │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ▲ Swipe Up: Elastic Telemetry Sheet (Route Intelligence & Forecast)                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Segment Velocity Bar Component Standard

The `SegmentVelocityBar` visualizes the health of each road segment along a chosen route.
- Each block's width represents its relative distance fraction: $\frac{d_i}{\sum d}$.
- Color strictly maps to segment traffic condition (`#10B981`, `#F59E0B`, `#F97316`, `#EF4444`).
- Hover/tap must trigger a high-contrast micro-tooltip with exact telemetry (e.g. `Guadalupe to Buendia: 8.2 km/h (84% Congestion)`).

---

## 6. Frontend Quality & Design Checklist

1. [ ] **Fidelity to `DESIGN/`**: Verify components match `DESIGN/DESIGN.md` and `DESIGN/code.html`.
2. [ ] **No Unicode Emojis**: Verify search across `frontend/src/` returns 0 occurrences of emojis.
3. [ ] **Zero Map Destruction**: MapLibre canvas container must never re-mount when swapping corridors or routes.
4. [ ] **Build Verification**: `npm run build` passes with zero TypeScript warnings or errors (`tsc -b`).
5. [ ] **Monospaced Numbers**: All speed numbers, times, and coordinates use `JetBrains Mono` or `font-mono`.
