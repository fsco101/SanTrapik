import React from "react";
import type { RouteItem } from "../../types/traffic";

interface RouteComparisonProps {
  routes: RouteItem[];
  selectedRouteId: string;
  onSelectRoute: (id: string) => void;
}

export const RouteComparison: React.FC<RouteComparisonProps> = ({
  routes,
  selectedRouteId,
  onSelectRoute,
}) => {
  if (routes.length <= 1) return null;

  return (
    <div className="space-y-2">
      <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider font-mono block pl-1">
        Alternative Route Comparison:
      </span>
      <div className="grid grid-cols-2 gap-2">
        {routes.map((r) => {
          const isSelected = r.id === selectedRouteId;
          const isRecommended = r.is_recommended;

          return (
            <button
              key={r.id}
              onClick={() => onSelectRoute(r.id)}
              className={`text-left p-2.5 rounded border transition relative font-mono ${
                isSelected
                  ? "bg-surface-card border-ai-primary shadow-ai-aura"
                  : "bg-surface-panel hover:bg-surface-card border-white/10 text-text-secondary"
              }`}
            >
              {isRecommended && (
                <span className="absolute -top-2 right-2 text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-1.5 py-0.2 rounded uppercase">
                  Recommended
                </span>
              )}
              <span className="text-xs font-bold text-text-primary block font-outfit truncate">
                {r.name}
              </span>
              <div className="flex items-baseline justify-between mt-1 text-xs">
                <span className="text-white font-bold">{r.summary.estimated_travel_time_min}m</span>
                <span className={`text-[11px] font-semibold ${r.summary.estimated_delay_min > 20 ? "text-traffic-severe" : "text-traffic-heavy"}`}>
                  +{r.summary.estimated_delay_min}m delay
                </span>
              </div>
              <div className="text-[10px] text-text-muted mt-0.5 flex items-center justify-between">
                <span>{r.summary.total_distance_km} km</span>
                <span>{r.summary.active_incidents_count} incidents</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
