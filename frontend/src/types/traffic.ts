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
  clearance_minutes?: number;
  p10_clearance_mins?: number;
  p50_clearance_mins?: number;
  p90_clearance_mins?: number;
  clearance_window_display?: string;
  confidence_score?: number;
  confidence_tier?: string;
  tow_dispatch_status?: string;
  lanes_blocked?: number;
  road_width_lanes?: number;
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
  confidence_interval?: string;
  p10_optimistic_mins?: number;
  p50_median_mins?: number;
  p90_pessimistic_mins?: number;
  relief_window_display?: string;
  model_version?: string;
  is_predicted: boolean;
}

export interface TollCostBenefit {
  toll_fee_php: number;
  time_saved_min: number;
  cost_per_min_saved?: number | null;
  comparison_route_name?: string | null;
  is_zero_toll: boolean;
}

export interface DelayDecomposition {
  incident_delay_min: number;
  baseline_congestion_min: number;
  weather_delay_min: number;
  total_delay_min: number;
  primary_cause: "INCIDENT" | "RUSH_HOUR_VOLUME" | "MONSOON_FLOOD" | "NORMAL_FLOW" | string;
  cause_details: string;
}

export interface NumberCodingAdvisory {
  is_coding_active: boolean;
  is_restricted: boolean;
  plate_ending?: number | null;
  restricted_hours: string;
  restricted_day: string;
  has_window_hours: boolean;
  window_hours: string;
  message: string;
  affected_corridors: string[];
}

export interface FloodHazardDetail {
  id: string;
  corridor: string;
  city: string;
  water_depth: "GUTTER_DEEP" | "HALF_TIRE" | "TIRE_DEEP" | "SUBMERGED" | string;
  passable_to_light: boolean;
  description?: string;
  distance_meters?: number;
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
  badge?: "LEAST_TRAFFIC" | "SHORTEST_PATH" | "LEAST_TRAFFIC_AND_SHORTEST" | "ALTERNATIVE" | string;
  distance_diff_km?: number;
  time_diff_min?: number;
  summary: RouteSummary;
  expected_relief: ExpectedRelief;
  geometry: RouteGeometry;
  segments: RouteSegmentDetail[];
  toll_fee_php?: number;
  toll_cost_benefit?: TollCostBenefit;
  delay_decomposition?: DelayDecomposition;
  coding_advisory?: NumberCodingAdvisory;
  flood_hazards?: FloodHazardDetail[];
  is_impassable_flood?: boolean;
  spillover_warnings?: string[];
  spillover_segments?: string[];
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
  corridor?: string;
  confidence?: number;
  report_count?: number;
  still_there_votes?: number;
  cleared_votes?: number;
  reporter_token?: string;
  clearance_minutes?: number;
  p10_clearance_mins?: number;
  p50_clearance_mins?: number;
  p90_clearance_mins?: number;
  clearance_window_display?: string;
  confidence_score?: number;
  confidence_tier?: string;
  tow_dispatch_status?: string;
  lanes_blocked?: number;
  road_width_lanes?: number;
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
