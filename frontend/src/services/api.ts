import type { RouteItem, DashboardStats, IncidentItem, PlaceSuggestion, TransportMode } from "../types/traffic";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000/api/v1";

export async function searchPlaces(query: string): Promise<PlaceSuggestion[]> {
  if (!query || query.trim().length === 0) return [];
  try {
    const res = await fetch(`${API_BASE}/places/search?q=${encodeURIComponent(query.trim())}&limit=8`);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn("Backend places search failed, falling back to client-side Nominatim:", err);
  }

  // Resilient direct fallback to Nominatim (bounded to NCR)
  try {
    const directRes = await fetch(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&viewbox=120.90,14.80,121.15,14.35&bounded=1&format=json&countrycodes=ph&limit=8`,
      { headers: { Accept: "application/json" } }
    );
    if (directRes.ok) {
      const data = await directRes.json();
      return data.map((item: any) => {
        const parts = item.display_name.split(",").map((s: string) => s.trim());
        return {
          name: parts[0] || query,
          display_name: item.display_name,
          city: parts.length > 1 ? parts[1] : "Metro Manila",
          lat: parseFloat(item.lat),
          lng: parseFloat(item.lon)
        };
      });
    }
  } catch (err) {
    console.error("Direct Nominatim search failed:", err);
  }
  return [];
}

export async function analyzeRoute(
  origin: { lat: number; lng: number; name?: string },
  destination: { lat: number; lng: number; name?: string },
  includeAlternatives: boolean = true,
  transportMode: TransportMode = "car",
  useExpressway: boolean = true
): Promise<RouteItem[]> {
  try {
    const res = await fetch(`${API_BASE}/route/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        origin,
        destination,
        include_alternatives: includeAlternatives,
        transport_mode: transportMode,
        use_expressway: useExpressway
      }),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const json = await res.json();
    return json.data.routes;
  } catch (err) {
    console.warn("Backend API route analyze call failed, querying direct OSRM route:", err);
    try {
      const osrmRes = await fetch(
        `https://router.project-osrm.org/route/v1/driving/${origin.lng},${origin.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson&alternatives=${includeAlternatives}`
      );
      if (osrmRes.ok) {
        const osrmData = await osrmRes.json();
        if (osrmData.routes && osrmData.routes.length > 0) {
          return osrmData.routes.map((r: any, idx: number) => {
            const distKm = Number((r.distance / 1000).toFixed(1));
            const ttMin = Math.round(r.duration / 60);
            return {
              id: `rt_osrm_direct_${idx + 1}`,
              name: idx === 0 ? "via Primary Corridor" : "via Alternate Route",
              is_recommended: idx === 0,
              recommendation_reason: idx === 0 ? "Real-time OSRM optimal path" : "Alternative route",
              summary: {
                total_distance_km: distKm,
                estimated_travel_time_min: ttMin,
                normal_travel_time_min: Math.round((distKm / 50) * 60),
                estimated_delay_min: Math.max(0, ttMin - Math.round((distKm / 50) * 60)),
                overall_congestion: "MODERATE",
                active_incidents_count: 0,
                most_affected_segment: "NCR Arterial"
              },
              expected_relief: {
                relief_time: new Date(Date.now() + 25 * 60000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                estimated_minutes_remaining: 25,
                confidence: 0.85,
                is_predicted: true
              },
              geometry: r.geometry,
              segments: []
            };
          });
        }
      }
    } catch (osrmErr) {
      console.error("OSRM direct query failed:", osrmErr);
    }
    return getFallbackRoutes(origin.name || "Quezon City", destination.name || "Makati");
  }
}

export async function getDashboardStats(): Promise<DashboardStats> {
  try {
    const res = await fetch(`${API_BASE}/dashboard/stats`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const json = await res.json();
    return json.data;
  } catch (err) {
    return {
      active_incidents: 27,
      severe_roads_count: 14,
      moderate_roads_count: 31,
      average_road_speed_kmh: 18.4,
      most_congested_roads: [
        { road_name: "EDSA - Ortigas Flyover SB", traffic_level: "SEVERE", congestion_percentage: 91.5, average_speed_kmh: 11.2, expected_relief: "10:42 PM" },
        { road_name: "C-5 - Bagong Ilog Flyover", traffic_level: "SEVERE", congestion_percentage: 86.0, average_speed_kmh: 14.5, expected_relief: "11:05 PM" },
        { road_name: "Commonwealth - Philcoa to Circle", traffic_level: "HEAVY", congestion_percentage: 73.0, average_speed_kmh: 24.0, expected_relief: "10:18 PM" },
        { road_name: "España Boulevard - Welcome to UST", traffic_level: "HEAVY", congestion_percentage: 69.0, average_speed_kmh: 18.5, expected_relief: "10:30 PM" }
      ]
    };
  }
}

export async function getIncidents(): Promise<IncidentItem[]> {
  try {
    const res = await fetch(`${API_BASE}/incidents?status=ACTIVE`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const json = await res.json();
    return json.data;
  } catch (err) {
    return [
      {
        id: "inc_9821",
        incident_type: "ACCIDENT",
        description: "2-vehicle collision occupying 2 middle lanes",
        severity: "CRITICAL",
        status: "ACTIVE",
        lat: 14.5855,
        lng: 121.0575,
        reported_at: new Date().toISOString(),
        data_source: "MMDA_METROBASE"
      },
      {
        id: "inc_9822",
        incident_type: "ROADWORK",
        description: "DPWH asphalt re-blocking; 1 lane passable",
        severity: "HIGH",
        status: "ACTIVE",
        lat: 14.5740,
        lng: 121.0690,
        reported_at: new Date().toISOString(),
        data_source: "DPWH_NCR"
      }
    ];
  }
}

function getFallbackRoutes(_originName: string, _destName: string): RouteItem[] {
  return [
    {
      id: "rt_primary_edsa",
      name: "via EDSA Corridor",
      is_recommended: false,
      summary: {
        total_distance_km: 15.4,
        estimated_travel_time_min: 84,
        normal_travel_time_min: 52,
        estimated_delay_min: 32,
        overall_congestion: "SEVERE",
        active_incidents_count: 2,
        most_affected_segment: "EDSA - Ortigas Flyover SB"
      },
      expected_relief: {
        relief_time: "10:20 PM",
        estimated_minutes_remaining: 38,
        confidence: 0.82,
        is_predicted: true
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [121.0494, 14.6515],
          [121.0421, 14.6415],
          [121.0482, 14.6305],
          [121.0545, 14.6185],
          [121.0580, 14.5885],
          [121.0465, 14.5695],
          [121.0315, 14.5540],
          [121.0234, 14.5573]
        ]
      },
      segments: [
        {
          segment_id: "seg_edsa_01",
          name: "EDSA - Quezon Avenue to Cubao",
          road_code: "C-4",
          direction: "SB",
          traffic_level: "HEAVY",
          average_speed_kmh: 22.5,
          congestion_percentage: 55.0,
          incidents: [],
          prediction: { predicted_relief_time: "10:05 PM", predicted_relief_minutes: 25, confidence: 0.80 },
          last_updated: "9:52 PM"
        },
        {
          segment_id: "seg_edsa_02",
          name: "EDSA - Ortigas Flyover SB",
          road_code: "C-4",
          direction: "SB",
          traffic_level: "SEVERE",
          average_speed_kmh: 11.2,
          congestion_percentage: 91.5,
          incidents: [
            {
              id: "inc_9821",
              type: "ACCIDENT",
              severity: "CRITICAL",
              description: "2-vehicle collision occupying 2 middle lanes; wrecker on scene",
              reported_at: "9:42 PM",
              status: "ACTIVE"
            }
          ],
          prediction: { predicted_relief_time: "10:20 PM", predicted_relief_minutes: 38, confidence: 0.82 },
          last_updated: "9:54 PM"
        },
        {
          segment_id: "seg_edsa_03",
          name: "EDSA - Guadalupe to Buendia",
          road_code: "C-4",
          direction: "SB",
          traffic_level: "HEAVY",
          average_speed_kmh: 18.0,
          congestion_percentage: 64.0,
          incidents: [],
          prediction: { predicted_relief_time: "10:10 PM", predicted_relief_minutes: 28, confidence: 0.76 },
          last_updated: "9:53 PM"
        },
        {
          segment_id: "seg_edsa_04",
          name: "EDSA - Buendia to Ayala Avenue",
          road_code: "C-4",
          direction: "SB",
          traffic_level: "NORMAL",
          average_speed_kmh: 48.0,
          congestion_percentage: 12.0,
          incidents: [],
          prediction: { predicted_relief_time: "10:00 PM", predicted_relief_minutes: 10, confidence: 0.90 },
          last_updated: "9:55 PM"
        }
      ]
    },
    {
      id: "rt_alt_c5",
      name: "via C-5 Road Corridor",
      is_recommended: true,
      recommendation_reason: "Saves 16 minutes with rolling traffic and fewer active lane closures",
      summary: {
        total_distance_km: 17.1,
        estimated_travel_time_min: 68,
        normal_travel_time_min: 52,
        estimated_delay_min: 16,
        overall_congestion: "HEAVY",
        active_incidents_count: 1,
        most_affected_segment: "C-5 - Bagong Ilog Flyover"
      },
      expected_relief: {
        relief_time: "10:05 PM",
        estimated_minutes_remaining: 22,
        confidence: 0.78,
        is_predicted: true
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [121.0494, 14.6515],
          [121.0745, 14.6560],
          [121.0790, 14.6225],
          [121.0755, 14.5890],
          [121.0665, 14.5685],
          [121.0585, 14.5510],
          [121.0234, 14.5573]
        ]
      },
      segments: [
        {
          segment_id: "seg_c5_01",
          name: "C-5 - Katipunan to Eastwood Libis",
          road_code: "C-5",
          direction: "SB",
          traffic_level: "MODERATE",
          average_speed_kmh: 38.0,
          congestion_percentage: 35.0,
          incidents: [],
          prediction: { predicted_relief_time: "10:00 PM", predicted_relief_minutes: 15, confidence: 0.85 },
          last_updated: "9:54 PM"
        },
        {
          segment_id: "seg_c5_02",
          name: "C-5 - Bagong Ilog Flyover",
          road_code: "C-5",
          direction: "SB",
          traffic_level: "HEAVY",
          average_speed_kmh: 24.5,
          congestion_percentage: 68.0,
          incidents: [
            {
              id: "inc_9822",
              type: "ROADWORK",
              severity: "HIGH",
              description: "DPWH asphalt re-blocking; outer lane affected",
              reported_at: "8:00 PM",
              status: "ACTIVE"
            }
          ],
          prediction: { predicted_relief_time: "10:05 PM", predicted_relief_minutes: 22, confidence: 0.78 },
          last_updated: "9:52 PM"
        }
      ]
    }
  ];
}
