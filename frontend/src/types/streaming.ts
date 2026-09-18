export type TelemetryConnectionStatus = "connected" | "connecting" | "offline";

export interface ViewportBBox {
  min_lng: number;
  min_lat: number;
  max_lng: number;
  max_lat: number;
}

export interface VelocityShiftDelta {
  segment_id: number;
  road_name: string;
  road_code?: string;
  direction?: string;
  current_speed_kmh: number;
  traffic_level: "NORMAL" | "MODERATE" | "HEAVY" | "SEVERE";
  congestion_percentage: number;
  traffic_color: string;
  last_updated?: string;
}

export interface RouteObstructionAlert {
  route_id: string;
  incident_id: string;
  incident_type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  corridor: string;
  description: string;
  distance_to_route_meters: number;
  estimated_delay_minutes: number;
  recommendation: string;
  can_reroute: boolean;
  timestamp: string;
}
