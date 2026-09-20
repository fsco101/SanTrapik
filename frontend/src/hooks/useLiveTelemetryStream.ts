import { useState, useEffect, useRef, useCallback } from "react";
import type { IncidentItem, DashboardStats } from "../types/traffic";
import type {
  TelemetryConnectionStatus,
  ViewportBBox,
  VelocityShiftDelta,
  RouteObstructionAlert,
} from "../types/streaming";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000/api/v1";

interface UseLiveTelemetryStreamOptions {
  bbox?: ViewportBBox | null;
  routeId?: string | null;
  onIncidentUpdate?: (incident: IncidentItem) => void;
  onVelocityShift?: (deltas: VelocityShiftDelta[]) => void;
  onRouteAlert?: (alert: RouteObstructionAlert) => void;
  onStatsUpdate?: (stats: DashboardStats) => void;
}

export function useLiveTelemetryStream({
  bbox = null,
  routeId = null,
  onIncidentUpdate,
  onVelocityShift,
  onRouteAlert,
  onStatsUpdate,
}: UseLiveTelemetryStreamOptions = {}) {
  const [status, setStatus] = useState<TelemetryConnectionStatus>("connecting");
  const [lastEventTime, setLastEventTime] = useState<Date>(new Date());
  const [freshnessText, setFreshnessText] = useState<string>("Connecting live...");

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef<number>(0);
  const clientIdRef = useRef<string | null>(null);
  const isUnmountedRef = useRef<boolean>(false);

  // Keep latest callbacks and params in refs to avoid re-triggering connection on prop changes
  const onIncidentUpdateRef = useRef(onIncidentUpdate);
  const onVelocityShiftRef = useRef(onVelocityShift);
  const onRouteAlertRef = useRef(onRouteAlert);
  const onStatsUpdateRef = useRef(onStatsUpdate);
  const bboxRef = useRef(bbox);
  const routeIdRef = useRef(routeId);
  const lastSentSubRef = useRef<{ bbox: ViewportBBox | null; routeId: string | null }>({
    bbox: null,
    routeId: null,
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    onIncidentUpdateRef.current = onIncidentUpdate;
    onVelocityShiftRef.current = onVelocityShift;
    onRouteAlertRef.current = onRouteAlert;
    onStatsUpdateRef.current = onStatsUpdate;
    bboxRef.current = bbox;
    routeIdRef.current = routeId;
  }, [onIncidentUpdate, onVelocityShift, onRouteAlert, onStatsUpdate, bbox, routeId]);

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;

    // Clean previous connection and timer
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setStatus("connecting");

    // Construct stream URL with viewport and route parameters
    const params = new URLSearchParams();
    const curBbox = bboxRef.current;
    const curRouteId = routeIdRef.current;
    if (curBbox) {
      params.append("min_lng", curBbox.min_lng.toFixed(5));
      params.append("min_lat", curBbox.min_lat.toFixed(5));
      params.append("max_lng", curBbox.max_lng.toFixed(5));
      params.append("max_lat", curBbox.max_lat.toFixed(5));
    }
    if (curRouteId) {
      params.append("route_id", curRouteId);
    }
    if (clientIdRef.current) {
      params.append("client_id", clientIdRef.current);
    }

    const streamUrl = `${API_BASE}/telemetry/stream?${params.toString()}`;
    const es = new EventSource(streamUrl);
    eventSourceRef.current = es;

    es.onopen = () => {
      if (isUnmountedRef.current) return;
      setStatus("connected");
      retryCountRef.current = 0;
      setLastEventTime(new Date());
    };

    // 1. Connection established handshake
    es.addEventListener("connection_established", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        if (data.client_id) {
          clientIdRef.current = data.client_id;
        }
        setStatus("connected");
        setLastEventTime(new Date());
      } catch (err) {
        console.warn("Malformed handshake packet:", err);
      }
    });

    // 2. Incident updates
    es.addEventListener("incident_update", (e: MessageEvent) => {
      try {
        const raw = JSON.parse(e.data);
        setLastEventTime(new Date());
        if (onIncidentUpdateRef.current) {
          const item: IncidentItem = {
            id: raw.id,
            incident_type: raw.incident_type,
            description: raw.description,
            severity: raw.severity,
            status: raw.status,
            lat: raw.lat ?? raw.point_lng_lat?.[1],
            lng: raw.lng ?? raw.point_lng_lat?.[0],
            reported_at: raw.reported_at,
            data_source: raw.data_source,
            corridor: raw.corridor,
            confidence: raw.confidence,
            report_count: raw.report_count,
            still_there_votes: raw.still_there_votes,
            cleared_votes: raw.cleared_votes,
            reporter_token: raw.reporter_token,
          };
          onIncidentUpdateRef.current(item);
        }
      } catch (err) {
        console.warn("Failed to parse incident_update:", err);
      }
    });

    // 3. Velocity shifts
    es.addEventListener("velocity_shift", (e: MessageEvent) => {
      try {
        const raw = JSON.parse(e.data);
        const deltas = Array.isArray(raw) ? raw : (raw.deltas || []);
        setLastEventTime(new Date());
        if (onVelocityShiftRef.current && Array.isArray(deltas)) {
          onVelocityShiftRef.current(deltas);
        }
      } catch (err) {
        console.warn("Failed to parse velocity_shift:", err);
      }
    });

    // 4. Route corridor obstruction alert
    es.addEventListener("route_obstruction", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setLastEventTime(new Date());
        if (onRouteAlertRef.current) {
          onRouteAlertRef.current(data);
        }
      } catch (err) {
        console.warn("Failed to parse route_obstruction:", err);
      }
    });

    // 5. Aggregate stats update
    es.addEventListener("stats_update", (e: MessageEvent) => {
      try {
        const stats = JSON.parse(e.data);
        setLastEventTime(new Date());
        if (onStatsUpdateRef.current) {
          onStatsUpdateRef.current(stats);
        }
      } catch (err) {
        console.warn("Failed to parse stats_update:", err);
      }
    });

    es.onerror = () => {
      if (isUnmountedRef.current) return;
      es.close();
      eventSourceRef.current = null;

      // Exponential backoff reconnection: 1s -> 2s -> 4s -> 8s -> max 16s
      const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 16000);
      retryCountRef.current += 1;

      if (retryCountRef.current > 4) {
        setStatus("offline");
      } else {
        setStatus("connecting");
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    };
  }, []); // Stable: does not close/re-open SSE stream on viewport pan/zoom

  // Initial connection and teardown
  useEffect(() => {
    isUnmountedRef.current = false;
    connect();

    return () => {
      isUnmountedRef.current = true;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [connect]);

  // Dynamic renegotiation for pan/zoom or route change without reconnection drop
  useEffect(() => {
    if (!clientIdRef.current || status !== "connected") return;

    // Check if subscription changed significantly before scheduling a network request
    const last = lastSentSubRef.current;
    const routeChanged = last.routeId !== (routeId || null);
    let bboxChanged = false;
    if (!last.bbox && bbox) {
      bboxChanged = true;
    } else if (last.bbox && !bbox) {
      bboxChanged = true;
    } else if (last.bbox && bbox) {
      const delta =
        Math.abs(bbox.min_lng - last.bbox.min_lng) +
        Math.abs(bbox.min_lat - last.bbox.min_lat) +
        Math.abs(bbox.max_lng - last.bbox.max_lng) +
        Math.abs(bbox.max_lat - last.bbox.max_lat);
      if (delta > 0.003) {
        bboxChanged = true;
      }
    }

    if (!routeChanged && !bboxChanged) {
      return;
    }

    const timer = setTimeout(() => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      fetch(`${API_BASE}/telemetry/stream/${clientIdRef.current}/subscription`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          min_lng: bbox?.min_lng,
          min_lat: bbox?.min_lat,
          max_lng: bbox?.max_lng,
          max_lat: bbox?.max_lat,
          route_id: routeId || undefined,
        }),
      })
        .then((res) => {
          if (res.ok) {
            lastSentSubRef.current = { bbox, routeId: routeId || null };
          } else if (res.status === 429) {
            console.warn("Telemetry subscription throttled (429), pausing updates");
          }
        })
        .catch((err) => {
          if (err.name !== "AbortError") {
            console.warn("Failed to dynamically update SSE subscription bounds:", err);
          }
        });
    }, 500);

    return () => clearTimeout(timer);
  }, [bbox, routeId, status]);

  // Relative timestamp ticker
  useEffect(() => {
    const updateTicker = () => {
      if (status === "connecting") {
        setFreshnessText("Reconnecting...");
        return;
      }
      if (status === "offline") {
        setFreshnessText("Offline Cache");
        return;
      }

      const diffSec = Math.floor((Date.now() - lastEventTime.getTime()) / 1000);
      if (diffSec < 10) {
        setFreshnessText("Live Stream");
      } else if (diffSec < 60) {
        setFreshnessText(`Streamed ${diffSec}s ago`);
      } else {
        const mins = Math.floor(diffSec / 60);
        setFreshnessText(`Streamed ${mins}m ago`);
      }
    };

    updateTicker();
    const interval = setInterval(updateTicker, 3000);
    return () => clearInterval(interval);
  }, [lastEventTime, status]);

  return {
    status,
    isOnline: status === "connected",
    lastEventTime,
    freshnessText,
    reconnect: connect,
  };
}
