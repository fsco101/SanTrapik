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

  const renderBadge = (route: RouteItem) => {
    switch (route.badge) {
      case "LEAST_TRAFFIC_AND_SHORTEST":
        return (
          <span className="text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 px-1.5 py-0.5 rounded shadow-sm uppercase tracking-wider font-mono">
            [LEAST TRAFFIC & SHORTEST]
          </span>
        );
      case "LEAST_TRAFFIC":
        return (
          <span className="text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-1.5 py-0.5 rounded shadow-sm uppercase tracking-wider font-mono">
            [LEAST TRAFFIC]
          </span>
        );
      case "SHORTEST_PATH":
        return (
          <span className="text-[9px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 px-1.5 py-0.5 rounded shadow-sm uppercase tracking-wider font-mono">
            [SHORTEST PATH]
          </span>
        );
      case "ALTERNATIVE":
        return (
          <span className="text-[9px] font-bold bg-slate-700/50 text-slate-300 border border-slate-600 px-1.5 py-0.5 rounded shadow-sm uppercase tracking-wider font-mono">
            [ALTERNATIVE]
          </span>
        );
      default:
        if (route.is_recommended) {
          return (
            <span className="text-[9px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 px-1.5 py-0.5 rounded shadow-sm uppercase tracking-wider font-mono">
              [RECOMMENDED]
            </span>
          );
        }
        return null;
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between pl-1">
        <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider font-mono">
          Route Optimization Comparison:
        </span>
        <span className="text-[10px] text-ai-cyan font-mono font-semibold">
          {routes.length} options evaluated
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {routes.map((r) => {
          const isSelected = r.id === selectedRouteId;

          return (
            <button
              key={r.id}
              onClick={() => onSelectRoute(r.id)}
              className={`text-left p-2.5 rounded-lg border transition relative font-mono cursor-pointer ${
                isSelected
                  ? "bg-surface-card border-ai-primary shadow-[0_0_14px_rgba(99,102,241,0.3)] ring-1 ring-ai-primary"
                  : "bg-surface-panel hover:bg-surface-card/80 border-white/10 text-text-secondary"
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1.5">
                <span className="text-xs font-bold text-text-primary font-outfit truncate">
                  {r.name}
                </span>
                {renderBadge(r)}
              </div>

              <div className="flex items-baseline justify-between mt-1 text-xs">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-white font-bold font-mono text-sm">
                    {r.summary.estimated_travel_time_min} min
                  </span>
                  {r.time_diff_min !== undefined && r.time_diff_min > 0 ? (
                    <span className="text-[10px] text-traffic-heavy font-mono">
                      (+{r.time_diff_min}m)
                    </span>
                  ) : r.time_diff_min === 0 ? (
                    <span className="text-[10px] text-emerald-400 font-mono font-semibold">
                      (Fastest)
                    </span>
                  ) : null}
                </div>
                <span
                  className={`text-[11px] font-semibold ${
                    r.summary.estimated_delay_min > 20
                      ? "text-traffic-severe"
                      : "text-traffic-heavy"
                  }`}
                >
                  +{r.summary.estimated_delay_min}m delay
                </span>
              </div>

              <div className="text-[10px] text-text-muted mt-1.5 flex items-center justify-between border-t border-white/5 pt-1.5">
                <span className="flex items-center gap-1">
                  <span className="text-slate-300 font-medium">{r.summary.total_distance_km} km</span>
                  {r.distance_diff_km !== undefined && r.distance_diff_km > 0 ? (
                    <span className="text-slate-500">(+{r.distance_diff_km} km)</span>
                  ) : r.distance_diff_km === 0 ? (
                    <span className="text-cyan-400 font-semibold">(Shortest)</span>
                  ) : null}
                </span>
                <span
                  className={
                    r.summary.active_incidents_count > 0
                      ? "text-amber-400 font-semibold"
                      : "text-text-muted"
                  }
                >
                  {r.summary.active_incidents_count} incident
                  {r.summary.active_incidents_count !== 1 ? "s" : ""}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Show reason justification for the active route */}
      {routes.find((r) => r.id === selectedRouteId)?.recommendation_reason && (
        <div className="text-[11px] p-2 bg-white/5 border border-white/10 rounded font-mono text-text-secondary flex items-start gap-1.5">
          <span className="material-symbols-outlined text-[15px] text-ai-cyan shrink-0 mt-0.5">
            info
          </span>
          <span className="leading-snug">
            {routes.find((r) => r.id === selectedRouteId)?.recommendation_reason}
          </span>
        </div>
      )}
    </div>
  );
};
