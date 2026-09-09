import { useState, useEffect, useCallback } from "react";
import { getDashboardStats, getIncidents } from "../services/api";
import type { DashboardStats, IncidentItem } from "../types/traffic";

interface UseTrafficRefreshOptions {
  intervalMs?: number;
  onRefreshStats?: (stats: DashboardStats) => void;
  onRefreshIncidents?: (incidents: IncidentItem[]) => void;
}

export function useTrafficRefresh({
  intervalMs = 60000,
  onRefreshStats,
  onRefreshIncidents,
}: UseTrafficRefreshOptions = {}) {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [freshnessText, setFreshnessText] = useState<string>("Updated just now");

  const refreshData = useCallback(async () => {
    try {
      const [stats, incs] = await Promise.all([
        getDashboardStats(),
        getIncidents(),
      ]);
      if (onRefreshStats) onRefreshStats(stats);
      if (onRefreshIncidents) onRefreshIncidents(incs);
      setIsOnline(true);
      setLastUpdated(new Date());
    } catch (err) {
      console.warn("Background telemetry polling failed:", err);
      setIsOnline(false);
    }
  }, [onRefreshStats, onRefreshIncidents]);

  // Periodic polling interval
  useEffect(() => {
    const timer = setInterval(() => {
      refreshData();
    }, intervalMs);

    return () => clearInterval(timer);
  }, [refreshData, intervalMs]);

  // Relative timestamp ticker every 5 seconds
  useEffect(() => {
    const updateTicker = () => {
      const diffSec = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);
      if (diffSec < 15) {
        setFreshnessText("Updated just now");
      } else if (diffSec < 60) {
        setFreshnessText(`Updated ${diffSec}s ago`);
      } else {
        const mins = Math.floor(diffSec / 60);
        setFreshnessText(`Updated ${mins}m ago`);
      }
    };

    updateTicker();
    const ticker = setInterval(updateTicker, 5000);
    return () => clearInterval(ticker);
  }, [lastUpdated]);

  return {
    isOnline,
    lastUpdated,
    freshnessText,
    refreshData,
  };
}
