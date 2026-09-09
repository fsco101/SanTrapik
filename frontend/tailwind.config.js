/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base Obsidian Canvas & Structural Surfaces
        "surface-bg": "#080C14",
        "surface-panel": "#0F172A",
        "surface-card": "#1E293B",
        "surface-elevated": "#334155",
        "border-subtle": "rgba(255, 255, 255, 0.08)",

        // Semantic Traffic Telemetry Signals
        "traffic-normal": "#10B981",
        "traffic-moderate": "#F59E0B",
        "traffic-heavy": "#F97316",
        "traffic-severe": "#EF4444",

        // AI & Predictive Intelligence
        "ai-primary": "#6366F1",
        "ai-glow": "rgba(99, 102, 241, 0.25)",
        "ai-cyan": "#06B6D4",

        // Text & Hierarchy
        "text-primary": "#F8FAFC",
        "text-secondary": "#94A3B8",
        "text-muted": "#64748B",

        // Accent & container tokens from DESIGN/DESIGN.md
        "surface-dim": "#0f131c",
        "surface-bright": "#353942",
        "primary-container": "#8083ff",
        "secondary-container": "#03b5d3",
        "tertiary-container": "#00885d"
      },
      fontFamily: {
        outfit: ["Outfit", "sans-serif"],
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"]
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px"
      },
      spacing: {
        "sidebar-width": "26.25rem",
        "sheet-collapsed-height": "4.5rem",
        "panel-gap": "0.75rem"
      },
      boxShadow: {
        "ai-aura": "0 0 24px rgba(99, 102, 241, 0.20), inset 0 0 0 1px rgba(99, 102, 241, 0.4)",
        "alert-glow": "0 0 16px rgba(239, 68, 68, 0.25)",
        "active-glow": "0 0 16px rgba(99, 102, 241, 0.35)"
      }
    },
  },
  plugins: [],
}
