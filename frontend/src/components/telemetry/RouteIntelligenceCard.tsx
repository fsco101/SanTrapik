import React, { useState } from "react";
import type { RouteItem } from "../../types/traffic";

interface RouteIntelligenceCardProps {
  route: RouteItem;
}

export const RouteIntelligenceCard: React.FC<RouteIntelligenceCardProps> = ({ route }) => {
  const [incidentsOpen, setIncidentsOpen] = useState(true);
  const [hoveredSegment, setHoveredSegment] = useState<string | null>(null);

  const { summary, expected_relief, segments } = route;

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

  // Deduplicate incidents across all traversed segments by ID and aggregate affected road names
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
        affectedSegments: string[];
      }
    >();

    segments.forEach((s) => {
      (s.incidents || []).forEach((inc) => {
        const key = inc.id || `${inc.type}-${inc.description}`;
        if (!incidentMap.has(key)) {
          incidentMap.set(key, {
            ...inc,
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
    <div className="bg-surface-panel rounded-lg border border-white/10 overflow-hidden shadow-lg space-y-3 p-4">
      {/* 1. Header with Destination & Severity Badge */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider font-mono block">
            Corridor Telemetry
          </span>
          <h2 className="font-outfit font-bold text-lg text-text-primary tracking-tight">
            {route.name}
          </h2>
        </div>
        <div className={`px-2.5 py-1 rounded text-xs font-mono font-bold uppercase tracking-wider border flex items-center gap-1.5 ${sevStyle.badge}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
          <span>{summary.overall_congestion}</span>
        </div>
      </div>

      {/* 2. Metric Cluster: Estimated vs Normal vs Net Delay */}
      <div className="grid grid-cols-3 gap-2 bg-surface-card rounded p-3 border border-white/5 font-mono">
        <div>
          <span className="text-[10px] uppercase text-text-muted block">Estimated</span>
          <span className="text-xl font-bold text-text-primary">
            {formatTime(summary.estimated_travel_time_min)}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-text-muted block">Normal</span>
          <span className="text-xl font-bold text-text-secondary">
            {formatTime(summary.normal_travel_time_min)}
          </span>
        </div>
        <div>
          <span className="text-[10px] uppercase text-text-muted block">Net Delay</span>
          <span className={`text-xl font-bold ${summary.estimated_delay_min > 0 ? sevStyle.text : "text-traffic-normal"}`}>
            {summary.estimated_delay_min > 0 ? `+${summary.estimated_delay_min}m` : "On Time"}
          </span>
        </div>
      </div>

      {/* 3. Segment Velocity Bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-text-muted text-[11px]">Segment Velocity Profile:</span>
          <span className="text-text-secondary text-[11px] truncate max-w-[200px]">
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

      {/* 4. Active Incident Accordion */}
      <div className="border border-white/5 rounded bg-surface-card overflow-hidden">
        <button
          onClick={() => setIncidentsOpen(!incidentsOpen)}
          className="w-full px-3 py-2 flex items-center justify-between text-xs font-mono bg-surface-elevated/40 hover:bg-surface-elevated transition"
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-amber-400 text-[16px]">warning</span>
            <span className="font-semibold text-text-primary">
              Active Incidents Diagnostics ({uniqueIncidents.length})
            </span>
          </div>
          <span className="material-symbols-outlined text-text-muted text-[16px]">
            {incidentsOpen ? "expand_less" : "expand_more"}
          </span>
        </button>

        {incidentsOpen && (
          <div className="p-3 space-y-2 border-t border-white/5">
            {uniqueIncidents.map((inc, idx) => (
              <div
                key={inc.id ? `${inc.id}-${idx}` : `inc-${idx}`}
                className="text-xs space-y-1 bg-surface-panel p-2 rounded border border-white/5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30">
                    {inc.type}
                  </span>
                  <span className="text-[10px] text-text-muted font-mono">
                    {formatReportedTime(inc.reported_at)}
                  </span>
                </div>
                <p className="text-text-primary text-xs font-sans">{inc.description}</p>
                <div className="flex items-center justify-between text-[10px] text-text-muted font-mono pt-1">
                  <span className="truncate max-w-[220px]" title={inc.affectedSegments.join(", ")}>
                    At: {inc.affectedSegments.join(", ") || "Active Corridor"}
                  </span>
                  <span className="text-text-secondary font-bold">Source: MMDA</span>
                </div>
              </div>
            ))}
            {uniqueIncidents.length === 0 && (
              <p className="text-xs text-text-muted font-mono text-center py-1">
                No active collision or construction blockages detected along this route.
              </p>
            )}
          </div>
        )}
      </div>

      {/* 5. AI Relief Prediction Footer */}
      <div className="pt-2 border-t border-indigo-500/30 bg-indigo-950/20 -mx-4 -mb-4 p-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-ai-cyan text-[14px]">✦</span>
            <span className="text-xs font-bold font-outfit text-white tracking-wide">
              AI Congestion Relief Prediction
            </span>
          </div>
          <span className="text-[10px] font-mono font-semibold text-ai-cyan bg-indigo-900/60 px-1.5 py-0.5 rounded border border-indigo-500/30">
            Model v1.0.2
          </span>
        </div>

        <div className="flex items-baseline justify-between font-mono">
          <div>
            <span className="text-[10px] text-text-muted block">Expected Relief:</span>
            <span className="text-lg font-bold text-white tracking-tight">
              {expected_relief.relief_time}
            </span>
            <span className="text-xs text-ai-cyan ml-1.5">
              (~{expected_relief.estimated_minutes_remaining}m remaining)
            </span>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-text-muted block">Confidence:</span>
            <span className="text-sm font-bold text-ai-cyan">
              {Math.round(expected_relief.confidence * 100)}%
            </span>
          </div>
        </div>

        {/* Linear Confidence Bar */}
        <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden border border-white/5">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full transition-all duration-500"
            style={{ width: `${Math.round(expected_relief.confidence * 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};
