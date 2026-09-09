import React from "react";
import type { Coordinate } from "../../types/traffic";

interface RouteSearchProps {
  origin: Coordinate;
  destination: Coordinate;
  onOriginChange: (coord: Coordinate) => void;
  onDestinationChange: (coord: Coordinate) => void;
  onSwap: () => void;
  onAnalyze: () => void;
  isLoading: boolean;
}

export const RouteSearch: React.FC<RouteSearchProps> = ({
  origin,
  destination,
  onOriginChange,
  onDestinationChange,
  onSwap,
  onAnalyze,
  isLoading,
}) => {
  return (
    <div className="bg-surface-panel rounded-lg p-3 border border-white/10 space-y-3">
      <div className="relative space-y-2">
        {/* Origin */}
        <div className="flex items-center gap-2 bg-surface-card rounded px-3 py-2 border border-white/5 focus-within:border-ai-primary focus-within:shadow-active-glow transition">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0"></span>
          <div className="flex-1">
            <span className="text-[9px] uppercase font-bold text-text-muted tracking-wider block font-mono">
              Start Point (NCR)
            </span>
            <input
              type="text"
              value={origin.name || ""}
              onChange={(e) => onOriginChange({ ...origin, name: e.target.value })}
              placeholder="e.g. Quezon City Circle"
              className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none font-sans"
            />
          </div>
        </div>

        {/* Swap Button */}
        <button
          onClick={onSwap}
          type="button"
          title="Swap origin and destination"
          className="absolute right-3 top-[34px] z-10 w-7 h-7 rounded-full bg-surface-elevated hover:bg-slate-600 border border-white/10 flex items-center justify-center text-text-secondary hover:text-white transition shadow-sm"
        >
          <span className="material-symbols-outlined text-[15px]">swap_vert</span>
        </button>

        {/* Destination */}
        <div className="flex items-center gap-2 bg-surface-card rounded px-3 py-2 border border-white/5 focus-within:border-ai-primary focus-within:shadow-active-glow transition">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0"></span>
          <div className="flex-1">
            <span className="text-[9px] uppercase font-bold text-text-muted tracking-wider block font-mono">
              Destination (NCR)
            </span>
            <input
              type="text"
              value={destination.name || ""}
              onChange={(e) => onDestinationChange({ ...destination, name: e.target.value })}
              placeholder="e.g. Ayala Triangle, Makati"
              className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none font-sans"
            />
          </div>
        </div>
      </div>

      {/* Action Button */}
      <button
        onClick={onAnalyze}
        disabled={isLoading}
        className="w-full bg-ai-primary hover:bg-indigo-600 active:scale-[0.99] text-white font-outfit font-semibold py-2.5 px-4 rounded transition flex items-center justify-center gap-2 shadow-active-glow disabled:opacity-50 text-sm"
      >
        <span className="material-symbols-outlined text-[18px]">
          {isLoading ? "hourglass_top" : "insights"}
        </span>
        <span>{isLoading ? "Analyzing NCR Telemetry..." : "Analyze Route Intelligence"}</span>
      </button>
    </div>
  );
};
