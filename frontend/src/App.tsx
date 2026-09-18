import { useState, useEffect } from "react";
import { Header } from "./components/layout/Header";
import { QuickCorridors, CORRIDORS } from "./components/route/QuickCorridors";
import type { QuickCorridorItem } from "./components/route/QuickCorridors";
import { RouteSearch } from "./components/route/RouteSearch";
import { RouteIntelligenceCard } from "./components/telemetry/RouteIntelligenceCard";
import { RouteComparison } from "./components/route/RouteComparison";
import { MapContainer } from "./components/map/MapContainer";
import { BottomTelemetrySheet } from "./components/layout/BottomTelemetrySheet";
import { IncidentReportModal } from "./components/incident/IncidentReportModal";
import type { Coordinate, RouteItem, DashboardStats, IncidentItem, TransportMode } from "./types/traffic";
import type { VelocityShiftDelta, ViewportBBox, RouteObstructionAlert } from "./types/streaming";
import { analyzeRoute, getDashboardStats, getIncidents, resolveLiveIncident } from "./services/api";
import { useLiveTelemetryStream } from "./hooks/useLiveTelemetryStream";

export function App() {
  const [origin, setOrigin] = useState<Coordinate>(CORRIDORS[0].origin);
  const [destination, setDestination] = useState<Coordinate>(CORRIDORS[0].destination);
  const [activeCorridor, setActiveCorridor] = useState<string | null>(CORRIDORS[0].name);
  const [transportMode, setTransportMode] = useState<TransportMode>("car");
  const [useExpressway, setUseExpressway] = useState<boolean>(true);
  const [plateEnding, setPlateEnding] = useState<number | null>(null);

  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<string>("");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [heatmapVisible, setHeatmapVisible] = useState<boolean>(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);

  // Streaming states (SP7-002, SP7-003, SP7-004, SP7-005)
  const [viewportBBox, setViewportBBox] = useState<ViewportBBox | null>(null);
  const [speedDeltas, setSpeedDeltas] = useState<VelocityShiftDelta[]>([]);
  const [obstructionAlert, setObstructionAlert] = useState<RouteObstructionAlert | null>(null);

  // Persistent Server-Sent Events (SSE) telemetry stream with exponential backoff
  const {
    status: connectionStatus,
    isOnline,
    freshnessText,
    reconnect: refreshStream,
  } = useLiveTelemetryStream({
    bbox: viewportBBox,
    routeId: selectedRouteId || null,
    onIncidentUpdate: (newInc) => {
      setIncidents((prev) => [newInc, ...prev.filter((i) => i.id !== newInc.id)]);
    },
    onVelocityShift: (deltas) => {
      setSpeedDeltas(deltas);
    },
    onRouteAlert: (alert) => {
      setObstructionAlert(alert);
    },
    onStatsUpdate: (updatedStats) => {
      setStats(updatedStats);
    },
  });

  // Initial load
  useEffect(() => {
    loadInitialData();
  }, []);


  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const [statsData, incidentsData, initialRoutes] = await Promise.all([
        getDashboardStats(),
        getIncidents(),
        analyzeRoute(origin, destination, true, transportMode, useExpressway, plateEnding)
      ]);
      setStats(statsData);
      setIncidents(incidentsData);
      setRoutes(initialRoutes);
      if (initialRoutes.length > 0) {
        setSelectedRouteId(initialRoutes[0].id);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleOriginChange = (coord: Coordinate) => {
    setActiveCorridor(null);
    setOrigin(coord);
    if (coord.lat && coord.lng) {
      triggerAnalyze(coord, destination, transportMode, useExpressway, plateEnding);
    }
  };

  const handleDestinationChange = (coord: Coordinate) => {
    setActiveCorridor(null);
    setDestination(coord);
    if (coord.lat && coord.lng) {
      triggerAnalyze(origin, coord, transportMode, useExpressway, plateEnding);
    }
  };

  const handleTransportModeChange = (mode: TransportMode) => {
    setTransportMode(mode);
    const updatedExp = (mode === "motorcycle" || mode === "walking") ? false : useExpressway;
    if (mode === "motorcycle" || mode === "walking") {
      setUseExpressway(false);
    }
    triggerAnalyze(origin, destination, mode, updatedExp, plateEnding);
  };

  const handleUseExpresswayChange = (use: boolean) => {
    setUseExpressway(use);
    triggerAnalyze(origin, destination, transportMode, use, plateEnding);
  };

  const handlePlateEndingChange = (ending: number | null) => {
    setPlateEnding(ending);
    triggerAnalyze(origin, destination, transportMode, useExpressway, ending);
  };

  const handleSelectCorridor = (item: QuickCorridorItem) => {
    setActiveCorridor(item.name);
    setOrigin(item.origin);
    setDestination(item.destination);
    triggerAnalyze(item.origin, item.destination, transportMode, useExpressway, plateEnding);
  };

  const handleSwap = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
    triggerAnalyze(destination, temp, transportMode, useExpressway, plateEnding);
  };

  const triggerAnalyze = async (
    orig = origin,
    dest = destination,
    mode = transportMode,
    exp = useExpressway,
    plate = plateEnding
  ) => {
    setIsLoading(true);
    try {
      const fetchedRoutes = await analyzeRoute(orig, dest, true, mode, exp, plate);
      setRoutes(fetchedRoutes);
      if (fetchedRoutes.length > 0) {
        setSelectedRouteId(fetchedRoutes[0].id);
      }
      refreshStream();
    } finally {
      setIsLoading(false);
    }
  };

  const handleResolveIncident = async (incidentId: string) => {
    const success = await resolveLiveIncident(incidentId);
    if (success) {
      setIncidents((prev) => prev.filter((inc) => inc.id !== incidentId));
      triggerAnalyze();
    }
  };

  const handleIncidentReported = (newInc: IncidentItem) => {
    setIncidents((prev) => [newInc, ...prev.filter((i) => i.id !== newInc.id)]);
    triggerAnalyze();
  };

  const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0] || null;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-surface-bg text-text-primary">
      {/* 1. Header */}
      <Header
        stats={stats}
        isLoading={isLoading}
        onRefresh={() => {
          triggerAnalyze();
          refreshStream();
        }}
        freshnessText={freshnessText}
        isOnline={isOnline}
        connectionStatus={connectionStatus}
        onOpenReportModal={() => setIsReportModalOpen(true)}
      />

      {/* Real-Time Chokepoint Route Obstruction Flash Alert (SP7-003) */}
      {obstructionAlert && (
        <div className="bg-rose-950/95 border-b border-rose-500/50 text-white px-4 py-2 flex flex-wrap items-center justify-between gap-2 z-30 shadow-lg font-mono text-xs backdrop-blur-md animate-pulse">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-rose-400 text-[18px]">warning</span>
            <span className="font-bold text-rose-300">[ROUTE OBSTRUCTION DETECTED]</span>
            <span>
              {obstructionAlert.incident_type} on {obstructionAlert.corridor} ({obstructionAlert.distance_to_route_meters}m from corridor)
            </span>
            <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">
              +{obstructionAlert.estimated_delay_minutes}m delay
            </span>
          </div>
          <div className="flex items-center gap-2">
            {routes.length > 1 && (
              <button
                onClick={() => {
                  const alt = routes.find((r) => r.id !== selectedRouteId);
                  if (alt) {
                    setSelectedRouteId(alt.id);
                  }
                  setObstructionAlert(null);
                }}
                className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition shadow flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[15px]">alt_route</span>
                <span>Switch to Alternate Route</span>
              </button>
            )}
            <button
              onClick={() => setObstructionAlert(null)}
              className="px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-slate-300 text-xs transition"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Offline Notice Banner */}
      {!isOnline && (
        <div className="bg-amber-500/15 border-b border-amber-500/30 text-amber-300 text-xs px-4 py-1.5 flex items-center justify-between font-mono z-30">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            Backend streaming offline: Reconnecting with exponential backoff...
          </span>
          <button
            onClick={() => refreshStream()}
            className="text-[11px] underline hover:text-white"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* 2. Main Workspace Layout */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Desktop Left Telemetry Console */}
        <aside className="hidden md:flex flex-col w-[420px] shrink-0 border-r border-white/10 bg-surface-bg/95 z-20 overflow-y-auto p-4 space-y-4">
          <QuickCorridors
            activeCorridorName={activeCorridor}
            onSelect={handleSelectCorridor}
          />

          <RouteSearch
            origin={origin}
            destination={destination}
            onOriginChange={handleOriginChange}
            onDestinationChange={handleDestinationChange}
            onSwap={handleSwap}
            onAnalyze={() => triggerAnalyze()}
            isLoading={isLoading}
            transportMode={transportMode}
            onTransportModeChange={handleTransportModeChange}
            useExpressway={useExpressway}
            onUseExpresswayChange={handleUseExpresswayChange}
            plateEnding={plateEnding}
            onPlateEndingChange={handlePlateEndingChange}
          />

          {routes.length > 1 && (
            <RouteComparison
              routes={routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
            />
          )}

          {selectedRoute && <RouteIntelligenceCard route={selectedRoute} />}
        </aside>

        {/* Interactive Map Canvas */}
        <main className="flex-1 h-full relative">
          <MapContainer
            selectedRoute={selectedRoute}
            routes={routes}
            onSelectRoute={setSelectedRouteId}
            origin={origin}
            destination={destination}
            incidents={incidents}
            heatmapVisible={heatmapVisible}
            onToggleHeatmap={() => setHeatmapVisible(!heatmapVisible)}
            speedDeltas={speedDeltas}
            onViewportChange={setViewportBBox}
            onResolveIncident={handleResolveIncident}
            onOpenReportModal={() => setIsReportModalOpen(true)}
          />
        </main>


        {/* Mobile Bottom Telemetry Sheet */}
        <BottomTelemetrySheet activeRoute={selectedRoute}>
          <QuickCorridors
            activeCorridorName={activeCorridor}
            onSelect={handleSelectCorridor}
          />

          <RouteSearch
            origin={origin}
            destination={destination}
            onOriginChange={handleOriginChange}
            onDestinationChange={handleDestinationChange}
            onSwap={handleSwap}
            onAnalyze={() => triggerAnalyze()}
            isLoading={isLoading}
            transportMode={transportMode}
            onTransportModeChange={handleTransportModeChange}
            useExpressway={useExpressway}
            onUseExpresswayChange={handleUseExpresswayChange}
            plateEnding={plateEnding}
            onPlateEndingChange={handlePlateEndingChange}
          />

          {routes.length > 1 && (
            <RouteComparison
              routes={routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
            />
          )}

          {selectedRoute && <RouteIntelligenceCard route={selectedRoute} />}
        </BottomTelemetrySheet>
      </div>

      {/* Real-Time Live Incident Reporting Modal */}
      <IncidentReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onIncidentReported={handleIncidentReported}
        defaultLocation={origin}
      />
    </div>
  );
}

export default App;
