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
      <div className="flex items-center justify-between pl-1">
        <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider font-mono">
          Alternative Route Comparison:
        </span>
        <span className="text-[10px] text-ai-cyan font-mono">
          {routes.length} options evaluated
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {routes.map((r) => {
          const isSelected = r.id === selectedRouteId;
          const isRecommended = r.is_recommended;

          return (
            <button
              key={r.id}
              onClick={() => onSelectRoute(r.id)}
              className={`text-left p-2.5 rounded-lg border transition relative font-mono ${
                isSelected
                  ? "bg-surface-card border-ai-primary shadow-[0_0_12px_rgba(99,102,241,0.25)]"
                  : "bg-surface-panel hover:bg-surface-card/80 border-white/10 text-text-secondary"
              }`}
            >
              {isRecommended && (
                <span className="absolute -top-2 right-2 text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 px-1.5 py-0.5 rounded shadow-sm uppercase tracking-wider flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Recommended
                </span>
              )}
              <span className="text-xs font-bold text-text-primary block font-outfit truncate pr-8">
                {r.name}
              </span>
              <div className="flex items-baseline justify-between mt-1 text-xs">
                <span className="text-white font-bold font-mono">{r.summary.estimated_travel_time_min} min</span>
                <span className={`text-[11px] font-semibold ${r.summary.estimated_delay_min > 20 ? "text-traffic-severe" : "text-traffic-heavy"}`}>
                  +{r.summary.estimated_delay_min}m delay
                </span>
              </div>
              <div className="text-[10px] text-text-muted mt-1 flex items-center justify-between">
                <span>{r.summary.total_distance_km} km</span>
                <span className={r.summary.active_incidents_count > 0 ? "text-amber-400" : "text-text-muted"}>
                  {r.summary.active_incidents_count} incident{r.summary.active_incidents_count !== 1 ? "s" : ""}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Show reason justification for the active route */}
      {routes.find((r) => r.id === selectedRouteId)?.recommendation_reason && (
        <div className="text-[11px] p-2 bg-white/5 border border-white/10 rounded font-mono text-text-secondary flex items-start gap-1.5">
          <span className="text-ai-cyan font-bold shrink-0">ℹ</span>
          <span>{routes.find((r) => r.id === selectedRouteId)?.recommendation_reason}</span>
        </div>
      )}
    </div>
  );
};
