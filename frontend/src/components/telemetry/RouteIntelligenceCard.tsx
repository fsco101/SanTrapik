import React, { useState } from "react";
import type { RouteItem } from "../../types/traffic";
import { voteClearance } from "../../services/api";

interface RouteIntelligenceCardProps {
  route: RouteItem;
  onSelectIncident?: (incident: any) => void;
}

export const RouteIntelligenceCard: React.FC<RouteIntelligenceCardProps> = ({ route, onSelectIncident }) => {
  const [incidentsOpen, setIncidentsOpen] = useState(true);
  const [prognosisOpen, setPrognosisOpen] = useState(false);
  const [hoveredSegment, setHoveredSegment] = useState<string | null>(null);
  const [departureOffset, setDepartureOffset] = useState<number>(0);

  const { summary, expected_relief, segments } = route;

  // SP9-005: AI Prognosis Horizon calculations
  const projectedTravelTime = departureOffset === 0
    ? summary.estimated_travel_time_min
    : Math.max(
        summary.normal_travel_time_min,
        Math.round(summary.estimated_travel_time_min - (departureOffset * 0.22))
      );
  const projectedDelay = Math.max(0, projectedTravelTime - summary.normal_travel_time_min);

  // Format hours and minutes
  const formatTime = (minutes: number) => {
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hrs > 0) return `${hrs}h ${mins}m`;
    return `${mins}m`;
  };

  const getSeverityStyle = (level: string) => {
    switch (level) {
      case "SEVERE":
        return { badge: "bg-rose-500/20 text-rose-400 border-rose-500/40", text: "text-traffic-severe" };
      case "HEAVY":
        return { badge: "bg-orange-500/20 text-orange-400 border-orange-500/40", text: "text-traffic-heavy" };
      case "MODERATE":
        return { badge: "bg-amber-500/20 text-amber-400 border-amber-500/40", text: "text-traffic-moderate" };
      default:
        return { badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40", text: "text-traffic-normal" };
    }
  };

  const sevStyle = getSeverityStyle(summary.overall_congestion);

  // Format reported time
  const formatReportedTime = (timeStr: string) => {
    if (!timeStr) return "";
    if (timeStr.includes("T")) {
      try {
        return new Date(timeStr).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
      } catch {
        return timeStr;
      }
    }
    return timeStr;
  };

  // Deduplicate incidents across all traversed segments
  const uniqueIncidents = React.useMemo(() => {
    const incidentMap = new Map<
      string,
      {
        id: string;
        type: string;
        severity: string;
        description?: string;
        reported_at: string;
        status: string;
        data_source?: string;
        affectedSegments: string[];
        clearance_minutes?: number;
        p10_clearance_mins?: number;
        p50_clearance_mins?: number;
        p90_clearance_mins?: number;
        clearance_window_display?: string;
        confidence_score?: number;
        tow_dispatch_status?: string;
        lanes_blocked?: number;
        road_width_lanes?: number;
      }
    >();

    segments.forEach((s) => {
      (s.incidents || []).forEach((inc) => {
        const key = inc.id || `${inc.type}-${inc.description}`;
        if (!incidentMap.has(key)) {
          incidentMap.set(key, {
            ...inc,
            data_source: (inc as any).data_source || "LIVE_TELEMETRY",
            affectedSegments: s.name ? [s.name] : [],
          });
        } else {
          const existing = incidentMap.get(key)!;
          if (s.name && !existing.affectedSegments.includes(s.name)) {
            existing.affectedSegments.push(s.name);
          }
        }
      });
    });

    return Array.from(incidentMap.values());
  }, [segments]);

  return (
    <div className="bg-surface-panel rounded-lg border border-white/10 overflow-hidden shadow-lg space-y-3.5 p-4">
      {/* 1. Header with Route Title & Live Severity Badge */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="text-[11px] uppercase font-bold text-text-muted tracking-wider font-mono block">
            Corridor Intelligence & Telemetry
          </span>
          <h2 className="font-outfit font-bold text-lg text-white tracking-tight mt-0.5">
            {route.name}
          </h2>
        </div>
        <div className={`px-2.5 py-1 rounded text-xs font-mono font-bold uppercase tracking-wider border flex items-center gap-1.5 shrink-0 ${sevStyle.badge}`}>
          <span className="w-2 h-2 rounded-full bg-current animate-pulse"></span>
          <span>{summary.overall_congestion}</span>
        </div>
      </div>

      {/* 2. Primary Commute Metric Cluster: Estimated vs Normal vs Net Delay */}
      <div className="grid grid-cols-3 gap-2.5 bg-surface-card rounded-lg p-3.5 border border-white/5 font-mono">
        <div>
          <span className="text-[10px] uppercase text-text-muted font-bold block tracking-wider">
            {departureOffset > 0 ? `Forecast (+${departureOffset}m)` : "Estimated ETA"}
          </span>
          <span className="text-2xl font-bold text-white tracking-tight">
            {formatTime(projectedTravelTime)}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-text-muted font-bold block tracking-wider">
            Normal (Free-flow)
          </span>
          <span className="text-xl font-bold text-text-secondary">
            {formatTime(summary.normal_travel_time_min)}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-text-muted font-bold block tracking-wider">
            Net Congestion
          </span>
          <span className={`text-xl font-bold ${projectedDelay > 0 ? sevStyle.text : "text-traffic-normal"}`}>
            {projectedDelay > 0 ? `+${projectedDelay}m` : "On Time"}
          </span>
        </div>
      </div>

      {/* 2.1 Multi-Modal Telemetry Bar: Toll Economics & Coding Advisory */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs font-mono">
        {/* Toll Economics Card */}
        <div className="bg-surface-card border border-white/5 rounded-lg p-3 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase text-text-muted font-bold flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-amber-400">toll</span>
              Expressway Toll
            </span>
            {(route.toll_fee_php || 0) > 0 ? (
              <span className="text-[11px] font-bold text-amber-300 bg-amber-500/15 px-2 py-0.5 rounded border border-amber-500/30">
                PHP {Math.round(route.toll_fee_php || 0)}
              </span>
            ) : (
              <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30">
                ZERO TOLL
              </span>
            )}
          </div>
          {route.toll_cost_benefit?.cost_per_min_saved !== undefined &&
          route.toll_cost_benefit.cost_per_min_saved !== null &&
          route.toll_cost_benefit.time_saved_min > 0 ? (
            <p className="text-xs text-amber-200 leading-snug">
              Saves {route.toll_cost_benefit.time_saved_min}m vs surface road (PHP {route.toll_cost_benefit.cost_per_min_saved}/min saved)
            </p>
          ) : (
            <p className="text-xs text-text-muted leading-snug">
              {(route.toll_fee_php || 0) === 0 ? "Public arterial road (no toll charges)." : "Expressway transit corridor."}
            </p>
          )}
        </div>

        {/* Number Coding Advisory Card */}
        <div className="bg-surface-card border border-white/5 rounded-lg p-3 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase text-text-muted font-bold flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-indigo-400">pin</span>
              MMDA UVVRP Coding
            </span>
            {route.coding_advisory?.is_restricted ? (
              <span className="text-[11px] font-bold text-rose-300 bg-rose-500/20 px-2 py-0.5 rounded border border-rose-500/30">
                RESTRICTED
              </span>
            ) : route.coding_advisory?.is_coding_active ? (
              <span className="text-[11px] font-bold text-amber-300 bg-amber-500/15 px-2 py-0.5 rounded border border-amber-500/30">
                ENFORCED
              </span>
            ) : (
              <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30">
                CLEAR / EXEMPT
              </span>
            )}
          </div>
          <p className="text-xs text-text-secondary leading-snug truncate" title={route.coding_advisory?.message}>
            {route.coding_advisory?.message || "No UVVRP restriction active for this route."}
          </p>
        </div>
      </div>

      {/* 2.2 AI Congestion Relief Prediction (SP9-002 Quantile Envelopes) */}
      <div className="rounded-lg border border-indigo-500/30 bg-indigo-950/30 p-3.5 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[17px] text-ai-cyan">auto_awesome</span>
            <span className="text-xs font-bold font-outfit text-white tracking-wide">
              AI Congestion Relief Prediction
            </span>
          </div>
          <span className="text-[10px] font-mono font-semibold text-ai-cyan bg-indigo-900/60 px-2 py-0.5 rounded border border-indigo-500/30">
            {expected_relief.model_version || "v1.4-rt-gbr"}
          </span>
        </div>

        <div className="flex items-baseline justify-between font-mono">
          <div>
            <span className="text-[10px] uppercase text-text-muted font-bold block tracking-wider">
              Expected Relief Time:
            </span>
            <span className="text-xl font-bold text-white tracking-tight">
              {expected_relief.relief_time}
            </span>
            <span className="text-sm text-ai-cyan ml-2 font-bold">
              ({expected_relief.relief_window_display || `~${expected_relief.estimated_minutes_remaining}m`})
            </span>
          </div>
          <div className="text-right">
            <span className="text-[10px] uppercase text-text-muted font-bold block tracking-wider">
              Model Confidence
            </span>
            <span className="text-sm font-bold text-ai-cyan">
              {Math.round(expected_relief.confidence * 100)}%
            </span>
          </div>
        </div>

        {/* Quantile Bounds Breakdown (P10 / P50 / P90) */}
        {expected_relief.p10_optimistic_mins !== undefined && (
          <div className="grid grid-cols-3 gap-1.5 text-center font-mono text-xs bg-black/40 p-2 rounded border border-white/5">
            <div>
              <span className="text-emerald-400 block text-[10px] font-bold">P10 OPTIMISTIC</span>
              <span className="text-white font-semibold">~{expected_relief.p10_optimistic_mins}m</span>
            </div>
            <div className="border-x border-white/10">
              <span className="text-ai-cyan block text-[10px] font-bold">P50 MEDIAN</span>
              <span className="text-white font-semibold">~{expected_relief.p50_median_mins}m</span>
            </div>
            <div>
              <span className="text-rose-400 block text-[10px] font-bold">P90 MAX DELAY</span>
              <span className="text-white font-semibold">~{expected_relief.p90_pessimistic_mins}m</span>
            </div>
          </div>
        )}

        {/* Linear Confidence Bar */}
        <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden border border-white/5">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full transition-all duration-500"
            style={{ width: `${Math.round(expected_relief.confidence * 100)}%` }}
          />
        </div>
      </div>

      {/* 2.3 Departure Horizon Scrubber (SP9-005) */}
      <div className="bg-surface-card rounded-lg border border-indigo-500/25 overflow-hidden">
        <button
          type="button"
          onClick={() => setPrognosisOpen(!prognosisOpen)}
          className="w-full px-3.5 py-2.5 flex items-center justify-between text-xs font-mono bg-indigo-950/20 hover:bg-indigo-950/40 transition cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-ai-cyan text-[17px]">schedule</span>
            <span className="text-text-primary uppercase text-xs font-bold tracking-wider">
              Departure Horizon Scrubber
            </span>
          </div>
          <div className="flex items-center gap-2">
            {departureOffset > 0 ? (
              <span className="text-[10px] font-mono font-bold bg-ai-primary/20 text-ai-cyan border border-ai-cyan/40 px-2 py-0.5 rounded">
                +{departureOffset}m FORECAST
              </span>
            ) : (
              <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                NOW (0m)
              </span>
            )}
            <span className="material-symbols-outlined text-text-muted text-[16px]">
              {prognosisOpen ? "expand_less" : "expand_more"}
            </span>
          </div>
        </button>

        {prognosisOpen && (
          <div className="p-3.5 pt-2 space-y-2 border-t border-indigo-500/20">
            <div className="space-y-2 font-mono">
              <input
                type="range"
                min="0"
                max="60"
                step="15"
                value={departureOffset}
                onChange={(e) => setDepartureOffset(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-ai-cyan"
              />
              <div className="flex justify-between text-xs text-text-muted">
                <span className={departureOffset === 0 ? "text-ai-cyan font-bold" : ""}>+0m (Now)</span>
                <span className={departureOffset === 15 ? "text-ai-cyan font-bold" : ""}>+15m</span>
                <span className={departureOffset === 30 ? "text-ai-cyan font-bold" : ""}>+30m</span>
                <span className={departureOffset === 45 ? "text-ai-cyan font-bold" : ""}>+45m</span>
                <span className={departureOffset === 60 ? "text-ai-cyan font-bold" : ""}>+60m</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 2.4 Spatiotemporal Bottleneck Spillover Warning (SP9-003) */}
      {route.spillover_warnings && route.spillover_warnings.length > 0 && (
        <div className="p-3 rounded-lg border border-amber-500/40 bg-amber-950/20 space-y-1.5 font-mono">
          <div className="flex items-center gap-2 text-amber-400 font-bold text-xs">
            <span className="material-symbols-outlined text-[17px] animate-pulse">crisis_alert</span>
            <span>Spatiotemporal Queue Spillover Warning</span>
          </div>
          {route.spillover_warnings.map((warn, idx) => (
            <p key={idx} className="text-xs text-amber-200/90 leading-snug">
              • {warn}
            </p>
          ))}
        </div>
      )}

      {/* 2.5 Monsoon & Flood Hazard Geo-Integration Alert */}
      {route.flood_hazards && route.flood_hazards.length > 0 && (
        <div className="p-3 rounded-lg border border-rose-500/40 bg-rose-950/20 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-rose-400 font-mono font-bold text-xs">
              <span className="material-symbols-outlined text-[17px]">flood</span>
              <span>Monsoon Flood Hazard Warning</span>
            </div>
            {route.is_impassable_flood ? (
              <span className="text-[10px] font-mono font-bold bg-rose-500 text-white px-2 py-0.5 rounded">
                IMPASSABLE
              </span>
            ) : (
              <span className="text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded">
                CAUTION
              </span>
            )}
          </div>
          {route.flood_hazards.map((fld) => (
            <div key={fld.id} className="text-xs font-mono bg-black/30 p-2 rounded border border-rose-500/20 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-white">{fld.corridor} ({fld.city})</span>
                <span className="text-amber-400 font-bold uppercase">{fld.water_depth.replace("_", " ")}</span>
              </div>
              <p className="text-xs text-slate-300 font-sans">{fld.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* 3. Delay Decomposition & Velocity Profile (Always Viewable) */}
      <div className="bg-surface-card border border-white/5 rounded-lg p-3.5 space-y-3">
        {/* Delay Decomposition Section */}
        {route.delay_decomposition && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-bold text-text-primary tracking-wider font-mono flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-ai-cyan">analytics</span>
                Root Cause Delay Decomposition
              </span>
              <span className="text-[10px] font-mono font-bold bg-ai-primary/20 text-ai-cyan border border-ai-primary/40 px-2 py-0.5 rounded uppercase">
                {route.delay_decomposition.primary_cause.replace(/_/g, " ")}
              </span>
            </div>

            {route.delay_decomposition.total_delay_min > 0 ? (
              <div className="space-y-1.5">
                <div className="h-3 w-full bg-slate-900 rounded overflow-hidden flex gap-0.5 p-0.5 border border-white/10">
                  {route.delay_decomposition.incident_delay_min > 0 && (
                    <div
                      style={{
                        width: `${(route.delay_decomposition.incident_delay_min / route.delay_decomposition.total_delay_min) * 100}%`,
                      }}
                      className="h-full bg-rose-500 rounded-sm"
                      title={`Incident Bottlenecks: ${route.delay_decomposition.incident_delay_min}m`}
                    />
                  )}
                  {route.delay_decomposition.baseline_congestion_min > 0 && (
                    <div
                      style={{
                        width: `${(route.delay_decomposition.baseline_congestion_min / route.delay_decomposition.total_delay_min) * 100}%`,
                      }}
                      className="h-full bg-amber-500 rounded-sm"
                      title={`Rush Hour Volume: ${route.delay_decomposition.baseline_congestion_min}m`}
                    />
                  )}
                  {route.delay_decomposition.weather_delay_min > 0 && (
                    <div
                      style={{
                        width: `${(route.delay_decomposition.weather_delay_min / route.delay_decomposition.total_delay_min) * 100}%`,
                      }}
                      className="h-full bg-cyan-500 rounded-sm"
                      title={`Monsoon / Weather Runoff: ${route.delay_decomposition.weather_delay_min}m`}
                    />
                  )}
                </div>

                <div className="grid grid-cols-3 gap-1 text-[11px] font-mono">
                  <div className="flex items-center gap-1 text-slate-300">
                    <span className="w-2 h-2 rounded-sm bg-rose-500 shrink-0"></span>
                    <span>Incidents: +{route.delay_decomposition.incident_delay_min}m</span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-300">
                    <span className="w-2 h-2 rounded-sm bg-amber-500 shrink-0"></span>
                    <span>Rush Vol: +{route.delay_decomposition.baseline_congestion_min}m</span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-300">
                    <span className="w-2 h-2 rounded-sm bg-cyan-500 shrink-0"></span>
                    <span>Weather: +{route.delay_decomposition.weather_delay_min}m</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[15px]">check_circle</span>
                <span>Free-flow travel speeds across corridor. Zero net delay.</span>
              </div>
            )}
          </div>
        )}

        {/* Segment Velocity Profile */}
        <div className="space-y-1.5 pt-2 border-t border-white/5">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-text-muted flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px] text-emerald-400">timeline</span>
              <span>Segment Velocity Profile:</span>
            </span>
            <span className="text-text-secondary font-semibold truncate max-w-[200px]">
              {hoveredSegment || `Bottleneck: ${summary.most_affected_segment}`}
            </span>
          </div>
          <div className="h-3 w-full bg-slate-900 rounded overflow-hidden flex gap-0.5 p-0.5 border border-white/10">
            {segments.map((seg, idx) => {
              let bgClass = "bg-traffic-normal";
              if (seg.traffic_level === "SEVERE") bgClass = "bg-traffic-severe";
              else if (seg.traffic_level === "HEAVY") bgClass = "bg-traffic-heavy";
              else if (seg.traffic_level === "MODERATE") bgClass = "bg-traffic-moderate";

              return (
                <div
                  key={seg.segment_id ? `${seg.segment_id}-${idx}` : `seg-${idx}`}
                  onMouseEnter={() => setHoveredSegment(`${seg.name}: ${seg.average_speed_kmh} km/h (${seg.traffic_level})`)}
                  onMouseLeave={() => setHoveredSegment(null)}
                  className={`h-full flex-1 rounded-sm transition-opacity hover:opacity-80 cursor-pointer ${bgClass}`}
                  title={`${seg.name}: ${seg.average_speed_kmh} km/h`}
                />
              );
            })}
          </div>
        </div>
      </div>

      {/* 4. Active Incident Diagnostics (Viewable Immediately) */}
      <div className="border border-white/5 rounded-lg bg-surface-card overflow-hidden">
        <button
          type="button"
          onClick={() => setIncidentsOpen(!incidentsOpen)}
          className="w-full px-3.5 py-2.5 flex items-center justify-between text-xs font-mono bg-surface-elevated/40 hover:bg-surface-elevated transition cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <span className={`material-symbols-outlined text-[17px] ${uniqueIncidents.length > 0 ? "text-amber-400" : "text-emerald-400"}`}>
              {uniqueIncidents.length > 0 ? "warning" : "verified"}
            </span>
            <span className="font-bold text-text-primary text-xs uppercase tracking-wider">
              Active Incidents Diagnostics ({uniqueIncidents.length})
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
              uniqueIncidents.length > 0
                ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                : "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
            }`}>
              {uniqueIncidents.length > 0 ? `${uniqueIncidents.length} HAZARD${uniqueIncidents.length > 1 ? "S" : ""}` : "ALL CLEAR"}
            </span>
            <span className="material-symbols-outlined text-text-muted text-[16px]">
              {incidentsOpen ? "expand_less" : "expand_more"}
            </span>
          </div>
        </button>

        {incidentsOpen && (
          <div className="p-3 space-y-2.5 border-t border-white/5 max-h-64 overflow-y-auto overscroll-contain">
            {uniqueIncidents.map((inc, idx) => {
              const isUnverified = inc.status === "REPORTED" || ((inc as any).report_count === 1 && inc.status !== "VERIFIED");
              return (
                <div
                  key={inc.id ? `${inc.id}-${idx}` : `inc-${idx}`}
                  onClick={() => onSelectIncident?.(inc)}
                  className={`text-xs space-y-2 bg-surface-panel p-3 rounded-lg border transition-all cursor-pointer hover:border-ai-cyan/50 hover:bg-surface-elevated/60 ${
                    isUnverified ? "border-amber-500/40 border-dashed" : "border-white/10"
                  }`}
                  title="Click to view detailed physical clearance diagnostics"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30">
                        {inc.type}
                      </span>
                      {isUnverified ? (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                          [UNVERIFIED - 1 REPORT]
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                          [VERIFIED CONSENSUS]
                        </span>
                      )}
                    </div>
                    {inc.clearance_window_display ? (
                      <span className="text-[10px] text-ai-cyan font-mono font-bold bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-500/30">
                        Clearance: {inc.clearance_window_display}
                      </span>
                    ) : (
                      <span className="text-xs text-text-muted font-mono">
                        {formatReportedTime(inc.reported_at)}
                      </span>
                    )}
                  </div>

                  <p className="text-text-primary text-xs font-sans leading-relaxed">{inc.description}</p>

                  <div className="flex items-center justify-between text-xs text-text-muted font-mono pt-1.5 border-t border-white/5">
                    <span className="truncate max-w-[200px]" title={inc.affectedSegments.join(", ")}>
                      At: {inc.affectedSegments.join(", ") || "Active Corridor"}
                    </span>
                    <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={async () => {
                          await voteClearance(inc.id, "STILL_THERE");
                        }}
                        className="px-2 py-0.5 bg-surface-card hover:bg-white/10 border border-white/10 rounded text-[10px] text-amber-300 font-mono transition cursor-pointer"
                        title="Confirm incident is still active"
                      >
                        Active
                      </button>
                      <button
                        onClick={async () => {
                          await voteClearance(inc.id, "CLEARED");
                        }}
                        className="px-2 py-0.5 bg-emerald-950/40 hover:bg-emerald-900/50 border border-emerald-500/30 rounded text-[10px] text-emerald-400 font-mono transition cursor-pointer"
                        title="Vote that road hazard has cleared"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
            {uniqueIncidents.length === 0 && (
              <div className="py-3 px-4 bg-emerald-950/20 border border-emerald-500/20 rounded-lg text-center space-y-1">
                <div className="flex items-center justify-center gap-1.5 text-emerald-400 font-mono text-xs font-bold">
                  <span className="material-symbols-outlined text-[16px]">verified</span>
                  <span>All Corridors Clear</span>
                </div>
                <p className="text-xs text-text-muted font-mono">
                  Zero active accidents or road closures detected along this route.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};


