import React, { useState, useEffect, useRef } from "react";
import type { Coordinate, PlaceSuggestion, TransportMode } from "../../types/traffic";
import { searchPlaces } from "../../services/api";

interface RouteSearchProps {
  origin: Coordinate;
  destination: Coordinate;
  onOriginChange: (coord: Coordinate) => void;
  onDestinationChange: (coord: Coordinate) => void;
  onSwap: () => void;
  onAnalyze: () => void;
  isLoading: boolean;
  transportMode: TransportMode;
  onTransportModeChange: (mode: TransportMode) => void;
  useExpressway: boolean;
  onUseExpresswayChange: (use: boolean) => void;
  plateEnding: number | null;
  onPlateEndingChange: (ending: number | null) => void;
  hasActiveRoutes?: boolean;
}

export const RouteSearch: React.FC<RouteSearchProps> = ({
  origin,
  destination,
  onOriginChange,
  onDestinationChange,
  onSwap,
  onAnalyze,
  isLoading,
  transportMode,
  onTransportModeChange,
  useExpressway,
  onUseExpresswayChange,
  plateEnding,
  onPlateEndingChange,
  hasActiveRoutes = false,
}) => {
  // Origin search state
  const [originQuery, setOriginQuery] = useState(origin.name || "");
  const [originSuggestions, setOriginSuggestions] = useState<PlaceSuggestion[]>([]);
  const [isOriginOpen, setIsOriginOpen] = useState(false);
  const [isOriginLoading, setIsOriginLoading] = useState(false);

  // Destination search state
  const [destQuery, setDestQuery] = useState(destination.name || "");
  const [destSuggestions, setDestSuggestions] = useState<PlaceSuggestion[]>([]);
  const [isDestOpen, setIsDestOpen] = useState(false);
  const [isDestLoading, setIsDestLoading] = useState(false);

  const [isExpanded, setIsExpanded] = useState(!hasActiveRoutes);

  // If active routes appear, auto-collapse if user hasn't explicitly opened it
  useEffect(() => {
    if (hasActiveRoutes) {
      setIsExpanded(false);
    }
  }, [hasActiveRoutes]);

  const originContainerRef = useRef<HTMLDivElement>(null);
  const destContainerRef = useRef<HTMLDivElement>(null);

  // Sync state if props change from outside (e.g. swap or quick corridors)
  useEffect(() => {
    setOriginQuery(origin.name || "");
  }, [origin.name]);

  useEffect(() => {
    setDestQuery(destination.name || "");
  }, [destination.name]);

  // Click outside listener to dismiss dropdowns
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (originContainerRef.current && !originContainerRef.current.contains(e.target as Node)) {
        setIsOriginOpen(false);
      }
      if (destContainerRef.current && !destContainerRef.current.contains(e.target as Node)) {
        setIsDestOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search for Origin
  useEffect(() => {
    if (!originQuery || originQuery.trim().length < 2) {
      setOriginSuggestions([]);
      return;
    }
    if (originQuery === origin.name) return;

    setIsOriginLoading(true);
    const timer = setTimeout(async () => {
      const results = await searchPlaces(originQuery);
      setOriginSuggestions(results);
      setIsOriginLoading(false);
      setIsOriginOpen(true);
    }, 280);

    return () => clearTimeout(timer);
  }, [originQuery, origin.name]);

  // Debounced search for Destination
  useEffect(() => {
    if (!destQuery || destQuery.trim().length < 2) {
      setDestSuggestions([]);
      return;
    }
    if (destQuery === destination.name) return;

    setIsDestLoading(true);
    const timer = setTimeout(async () => {
      const results = await searchPlaces(destQuery);
      setDestSuggestions(results);
      setIsDestLoading(false);
      setIsDestOpen(true);
    }, 280);

    return () => clearTimeout(timer);
  }, [destQuery, destination.name]);

  const [isCodingOpen, setIsCodingOpen] = useState(plateEnding !== null);

  const handleSelectOrigin = (p: PlaceSuggestion) => {
    setOriginQuery(p.name);
    onOriginChange({
      name: p.name,
      lat: p.lat,
      lng: p.lng,
    });
    setIsOriginOpen(false);
  };

  const handleSelectDestination = (p: PlaceSuggestion) => {
    setDestQuery(p.name);
    onDestinationChange({
      name: p.name,
      lat: p.lat,
      lng: p.lng,
    });
    setIsDestOpen(false);
  };

  // 1. Compact Corridor Summary Bar (when routes exist and user collapsed search)
  if (!isExpanded && hasActiveRoutes) {
    return (
      <div className="bg-surface-panel rounded-lg p-3 border border-white/10 shadow-sm flex items-center justify-between gap-2.5 transition">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-text-primary min-w-0 flex-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0"></span>
            <span className="truncate max-w-[130px] font-sans text-white font-medium" title={origin.name}>
              {origin.name || "Origin"}
            </span>
            <span className="material-symbols-outlined text-[14px] text-text-muted shrink-0">arrow_forward</span>
            <span className="w-2 h-2 rounded-sm bg-rose-500 shrink-0"></span>
            <span className="truncate max-w-[130px] font-sans text-white font-medium" title={destination.name}>
              {destination.name || "Destination"}
            </span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0 font-mono text-[11px]">
            <span className="px-2 py-0.5 rounded bg-ai-primary/20 text-ai-cyan border border-ai-cyan/30 font-bold uppercase">
              {transportMode}
            </span>
            {useExpressway ? (
              <span className="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold">
                TOLL
              </span>
            ) : (
              <span className="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold">
                SURFACE
              </span>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded(true)}
          className="px-2.5 py-1 rounded bg-surface-card hover:bg-surface-elevated border border-white/10 text-xs font-mono text-ai-cyan hover:text-white flex items-center gap-1 transition shrink-0 cursor-pointer shadow-sm"
          title="Change route origin, destination, or transport mode"
        >
          <span className="material-symbols-outlined text-[15px]">tune</span>
          <span>Edit</span>
        </button>
      </div>
    );
  }

  return (
    <div className="bg-surface-panel rounded-lg p-3.5 border border-white/10 space-y-3 shadow-md">
      {/* Search Header when expanded with active routes */}
      {hasActiveRoutes && (
        <div className="flex items-center justify-between pb-1 border-b border-white/5 font-mono text-xs">
          <span className="text-text-muted font-bold uppercase tracking-wider text-[10px]">
            Route Planner
          </span>
          <button
            type="button"
            onClick={() => setIsExpanded(false)}
            className="text-text-secondary hover:text-white flex items-center gap-1 text-[11px] cursor-pointer"
          >
            <span>Minimize</span>
            <span className="material-symbols-outlined text-[15px]">expand_less</span>
          </button>
        </div>
      )}

      {/* 1. Origin & Destination with Vertical Transit Rail */}
      <div className="flex items-center gap-2.5">
        {/* Rail indicator */}
        <div className="flex flex-col items-center py-2 shrink-0 self-stretch justify-between">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-emerald-500/30 shrink-0"></span>
          <div className="w-0.5 flex-1 bg-gradient-to-b from-emerald-400 via-slate-600 to-rose-500 my-1"></div>
          <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 ring-2 ring-rose-500/30 shrink-0"></span>
        </div>

        {/* Input fields */}
        <div className="flex-1 space-y-1.5 min-w-0">
          {/* Origin Field with Autocomplete */}
          <div ref={originContainerRef} className="relative">
            <div className="flex items-center gap-2 bg-surface-card rounded px-2.5 py-1.5 border border-white/5 focus-within:border-ai-primary focus-within:shadow-active-glow transition">
              <div className="flex-1 min-w-0">
                <span className="text-[8px] uppercase font-bold text-emerald-400 tracking-wider block font-mono">
                  Start Point (NCR)
                </span>
                <input
                  type="text"
                  value={originQuery}
                  onFocus={() => {
                    if (originSuggestions.length > 0) setIsOriginOpen(true);
                  }}
                  onChange={(e) => {
                    setOriginQuery(e.target.value);
                    setIsOriginOpen(true);
                  }}
                  placeholder="Search origin in Metro Manila..."
                  className="w-full bg-transparent text-xs text-text-primary placeholder:text-text-muted focus:outline-none font-sans truncate"
                />
              </div>
              {isOriginLoading && (
                <span className="material-symbols-outlined text-[14px] text-text-muted animate-spin">
                  progress_activity
                </span>
              )}
              {originQuery && !isOriginLoading && (
                <button
                  type="button"
                  onClick={() => {
                    setOriginQuery("");
                    setOriginSuggestions([]);
                  }}
                  className="text-text-muted hover:text-white cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span>
                </button>
              )}
            </div>

            {/* Origin Autocomplete Dropdown */}
            {isOriginOpen && originSuggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-surface-elevated border border-white/15 rounded-lg shadow-2xl z-50 max-h-60 overflow-y-auto divide-y divide-white/5 backdrop-blur-md">
                {originSuggestions.map((place, idx) => (
                  <button
                    key={`${place.name}-${idx}`}
                    type="button"
                    onClick={() => handleSelectOrigin(place)}
                    className="w-full text-left px-3 py-2 hover:bg-ai-primary/20 hover:border-l-2 hover:border-ai-primary flex items-start gap-2 transition text-xs group cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-emerald-400 text-[15px] mt-0.5 shrink-0 group-hover:scale-110 transition">
                      location_on
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-text-primary group-hover:text-white truncate text-[11px]">
                        {place.name}
                      </p>
                      <p className="text-[9px] text-text-muted truncate">
                        {place.display_name}
                      </p>
                    </div>
                    {place.city && (
                      <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-white/5 text-text-secondary shrink-0 border border-white/5">
                        {place.city}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Destination Field with Autocomplete */}
          <div ref={destContainerRef} className="relative">
            <div className="flex items-center gap-2 bg-surface-card rounded px-2.5 py-1.5 border border-white/5 focus-within:border-ai-primary focus-within:shadow-active-glow transition">
              <div className="flex-1 min-w-0">
                <span className="text-[8px] uppercase font-bold text-rose-400 tracking-wider block font-mono">
                  Destination (NCR)
                </span>
                <input
                  type="text"
                  value={destQuery}
                  onFocus={() => {
                    if (destSuggestions.length > 0) setIsDestOpen(true);
                  }}
                  onChange={(e) => {
                    setDestQuery(e.target.value);
                    setIsDestOpen(true);
                  }}
                  placeholder="Search destination in Metro Manila..."
                  className="w-full bg-transparent text-xs text-text-primary placeholder:text-text-muted focus:outline-none font-sans truncate"
                />
              </div>
              {isDestLoading && (
                <span className="material-symbols-outlined text-[14px] text-text-muted animate-spin">
                  progress_activity
                </span>
              )}
              {destQuery && !isDestLoading && (
                <button
                  type="button"
                  onClick={() => {
                    setDestQuery("");
                    setDestSuggestions([]);
                  }}
                  className="text-text-muted hover:text-white cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span>
                </button>
              )}
            </div>

            {/* Destination Autocomplete Dropdown */}
            {isDestOpen && destSuggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-surface-elevated border border-white/15 rounded-lg shadow-2xl z-50 max-h-60 overflow-y-auto divide-y divide-white/5 backdrop-blur-md">
                {destSuggestions.map((place, idx) => (
                  <button
                    key={`${place.name}-${idx}`}
                    type="button"
                    onClick={() => handleSelectDestination(place)}
                    className="w-full text-left px-3 py-2 hover:bg-ai-primary/20 hover:border-l-2 hover:border-ai-primary flex items-start gap-2 transition text-xs group cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-rose-400 text-[15px] mt-0.5 shrink-0 group-hover:scale-110 transition">
                      flag
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-text-primary group-hover:text-white truncate text-[11px]">
                        {place.name}
                      </p>
                      <p className="text-[9px] text-text-muted truncate">
                        {place.display_name}
                      </p>
                    </div>
                    {place.city && (
                      <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-white/5 text-text-secondary shrink-0 border border-white/5">
                        {place.city}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Swap Button */}
        <button
          onClick={onSwap}
          type="button"
          title="Swap origin and destination"
          className="w-7 h-7 rounded-full bg-surface-elevated hover:bg-slate-700 border border-white/10 flex items-center justify-center text-text-secondary hover:text-white transition shadow-sm shrink-0 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[15px]">swap_vert</span>
        </button>
      </div>

      {/* 2. Transport Mode Selector (Street-Smart Commuter Options) */}
      <div className="space-y-1.5 pt-1">
        <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider block font-mono">
          Mode of Transportation
        </span>
        <div className="grid grid-cols-4 gap-1.5 bg-surface-card/60 p-1 rounded-lg border border-white/5">
          {[
            { id: "car", label: "Car", icon: "directions_car", sub: "Standard" },
            { id: "motorcycle", label: "Motorcycle", icon: "two_wheeler", sub: "Lane-filter" },
            { id: "jeepney", label: "Jeepney", icon: "airport_shuttle", sub: "Frequent stops" },
            { id: "walking", label: "Walking", icon: "directions_walk", sub: "Sidewalk" },
          ].map((mode) => {
            const isSelected = transportMode === mode.id;
            return (
              <button
                key={mode.id}
                type="button"
                onClick={() => {
                  onTransportModeChange(mode.id as TransportMode);
                  if (mode.id === "motorcycle" || mode.id === "walking") {
                    onUseExpresswayChange(false);
                  }
                }}
                className={`flex flex-col items-center justify-center py-2 px-1 rounded transition border cursor-pointer ${
                  isSelected
                    ? "bg-ai-primary/25 border-ai-primary text-white shadow-ai-aura"
                    : "bg-surface-elevated/40 border-transparent text-text-secondary hover:text-white hover:bg-surface-elevated"
                }`}
              >
                <span className={`material-symbols-outlined text-[19px] ${isSelected ? "text-ai-cyan" : ""}`}>
                  {mode.icon}
                </span>
                <span className="text-xs font-semibold mt-0.5 truncate max-w-full">
                  {mode.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Expressway Route Choice (Skyway / Tollway Toggle) */}
      <div className="flex items-center justify-between bg-surface-card rounded-lg px-3 py-2 border border-white/5">
        <div className="flex items-center gap-2.5">
          <span className="material-symbols-outlined text-[17px] text-amber-400">
            toll
          </span>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold text-text-primary">
                Expressway / Skyway
              </span>
              {transportMode === "motorcycle" && (
                <span className="text-[10px] font-mono px-1.5 py-0.2 bg-rose-500/20 text-rose-300 rounded border border-rose-500/30">
                  Sub-400cc Restricted
                </span>
              )}
              {transportMode === "walking" && (
                <span className="text-[10px] font-mono px-1.5 py-0.2 bg-slate-700 text-slate-300 rounded">
                  No Pedestrians
                </span>
              )}
            </div>
            <p className="text-[11px] text-text-muted mt-0.5">
              {transportMode === "motorcycle"
                ? "Sub-400cc bikes restricted from expressways"
                : transportMode === "walking"
                ? "Pedestrians routed via sidewalks & footbridges"
                : useExpressway
                ? "Fastest bypass via Skyway / Tollways"
                : "Surface arterial roads only (EDSA / C-5)"}
            </p>
          </div>
        </div>

        <button
          type="button"
          disabled={transportMode === "motorcycle" || transportMode === "walking"}
          onClick={() => onUseExpresswayChange(!useExpressway)}
          className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed ${
            useExpressway ? "bg-ai-primary" : "bg-slate-700"
          }`}
        >
          <span
            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
              useExpressway ? "translate-x-4" : "translate-x-0"
            }`}
          />
        </button>
      </div>

      {/* 4. MMDA Number Coding (UVVRP) Selector */}
      {(() => {
        const now = new Date();
        const dayOfWeek = now.getDay(); // 0: Sun, 1: Mon, 2: Tue, 3: Wed, 4: Thu, 5: Fri, 6: Sat
        const codingMap: Record<number, number[]> = {
          1: [1, 2],
          2: [3, 4],
          3: [5, 6],
          4: [7, 8],
          5: [9, 0],
        };
        const todayCodedDigits = codingMap[dayOfWeek] || [];
        const isCodedToday = todayCodedDigits.length > 0;

        return (
          <div className="bg-surface-card rounded-lg border border-white/5 overflow-hidden">
            <button
              type="button"
              onClick={() => transportMode === "car" && setIsCodingOpen(!isCodingOpen)}
              className={`w-full px-3 py-2 flex items-center justify-between text-xs font-mono transition ${
                transportMode === "car" ? "hover:bg-surface-elevated/40 cursor-pointer" : "cursor-default"
              }`}
            >
              <span className="text-[10px] uppercase font-bold text-text-muted tracking-wider block font-mono">
                MMDA UVVRP Number Coding
              </span>
              <div className="flex items-center gap-1.5">
                {transportMode !== "car" ? (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {transportMode.toUpperCase()} EXEMPT
                  </span>
                ) : isCodedToday ? (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    {todayCodedDigits.join(" & ")} CODED TODAY
                  </span>
                ) : (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-white/5">
                    WEEKEND SUSPENDED
                  </span>
                )}
                {transportMode === "car" && (
                  <span className="material-symbols-outlined text-text-muted text-[15px]">
                    {isCodingOpen ? "expand_less" : "expand_more"}
                  </span>
                )}
              </div>
            </button>

            {transportMode === "car" && isCodingOpen && (
              <div className="p-2.5 pt-1 border-t border-white/5 space-y-1.5">
                <div className="flex items-center gap-1 bg-surface-panel p-1.5 rounded border border-white/5 overflow-x-auto">
                  <button
                    type="button"
                    onClick={() => onPlateEndingChange(null)}
                    className={`px-2 py-1 text-[11px] font-mono font-semibold rounded transition cursor-pointer ${
                      plateEnding === null
                        ? "bg-ai-primary text-white border border-ai-primary"
                        : "bg-surface-elevated/40 text-text-muted hover:text-white"
                    }`}
                  >
                    Any
                  </button>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map((digit) => {
                    const isSelected = plateEnding === digit;
                    const isCoded = todayCodedDigits.includes(digit);
                    return (
                      <button
                        key={digit}
                        type="button"
                        onClick={() => onPlateEndingChange(isSelected ? null : digit)}
                        className={`flex-1 min-w-[24px] py-1 text-xs font-mono font-bold rounded text-center transition cursor-pointer ${
                          isSelected
                            ? "bg-ai-primary text-white border border-ai-cyan shadow-sm"
                            : isCoded
                            ? "bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25"
                            : "bg-surface-elevated/40 text-text-secondary hover:text-white hover:bg-surface-elevated"
                        }`}
                        title={isCoded ? `Plate ending in ${digit} is coded today` : `Plate ending in ${digit}`}
                      >
                        {digit}
                      </button>
                    );
                  })}
                </div>
                <div className="flex items-center justify-between text-[10px] text-text-muted px-0.5">
                  <span>Window: 7-10 AM, 5-8 PM</span>
                  <span>Makati: 7 AM-7 PM</span>
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* Action Button */}
      <button
        onClick={onAnalyze}
        disabled={isLoading}
        className="w-full bg-ai-primary hover:bg-indigo-600 active:scale-[0.99] text-white font-outfit font-semibold py-2.5 px-4 rounded-lg transition flex items-center justify-center gap-2 shadow-active-glow disabled:opacity-50 text-sm cursor-pointer"
      >
        <span className="material-symbols-outlined text-[18px]">
          {isLoading ? "hourglass_top" : "insights"}
        </span>
        <span>{isLoading ? "Analyzing NCR Telemetry..." : "Analyze Route Intelligence"}</span>
      </button>
    </div>
  );
};

