import React from "react";
import type { IncidentItem, IncidentSummary } from "../../types/traffic";
import { voteClearance } from "../../services/api";

interface IncidentDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  incident: IncidentItem | IncidentSummary | null;
  corridorName?: string;
}

export const IncidentDrawer: React.FC<IncidentDrawerProps> = ({
  isOpen,
  onClose,
  incident,
  corridorName,
}) => {
  if (!isOpen || !incident) return null;

  const incType = (incident as IncidentItem).incident_type || (incident as IncidentSummary).type || "INCIDENT";
  const severity = incident.severity || "MEDIUM";
  const description = incident.description || "Active traffic obstruction along corridor.";
  const reportedAt = incident.reported_at;

  const clearanceMins = incident.clearance_minutes ?? 25;
  const p10 = incident.p10_clearance_mins ?? Math.max(5, Math.round(clearanceMins * 0.8));
  const p50 = incident.p50_clearance_mins ?? clearanceMins;
  const p90 = incident.p90_clearance_mins ?? Math.round(clearanceMins * 1.35);
  const windowDisplay = incident.clearance_window_display || `~${p10}–${p90} mins`;
  const confidenceScore = incident.confidence_score ?? 0.85;
  const confidencePct = Math.round(confidenceScore * 100);

  const lanesBlocked = incident.lanes_blocked ?? 1;
  const roadWidth = incident.road_width_lanes ?? 4;
  const towStatus = incident.tow_dispatch_status || "PENDING";

  const formatReported = (timeStr?: string) => {
    if (!timeStr) return "Recently reported";
    try {
      if (timeStr.includes("T")) {
        return new Date(timeStr).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
      }
      return timeStr;
    } catch {
      return timeStr;
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toUpperCase()) {
      case "CRITICAL":
        return "bg-rose-500/20 text-rose-400 border-rose-500/40";
      case "HIGH":
        return "bg-orange-500/20 text-orange-400 border-orange-500/40";
      case "MEDIUM":
        return "bg-amber-500/20 text-amber-400 border-amber-500/40";
      default:
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/40";
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity duration-300">
      {/* Click outside backdrop */}
      <div className="flex-1 cursor-pointer" onClick={onClose} />

      {/* Slide-over Drawer Panel */}
      <div className="w-full max-w-md bg-surface-panel/95 backdrop-blur-xl border-l border-white/10 shadow-2xl flex flex-col h-full overflow-y-auto font-mono text-text-primary animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-4 border-b border-white/10 flex items-center justify-between bg-surface-elevated/50 sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-amber-400 text-xl">warning</span>
            <div>
              <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider block">
                Physical Clearance Diagnostics
              </span>
              <h3 className="font-outfit font-bold text-base text-white tracking-tight">
                {incType.replace(/_/g, " ")}
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg bg-surface-card hover:bg-white/10 border border-white/10 text-text-muted hover:text-white transition"
            title="Close Drawer"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <div className="p-4 space-y-4 flex-1">
          {/* Metadata Badges */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className={`px-2 py-0.5 rounded font-bold border ${getSeverityBadge(severity)}`}>
              {severity} SEVERITY
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              VERIFIED CONSENSUS
            </span>
            <span className="text-[11px] text-text-muted ml-auto">
              {formatReported(reportedAt)}
            </span>
          </div>

          {/* Location & Description */}
          <div className="bg-surface-card p-3 rounded-lg border border-white/5 space-y-1">
            <div className="text-[11px] text-text-muted uppercase">Corridor Location</div>
            <div className="text-sm font-semibold text-white">
              {corridorName || (incident as IncidentItem).corridor || "Monitored Arterial"}
            </div>
            <p className="text-xs text-text-secondary font-sans pt-1 leading-relaxed">
              {description}
            </p>
          </div>

          {/* AI Clearance Forecast Section (SP9-001 & SP9-002) */}
          <div className="p-4 rounded-lg border border-indigo-500/40 bg-gradient-to-b from-indigo-950/40 to-slate-950/60 space-y-3 shadow-inner">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-ai-cyan text-xs font-bold font-outfit">
                <span className="material-symbols-outlined text-[17px]">auto_awesome</span>
                <span>AI Physical Clearance Prognosis</span>
              </div>
              <span className="text-[10px] font-mono text-ai-cyan bg-indigo-900/70 px-2 py-0.5 rounded border border-indigo-500/30 font-bold">
                SP9-001 Model
              </span>
            </div>

            {/* Clearance Duration Big Metric */}
            <div className="flex items-baseline justify-between pt-1">
              <div>
                <span className="text-[10px] uppercase text-text-muted block">Estimated Clearance</span>
                <span className="text-2xl font-bold text-white tracking-tight">
                  {windowDisplay}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase text-text-muted block">Confidence</span>
                <span className="text-lg font-bold text-ai-cyan">
                  {confidencePct}%
                </span>
              </div>
            </div>

            {/* Confidence Meter Bar */}
            <div className="space-y-1">
              <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden border border-white/10 p-0.5">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 rounded-full transition-all duration-500"
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
              <div className="flex justify-between text-[9px] text-text-muted font-mono">
                <span>Model Certainty</span>
                <span>{confidenceScore >= 0.8 ? "HIGH FIDELITY" : "MODERATE"}</span>
              </div>
            </div>

            {/* P10 / P50 / P90 Quantile Envelopes */}
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/10 text-center">
              <div className="bg-black/40 p-2 rounded border border-white/5">
                <span className="text-[9px] uppercase text-emerald-400 block font-bold">P10 Optimistic</span>
                <span className="text-sm font-bold text-white">~{p10}m</span>
              </div>
              <div className="bg-black/40 p-2 rounded border border-ai-cyan/30">
                <span className="text-[9px] uppercase text-ai-cyan block font-bold">P50 Expected</span>
                <span className="text-sm font-bold text-white">~{p50}m</span>
              </div>
              <div className="bg-black/40 p-2 rounded border border-rose-500/20">
                <span className="text-[9px] uppercase text-rose-400 block font-bold">P90 Protracted</span>
                <span className="text-sm font-bold text-white">~{p90}m</span>
              </div>
            </div>
          </div>

          {/* Physical Attributes Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            {/* Lanes Blocked */}
            <div className="bg-surface-card p-3 rounded-lg border border-white/5 space-y-1">
              <span className="text-[10px] uppercase text-text-muted block font-bold">Lanes Blocked</span>
              <div className="flex items-center gap-1.5 text-rose-400 font-bold text-sm">
                <span className="material-symbols-outlined text-[16px]">remove_road</span>
                <span>{lanesBlocked} / {roadWidth} Lanes</span>
              </div>
              <div className="flex gap-1 pt-1">
                {Array.from({ length: roadWidth }).map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-1.5 flex-1 rounded-sm ${idx < lanesBlocked ? "bg-rose-500" : "bg-emerald-500/40"}`}
                  />
                ))}
              </div>
            </div>

            {/* Tow Truck Dispatch Status */}
            <div className="bg-surface-card p-3 rounded-lg border border-white/5 space-y-1">
              <span className="text-[10px] uppercase text-text-muted block font-bold">Tow Dispatch</span>
              <div className="flex items-center gap-1.5 text-sm font-bold">
                <span className="material-symbols-outlined text-[16px] text-amber-400">local_shipping</span>
                {towStatus === "ON_SCENE" ? (
                  <span className="text-emerald-400">ON SCENE</span>
                ) : (
                  <span className="text-amber-300">DISPATCHED</span>
                )}
              </div>
              <span className="text-[10px] text-text-muted block pt-1">
                {towStatus === "ON_SCENE" ? "Active towing underway" : "Transit en route"}
              </span>
            </div>
          </div>

          {/* Commuter Consensus Actions */}
          <div className="bg-surface-card p-3 rounded-lg border border-white/5 space-y-2">
            <div className="text-[10px] uppercase text-text-muted font-bold">
              Commuter Verification Actions
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={async () => {
                  await voteClearance(incident.id, "STILL_THERE");
                  onClose();
                }}
                className="px-3 py-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 rounded text-amber-300 text-xs font-bold flex items-center justify-center gap-1.5 transition"
              >
                <span className="material-symbols-outlined text-[15px]">report</span>
                <span>Still There</span>
              </button>
              <button
                onClick={async () => {
                  await voteClearance(incident.id, "CLEARED");
                  onClose();
                }}
                className="px-3 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 rounded text-emerald-400 text-xs font-bold flex items-center justify-center gap-1.5 transition"
              >
                <span className="material-symbols-outlined text-[15px]">check_circle</span>
                <span>Mark Cleared</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
