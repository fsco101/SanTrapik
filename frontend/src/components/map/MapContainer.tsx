import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { RouteItem, IncidentItem } from "../../types/traffic";

interface MapContainerProps {
  selectedRoute: RouteItem | null;
  incidents: IncidentItem[];
  heatmapVisible: boolean;
  onToggleHeatmap: () => void;
}

export const MapContainer: React.FC<MapContainerProps> = ({
  selectedRoute,
  incidents,
  heatmapVisible,
  onToggleHeatmap,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize MapLibre GL JS
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: [121.0405, 14.5855], // Centered around EDSA Ortigas / Metro Manila
      zoom: 12,
      pitch: 35,
      bearing: -10,
      attributionControl: false
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");

    map.on("load", () => {
      setMapLoaded(true);

      // Route Source & Layer
      map.addSource("route-source", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: []
        }
      });

      // Route Glow Layer (Indigo)
      map.addLayer({
        id: "route-glow",
        type: "line",
        source: "route-source",
        layout: {
          "line-join": "round",
          "line-cap": "round"
        },
        paint: {
          "line-color": "#6366F1",
          "line-width": 10,
          "line-opacity": 0.45,
          "line-blur": 4
        }
      });

      // Route Core Line Layer (Traffic severe/heavy highlight)
      map.addLayer({
        id: "route-line",
        type: "line",
        source: "route-source",
        layout: {
          "line-join": "round",
          "line-cap": "round"
        },
        paint: {
          "line-color": [
            "case",
            ["==", ["get", "congestion"], "SEVERE"], "#EF4444",
            ["==", ["get", "congestion"], "HEAVY"], "#F97316",
            ["==", ["get", "congestion"], "MODERATE"], "#F59E0B",
            "#10B981"
          ],
          "line-width": 5,
          "line-opacity": 0.95
        }
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
    };
  }, []);

  // Update Route Polyline
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !selectedRoute) return;

    const source = map.getSource("route-source") as maplibregl.GeoJSONSource;
    if (source) {
      source.setData({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {
              congestion: selectedRoute.summary.overall_congestion,
              name: selectedRoute.name
            },
            geometry: {
              type: "LineString",
              coordinates: selectedRoute.geometry.coordinates
            }
          }
        ]
      });

      // Fit map bounds to route coordinates
      const coords = selectedRoute.geometry.coordinates;
      if (coords.length > 0) {
        const bounds = coords.reduce(
          (b, coord) => b.extend(coord as [number, number]),
          new maplibregl.LngLatBounds(coords[0] as [number, number], coords[0] as [number, number])
        );
        map.fitBounds(bounds, { padding: 60, duration: 1000 });
      }
    }
  }, [selectedRoute, mapLoaded]);

  // Update Incident Markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // Clear old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Add new incident markers
    incidents.forEach((inc) => {
      const el = document.createElement("div");
      el.className = "group relative cursor-pointer";

      // Pulsating marker HTML
      el.innerHTML = `
        <div class="relative flex items-center justify-center w-8 h-8">
          <span class="animate-ping absolute inline-flex h-6 w-6 rounded-full ${
            inc.severity === "CRITICAL" ? "bg-rose-500" : "bg-amber-500"
          } opacity-60"></span>
          <div class="relative w-6 h-6 rounded-full ${
            inc.severity === "CRITICAL" ? "bg-rose-600" : "bg-amber-600"
          } border-2 border-white shadow-lg flex items-center justify-center text-white">
            <span class="material-symbols-outlined text-[13px]">${
              inc.incident_type === "ACCIDENT" ? "car_crash" : inc.incident_type === "FLOOD" ? "flood" : "construction"
            }</span>
          </div>
        </div>
      `;

      // Popup
      const popup = new maplibregl.Popup({ offset: 15, closeButton: false }).setHTML(`
        <div class="p-2 bg-slate-900 text-white rounded text-xs font-mono border border-white/10 max-w-[200px]">
          <div class="text-[10px] uppercase font-bold text-rose-400 mb-0.5">${inc.incident_type} (${inc.severity})</div>
          <div class="text-[11px] text-slate-200">${inc.description}</div>
          <div class="text-[9px] text-slate-400 mt-1">Source: ${inc.data_source}</div>
        </div>
      `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([inc.lng, inc.lat])
        .setPopup(popup)
        .addTo(map);

      markersRef.current.push(marker);
    });
  }, [incidents, mapLoaded]);

  const recenterMetroManila = () => {
    if (mapRef.current) {
      mapRef.current.flyTo({
        center: [121.0405, 14.5855],
        zoom: 12,
        pitch: 35,
        bearing: -10,
        duration: 1000
      });
    }
  };

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainerRef} className="w-full h-full bg-[#080C14]" />

      {/* Floating Map Controls */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
        <button
          onClick={recenterMetroManila}
          title="Recenter Metro Manila"
          className="bg-surface-panel/90 hover:bg-surface-elevated text-text-primary px-3 py-1.5 rounded border border-white/10 text-xs font-mono shadow-md flex items-center gap-1.5 transition backdrop-blur-md"
        >
          <span className="material-symbols-outlined text-[15px]">my_location</span>
          <span>Recenter NCR</span>
        </button>

        <button
          onClick={onToggleHeatmap}
          title="Toggle Traffic Heatmap Layer"
          className={`px-3 py-1.5 rounded border text-xs font-mono shadow-md flex items-center gap-1.5 transition backdrop-blur-md ${
            heatmapVisible
              ? "bg-indigo-950/90 border-ai-primary text-white shadow-ai-aura"
              : "bg-surface-panel/90 hover:bg-surface-elevated border-white/10 text-text-secondary"
          }`}
        >
          <span className="material-symbols-outlined text-[15px]">layers</span>
          <span>Heatmap {heatmapVisible ? "ON" : "OFF"}</span>
        </button>
      </div>

      {/* Legend Badge */}
      <div className="absolute bottom-6 right-4 z-20 hidden sm:flex items-center gap-2 bg-surface-panel/90 backdrop-blur-md px-3 py-1.5 rounded border border-white/10 text-[10px] font-mono shadow-md">
        <span className="text-text-muted">Status:</span>
        <span className="flex items-center gap-1 text-traffic-normal">
          <span className="w-2 h-2 rounded-full bg-traffic-normal"></span> Normal
        </span>
        <span className="flex items-center gap-1 text-traffic-moderate">
          <span className="w-2 h-2 rounded-full bg-traffic-moderate"></span> Mod
        </span>
        <span className="flex items-center gap-1 text-traffic-heavy">
          <span className="w-2 h-2 rounded-full bg-traffic-heavy"></span> Heavy
        </span>
        <span className="flex items-center gap-1 text-traffic-severe">
          <span className="w-2 h-2 rounded-full bg-traffic-severe"></span> Severe
        </span>
      </div>
    </div>
  );
};
