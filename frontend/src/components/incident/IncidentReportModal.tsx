import React, { useState } from "react";
import { reportLiveIncident } from "../../services/api";
import type { IncidentItem, Coordinate } from "../../types/traffic";

interface IncidentReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIncidentReported: (incident: IncidentItem) => void;
  defaultLocation?: Coordinate;
}

const COMMON_CORRIDORS = [
  { name: "EDSA - Ortigas Flyover", lat: 14.5855, lng: 121.0575 },
  { name: "EDSA - Guadalupe Bridge", lat: 14.5685, lng: 121.0465 },
  { name: "EDSA - Cubao Underpass", lat: 14.6185, lng: 121.0545 },
  { name: "C-5 - Bagong Ilog Flyover", lat: 14.5740, lng: 121.0690 },
  { name: "C-5 - Eastwood Libis", lat: 14.6110, lng: 121.0790 },
  { name: "Commonwealth - Philcoa", lat: 14.6540, lng: 121.0580 },
  { name: "España Blvd - UST", lat: 14.6080, lng: 120.9920 },
  { name: "Quezon Ave - Delta", lat: 14.6360, lng: 121.0310 },
];

export const IncidentReportModal: React.FC<IncidentReportModalProps> = ({
  isOpen,
  onClose,
  onIncidentReported,
  defaultLocation,
}) => {
  const [incidentType, setIncidentType] = useState<string>("ACCIDENT");
  const [severity, setSeverity] = useState<string>("HIGH");
  const [corridorName, setCorridorName] = useState<string>(
    defaultLocation?.name || "EDSA - Ortigas Flyover"
  );
  const [coords, setCoords] = useState<{ lat: number; lng: number }>({
    lat: defaultLocation?.lat || 14.5855,
    lng: defaultLocation?.lng || 121.0575,
  });
  const [description, setDescription] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSelectCorridor = (item: { name: string; lat: number; lng: number }) => {
    setCorridorName(item.name);
    setCoords({ lat: item.lat, lng: item.lng });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);

    try {
      const created = await reportLiveIncident({
        incident_type: incidentType,
        severity,
        road_name: corridorName,
        corridor: corridorName,
        lat: coords.lat,
        lng: coords.lng,
        description: description.trim() || `Reported ${incidentType.toLowerCase()} on ${corridorName}`,
        data_source: "COMMUTER_LIVE_REPORT",
      });

      onIncidentReported(created);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit live incident. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-surface-panel border border-white/15 rounded-xl shadow-2xl overflow-hidden font-sans text-text-primary">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-surface-elevated/70 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
              <span className="material-symbols-outlined text-[18px]">crisis_alert</span>
            </div>
            <div>
              <h3 className="text-sm font-bold tracking-tight text-white">Report Live Road Incident</h3>
              <p className="text-[11px] text-text-muted">Real-time commuter reporting with automatic road centerline snapping</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-white p-1 rounded transition"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {errorMsg && (
            <div className="p-2.5 bg-rose-950/80 border border-rose-500/40 rounded text-rose-300 text-[11px] flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">error</span>
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Incident Type Grid */}
          <div>
            <label className="block text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Incident Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { type: "ACCIDENT", label: "Accident", icon: "car_crash" },
                { type: "ROADWORK", label: "Roadwork", icon: "construction" },
                { type: "FLOOD", label: "Flooding", icon: "flood" },
                { type: "STALLED_VEHICLE", label: "Stalled", icon: "car_repair" },
                { type: "HAZARD", label: "Hazard", icon: "warning" },
              ].map((item) => (
                <button
                  type="button"
                  key={item.type}
                  onClick={() => setIncidentType(item.type)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border font-mono text-[11px] transition text-left ${
                    incidentType === item.type
                      ? "bg-rose-950/70 border-rose-500/80 text-rose-300 font-bold shadow-sm"
                      : "bg-surface-elevated/40 border-white/5 hover:border-white/20 text-text-secondary"
                  }`}
                >
                  <span className="material-symbols-outlined text-[16px]">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Severity Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Severity / Obstruction Level
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[
                { sev: "CRITICAL", label: "Critical", desc: "Blocked road", color: "text-rose-400 border-rose-500/80 bg-rose-950/50" },
                { sev: "HIGH", label: "High", desc: "2+ lanes", color: "text-amber-400 border-amber-500/80 bg-amber-950/50" },
                { sev: "MEDIUM", label: "Moderate", desc: "1 lane", color: "text-yellow-400 border-yellow-500/80 bg-yellow-950/50" },
                { sev: "LOW", label: "Low", desc: "Shoulder", color: "text-blue-400 border-blue-500/80 bg-blue-950/50" },
              ].map((item) => (
                <button
                  type="button"
                  key={item.sev}
                  onClick={() => setSeverity(item.sev)}
                  className={`p-2 rounded-lg border text-center transition ${
                    severity === item.sev
                      ? `${item.color} font-bold shadow-sm`
                      : "bg-surface-elevated/40 border-white/5 text-text-muted hover:border-white/20"
                  }`}
                >
                  <div className="text-[11px] font-mono">{item.label}</div>
                  <div className="text-[9px] opacity-70">{item.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Location & Quick Corridors */}
          <div>
            <label className="block text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Corridor / Street Location
            </label>
            <input
              type="text"
              value={corridorName}
              onChange={(e) => setCorridorName(e.target.value)}
              placeholder="e.g. EDSA - Ortigas Flyover SB"
              className="w-full bg-surface-elevated/80 border border-white/10 rounded-lg px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-rose-500 transition mb-2"
              required
            />

            {/* Quick Chips */}
            <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto pr-1">
              {COMMON_CORRIDORS.map((item) => (
                <button
                  type="button"
                  key={item.name}
                  onClick={() => handleSelectCorridor(item)}
                  className={`text-[10px] px-2 py-1 rounded border font-mono transition ${
                    corridorName === item.name
                      ? "bg-rose-500/20 border-rose-500 text-rose-300 font-bold"
                      : "bg-surface-elevated/40 border-white/5 hover:border-white/20 text-text-muted"
                  }`}
                >
                  {item.name}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-1.5">
              Details & Lane Impact
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Multi-vehicle fender bender blocking 2 middle lanes; MMDA enforcer on scene directing traffic"
              rows={2}
              className="w-full bg-surface-elevated/80 border border-white/10 rounded-lg p-2.5 text-white font-mono text-xs focus:outline-none focus:border-rose-500 transition resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-white/10 text-text-secondary hover:text-white hover:bg-surface-elevated text-xs transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !corridorName.trim()}
              className="px-5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg flex items-center gap-1.5 disabled:opacity-50 transition"
            >
              {submitting ? (
                <>
                  <span className="animate-spin material-symbols-outlined text-[15px]">refresh</span>
                  <span>Reporting...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[15px]">send</span>
                  <span>Submit Live Report</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
