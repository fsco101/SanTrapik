import React, { useState } from "react";
import type { RouteItem } from "../../types/traffic";

interface BottomTelemetrySheetProps {
  children: React.ReactNode;
  activeRoute: RouteItem | null;
}

export const BottomTelemetrySheet: React.FC<BottomTelemetrySheetProps> = ({ children, activeRoute }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 z-40 md:hidden bg-surface-panel/95 backdrop-blur-lg border-t border-white/10 rounded-t-xl transition-all duration-300 shadow-2xl flex flex-col ${
        isExpanded ? "h-[85vh]" : "h-20"
      }`}
    >
      {/* Draggable handle bar */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="h-7 w-full flex items-center justify-center cursor-pointer select-none"
      >
        <div className="w-10 h-1 rounded-full bg-white/20"></div>
      </div>

      {/* Collapsed mini-bar header */}
      {!isExpanded && activeRoute && (
        <div
          onClick={() => setIsExpanded(true)}
          className="px-4 pb-3 flex items-center justify-between font-mono cursor-pointer"
        >
          <div>
            <span className="text-[10px] uppercase text-text-muted block truncate max-w-[180px]">
              {activeRoute.name}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white">
                {activeRoute.summary.estimated_travel_time_min}m
              </span>
              <span className={`text-xs font-semibold ${activeRoute.summary.estimated_delay_min > 20 ? "text-traffic-severe" : "text-traffic-heavy"}`}>
                +{activeRoute.summary.estimated_delay_min}m delay
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-ai-cyan font-bold bg-indigo-950/80 px-2.5 py-1 rounded border border-ai-primary/40">
            <span>Tap to expand</span>
            <span className="material-symbols-outlined text-[15px]">expand_less</span>
          </div>
        </div>
      )}

      {/* Expanded full telemetry content */}
      <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${!isExpanded ? "hidden" : "block"}`}>
        <div className="flex items-center justify-between pb-1 border-b border-white/5">
          <span className="text-xs font-bold text-text-secondary uppercase tracking-wider font-mono">
            Full Route Telemetry
          </span>
          <button
            onClick={() => setIsExpanded(false)}
            className="text-text-muted hover:text-white flex items-center gap-1 text-xs font-mono"
          >
            <span>Close</span>
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};
