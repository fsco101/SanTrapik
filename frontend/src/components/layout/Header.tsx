import React from "react";
import type { DashboardStats } from "../../types/traffic";

interface HeaderProps {
  stats: DashboardStats | null;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ stats, onRefresh, isLoading }) => {
  return (
    <header className="h-14 border-b border-white/10 bg-surface-panel/90 backdrop-blur-md px-4 flex items-center justify-between z-30 select-none">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-gradient-to-br from-indigo-500 via-indigo-600 to-cyan-500 flex items-center justify-center shadow-active-glow">
            <span className="material-symbols-outlined text-white text-[18px]">traffic</span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-outfit font-bold text-lg tracking-tight text-text-primary">
                San<span className="text-ai-primary">Trapik</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider font-bold bg-white/10 text-text-secondary px-1.5 py-0.5 rounded text-xs font-mono">
                NCR
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Live Telemetry Pulsar */}
        <div className="flex items-center gap-2 bg-surface-card px-2.5 py-1 rounded-full border border-white/5 text-xs font-mono">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-traffic-normal"></span>
          </span>
          <span className="text-text-secondary hidden sm:inline">Telemetry Live</span>
          <span className="text-text-muted text-[10px] hidden md:inline">1m ago</span>
        </div>

        {/* Macro City Stats Badge */}
        {stats && (
          <div className="hidden lg:flex items-center gap-2 bg-surface-card px-3 py-1 rounded border border-white/5 text-xs font-mono">
            <span className="text-text-muted">Active Incidents:</span>
            <span className="text-traffic-severe font-bold">{stats.active_incidents}</span>
            <span className="text-white/20">|</span>
            <span className="text-text-muted">Avg Speed:</span>
            <span className="text-traffic-normal font-bold">{stats.average_road_speed_kmh} km/h</span>
          </div>
        )}

        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh live telemetry"
          className="w-8 h-8 rounded bg-surface-card hover:bg-surface-elevated border border-white/10 flex items-center justify-center text-text-secondary hover:text-white transition"
        >
          <span className={`material-symbols-outlined text-[16px] ${isLoading ? "animate-spin" : ""}`}>
            refresh
          </span>
        </button>
      </div>
    </header>
  );
};
