import React, { useState } from "react";
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
  const [filterMode, setFilterMode] = useState<"ALL" | "ZERO_TOLL" | "FASTEST">("ALL");

  if (routes.length <= 1) return null;

  const filteredRoutes = routes.filter((r) => {
    if (filterMode === "ZERO_TOLL") {
      return (r.toll_fee_php || 0) === 0;
    }
    if (filterMode === "FASTEST") {
      const minTime = Math.min(...routes.map((x) => x.summary.estimated_travel_time_min));
      return r.summary.estimated_travel_time_min === minTime;
    }
    return true;
  });

  const displayRoutes = filteredRoutes.length > 0 ? filteredRoutes : routes;

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

  const activeRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];

  return (
    <div className="space-y-2">
      {/* Route Filter Tabs */}
      <div className="flex items-center justify-between pl-1">
        <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider font-mono">
          Route Intelligence Options
        </span>
        <div className="flex items-center gap-1 font-mono">
          <button
            type="button"
            onClick={() => setFilterMode("ALL")}
            className={`px-2 py-0.5 text-[9px] rounded font-semibold transition ${
              filterMode === "ALL"
                ? "bg-ai-primary text-white"
                : "bg-surface-elevated/60 text-text-muted hover:text-white"
            }`}
          >
            [ALL]
          </button>
          <button
            type="button"
            onClick={() => setFilterMode("ZERO_TOLL")}
            className={`px-2 py-0.5 text-[9px] rounded font-semibold transition ${
              filterMode === "ZERO_TOLL"
                ? "bg-emerald-600 text-white"
                : "bg-surface-elevated/60 text-text-muted hover:text-white"
            }`}
          >
            [ZERO TOLL]
          </button>
          <button
            type="button"
            onClick={() => setFilterMode("FASTEST")}
            className={`px-2 py-0.5 text-[9px] rounded font-semibold transition ${
              filterMode === "FASTEST"
                ? "bg-indigo-600 text-white"
                : "bg-surface-elevated/60 text-text-muted hover:text-white"
            }`}
          >
            [FASTEST]
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {displayRoutes.map((r) => {
          const isSelected = r.id === selectedRouteId;
          const tollFee = r.toll_fee_php || 0;
          const isZeroToll = tollFee === 0;
          const cb = r.toll_cost_benefit;

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
              {/* Header: Name and Badges */}
              <div className="flex items-center justify-between gap-1 mb-1.5 flex-wrap">
                <span className="text-xs font-bold text-text-primary font-outfit truncate max-w-[140px]">
                  {r.name}
                </span>
                <div className="flex items-center gap-1">
                  {renderBadge(r)}
                  {isZeroToll ? (
                    <span className="text-[9px] font-mono font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 px-1 py-0.5 rounded">
                      [ZERO TOLL]
                    </span>
                  ) : (
                    <span className="text-[9px] font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30 px-1 py-0.5 rounded">
                      [TOLL: PHP {Math.round(tollFee)}]
                    </span>
                  )}
                </div>
              </div>

              {/* Flood & Coding Status Alerts */}
              <div className="flex items-center gap-1 mb-1.5 flex-wrap">
                {r.is_impassable_flood && (
                  <span className="text-[9px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 px-1 py-0.2 rounded">
                    [IMPASSABLE FLOOD]
                  </span>
                )}
                {r.coding_advisory?.is_restricted && (
                  <span className="text-[9px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 px-1 py-0.2 rounded">
                    [CODING RESTRICTED]
                  </span>
                )}
              </div>

              {/* Time and Delay */}
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

              {/* Toll Cost-Benefit Telemetry Metric */}
              {cb && cb.cost_per_min_saved !== undefined && cb.cost_per_min_saved !== null && cb.time_saved_min > 0 && (
                <div className="text-[9px] font-mono text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded px-1.5 py-0.5 mt-1.5">
                  Saves {cb.time_saved_min}m for PHP {Math.round(cb.toll_fee_php)} (PHP {cb.cost_per_min_saved}/min saved)
                </div>
              )}

              {/* Distance and Incidents */}
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
      {activeRoute?.recommendation_reason && (
        <div className="text-[11px] p-2 bg-white/5 border border-white/10 rounded font-mono text-text-secondary flex items-start gap-1.5">
          <span className="material-symbols-outlined text-[15px] text-ai-cyan shrink-0 mt-0.5">
            info
          </span>
          <span className="leading-snug">
            {activeRoute.recommendation_reason}
          </span>
        </div>
      )}
    </div>
  );
};
