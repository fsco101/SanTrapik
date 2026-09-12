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
    // Don't search if the query is already the selected place name
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
    // Don't search if the query is already the selected place name
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

  return (
    <div className="bg-surface-panel rounded-lg p-3 border border-white/10 space-y-3">
      <div className="relative space-y-2">
        {/* Origin Field with Autocomplete */}
        <div ref={originContainerRef} className="relative">
          <div className="flex items-center gap-2 bg-surface-card rounded px-3 py-2 border border-white/5 focus-within:border-ai-primary focus-within:shadow-active-glow transition">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0"></span>
            <div className="flex-1 min-w-0">
              <span className="text-[9px] uppercase font-bold text-text-muted tracking-wider block font-mono">
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
                placeholder="Search any place, mall, street in Metro Manila..."
                className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none font-sans truncate"
              />
            </div>
            {isOriginLoading && (
              <span className="material-symbols-outlined text-[15px] text-text-muted animate-spin">
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
                className="text-text-muted hover:text-white"
              >
                <span className="material-symbols-outlined text-[15px]">close</span>
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
                  className="w-full text-left px-3 py-2.5 hover:bg-ai-primary/20 hover:border-l-2 hover:border-ai-primary flex items-start gap-2.5 transition text-xs group"
                >
                  <span className="material-symbols-outlined text-emerald-400 text-[16px] mt-0.5 shrink-0 group-hover:scale-110 transition">
                    location_on
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-text-primary group-hover:text-white truncate">
                      {place.name}
                    </p>
                    <p className="text-[10px] text-text-muted truncate mt-0.5">
                      {place.display_name}
                    </p>
                  </div>
                  {place.city && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-text-secondary shrink-0 border border-white/5">
                      {place.city}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
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

        {/* Destination Field with Autocomplete */}
        <div ref={destContainerRef} className="relative">
          <div className="flex items-center gap-2 bg-surface-card rounded px-3 py-2 border border-white/5 focus-within:border-ai-primary focus-within:shadow-active-glow transition">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0"></span>
            <div className="flex-1 min-w-0">
              <span className="text-[9px] uppercase font-bold text-text-muted tracking-wider block font-mono">
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
                placeholder="Search any place, mall, street in Metro Manila..."
                className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none font-sans truncate"
              />
            </div>
            {isDestLoading && (
              <span className="material-symbols-outlined text-[15px] text-text-muted animate-spin">
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
                className="text-text-muted hover:text-white"
              >
                <span className="material-symbols-outlined text-[15px]">close</span>
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
                  className="w-full text-left px-3 py-2.5 hover:bg-ai-primary/20 hover:border-l-2 hover:border-ai-primary flex items-start gap-2.5 transition text-xs group"
                >
                  <span className="material-symbols-outlined text-rose-400 text-[16px] mt-0.5 shrink-0 group-hover:scale-110 transition">
                    flag
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-text-primary group-hover:text-white truncate">
                      {place.name}
                    </p>
                    <p className="text-[10px] text-text-muted truncate mt-0.5">
                      {place.display_name}
                    </p>
                  </div>
                  {place.city && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-text-secondary shrink-0 border border-white/5">
                      {place.city}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 2. Transport Mode Selector (Street-Smart Commuter Options) */}
      <div className="space-y-1.5 pt-1">
        <span className="text-[9px] uppercase font-bold text-text-muted tracking-wider block font-mono">
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
                  // Automatic street-smart enforcement: motorcycles & walking cannot take expressways
                  if (mode.id === "motorcycle" || mode.id === "walking") {
                    onUseExpresswayChange(false);
                  }
                }}
                className={`flex flex-col items-center justify-center py-2 px-1 rounded transition border ${
                  isSelected
                    ? "bg-ai-primary/25 border-ai-primary text-white shadow-ai-aura"
                    : "bg-surface-elevated/40 border-transparent text-text-secondary hover:text-white hover:bg-surface-elevated"
                }`}
              >
                <span className={`material-symbols-outlined text-[18px] ${isSelected ? "text-ai-cyan scale-110" : ""}`}>
                  {mode.icon}
                </span>
                <span className="text-[11px] font-semibold mt-1 truncate max-w-full">
                  {mode.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Expressway Route Choice (Skyway / Tollway Toggle) */}
      <div className="flex items-center justify-between bg-surface-card rounded px-3 py-2 border border-white/5">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-amber-400">
            toll
          </span>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold text-text-primary">
                Expressway / Skyway
              </span>
              {transportMode === "motorcycle" && (
                <span className="text-[9px] font-mono px-1 py-0.2 bg-rose-500/20 text-rose-300 rounded border border-rose-500/30">
                  Sub-400cc Restricted
                </span>
              )}
              {transportMode === "walking" && (
                <span className="text-[9px] font-mono px-1 py-0.2 bg-slate-700 text-slate-300 rounded">
                  No Pedestrians
                </span>
              )}
            </div>
            <p className="text-[10px] text-text-muted">
              {transportMode === "motorcycle"
                ? "PH law bars standard motorbikes from Skyway/SLEX/NLEX"
                : transportMode === "walking"
                ? "Pedestrians routed strictly via sidewalks & footbridges"
                : useExpressway
                ? "Using Skyway / Tollways for fastest bypass"
                : "Avoid tolls: Surface arterial roads only (EDSA / C-5)"}
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

      {/* Action Button */}
      <button
        onClick={onAnalyze}
        disabled={isLoading}
        className="w-full bg-ai-primary hover:bg-indigo-600 active:scale-[0.99] text-white font-outfit font-semibold py-2.5 px-4 rounded transition flex items-center justify-center gap-2 shadow-active-glow disabled:opacity-50 text-sm cursor-pointer"
      >
        <span className="material-symbols-outlined text-[18px]">
          {isLoading ? "hourglass_top" : "insights"}
        </span>
        <span>{isLoading ? "Analyzing NCR Telemetry..." : "Analyze Route Intelligence"}</span>
      </button>
    </div>
  );
};
