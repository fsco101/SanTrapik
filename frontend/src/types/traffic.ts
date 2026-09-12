export type TrafficLevel = "NORMAL" | "MODERATE" | "HEAVY" | "SEVERE";
export type TransportMode = "car" | "motorcycle" | "jeepney" | "walking";

export interface Coordinate {
  lat: float;
  lng: float;
  name?: string;
}

export interface PlaceSuggestion {
  name: string;
  display_name: string;
  city?: string;
  lat: number;
  lng: number;
}

export type float = number;

export interface IncidentSummary {
  id: string;
  type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  description?: string;
  reported_at: string;
  status: string;
}

export interface SegmentPrediction {
  predicted_relief_time: string;
  predicted_relief_minutes: number;
  confidence: number;
}

export interface RouteSegmentDetail {
  segment_id: string;
  name: string;
  road_code?: string;
  direction: string;
  traffic_level: TrafficLevel;
  average_speed_kmh: number;
  congestion_percentage: number;
  incidents: IncidentSummary[];
  prediction?: SegmentPrediction;
  last_updated: string;
}

export interface RouteSummary {
  total_distance_km: number;
  estimated_travel_time_min: number;
  normal_travel_time_min: number;
  estimated_delay_min: number;
  overall_congestion: TrafficLevel;
  active_incidents_count: number;
  most_affected_segment: string;
}

export interface ExpectedRelief {
  relief_time: string;
  estimated_minutes_remaining: number;
  confidence: number;
  is_predicted: boolean;
}

export interface RouteGeometry {
  type: "LineString";
  coordinates: [number, number][];
}

export interface RouteItem {
  id: string;
  name: string;
  is_recommended: boolean;
  recommendation_reason?: string;
  summary: RouteSummary;
  expected_relief: ExpectedRelief;
  geometry: RouteGeometry;
  segments: RouteSegmentDetail[];
}

export interface IncidentItem {
  id: string;
  incident_type: string;
  description?: string;
  severity: string;
  status: string;
  lat: number;
  lng: number;
  reported_at: string;
  data_source: string;
}

export interface CorridorCongestion {
  road_name: string;
  traffic_level: TrafficLevel;
  congestion_percentage: number;
  average_speed_kmh: number;
  expected_relief: string;
}

export interface DashboardStats {
  active_incidents: number;
  severe_roads_count: number;
  moderate_roads_count: number;
  average_road_speed_kmh: number;
  most_congested_roads: CorridorCongestion[];
}
