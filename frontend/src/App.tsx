import { useState, useEffect } from "react";
import { Header } from "./components/layout/Header";
import { QuickCorridors, CORRIDORS } from "./components/route/QuickCorridors";
import type { QuickCorridorItem } from "./components/route/QuickCorridors";
import { RouteSearch } from "./components/route/RouteSearch";
import { RouteIntelligenceCard } from "./components/telemetry/RouteIntelligenceCard";
import { RouteComparison } from "./components/route/RouteComparison";
import { MapContainer } from "./components/map/MapContainer";
import { BottomTelemetrySheet } from "./components/layout/BottomTelemetrySheet";
import type { Coordinate, RouteItem, DashboardStats, IncidentItem } from "./types/traffic";
import { analyzeRoute, getDashboardStats, getIncidents } from "./services/api";
import { useTrafficRefresh } from "./hooks/useTrafficRefresh";

export function App() {
  const [origin, setOrigin] = useState<Coordinate>(CORRIDORS[0].origin);
  const [destination, setDestination] = useState<Coordinate>(CORRIDORS[0].destination);
  const [activeCorridor, setActiveCorridor] = useState<string | null>(CORRIDORS[0].name);

  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<string>("");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [heatmapVisible, setHeatmapVisible] = useState<boolean>(false);

  // Background telemetry polling every 60s
  const { isOnline, freshnessText, refreshData } = useTrafficRefresh({
    intervalMs: 60000,
    onRefreshStats: setStats,
    onRefreshIncidents: setIncidents,
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
        analyzeRoute(origin, destination, true)
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

  const handleSelectCorridor = (item: QuickCorridorItem) => {
    setActiveCorridor(item.name);
    setOrigin(item.origin);
    setDestination(item.destination);
    triggerAnalyze(item.origin, item.destination);
  };

  const handleSwap = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
    triggerAnalyze(destination, temp);
  };

  const triggerAnalyze = async (orig = origin, dest = destination) => {
    setIsLoading(true);
    try {
      const fetchedRoutes = await analyzeRoute(orig, dest, true);
      setRoutes(fetchedRoutes);
      if (fetchedRoutes.length > 0) {
        setSelectedRouteId(fetchedRoutes[0].id);
      }
      refreshData();
    } finally {
      setIsLoading(false);
    }
  };

  const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0] || null;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-surface-bg text-text-primary">
      {/* 1. Header */}
      <Header
        stats={stats}
        isLoading={isLoading}
        onRefresh={() => triggerAnalyze()}
        freshnessText={freshnessText}
        isOnline={isOnline}
      />

      {/* Offline Notice Banner */}
      {!isOnline && (
        <div className="bg-amber-500/15 border-b border-amber-500/30 text-amber-300 text-xs px-4 py-1.5 flex items-center justify-between font-mono z-30">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            Backend API offline: Displaying pre-computed Metro Manila corridor telemetry.
          </span>
          <button
            onClick={() => refreshData()}
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
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onSwap={handleSwap}
            onAnalyze={() => triggerAnalyze()}
            isLoading={isLoading}
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
            incidents={incidents}
            heatmapVisible={heatmapVisible}
            onToggleHeatmap={() => setHeatmapVisible(!heatmapVisible)}
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
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onSwap={handleSwap}
            onAnalyze={() => triggerAnalyze()}
            isLoading={isLoading}
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
    </div>
  );
}

export default App;
