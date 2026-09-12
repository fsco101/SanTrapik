import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import type { RouteItem, IncidentItem, Coordinate } from "../../types/traffic";

interface MapContainerProps {
  selectedRoute: RouteItem | null;
  routes?: RouteItem[];
  onSelectRoute?: (id: string) => void;
  origin: Coordinate;
  destination: Coordinate;
  incidents: IncidentItem[];
  heatmapVisible: boolean;
  onToggleHeatmap: () => void;
  onResolveIncident?: (id: string) => void;
  onOpenReportModal?: () => void;
}

export const MapContainer: React.FC<MapContainerProps> = ({
  selectedRoute,
  routes = [],
  onSelectRoute,
  origin,
  destination,
  incidents,
  heatmapVisible,
  onToggleHeatmap,
  onResolveIncident,
  onOpenReportModal,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const endpointMarkersRef = useRef<maplibregl.Marker[]>([]);
  const routePillMarkersRef = useRef<maplibregl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  const onSelectRouteRef = useRef(onSelectRoute);
  useEffect(() => {
    onSelectRouteRef.current = onSelectRoute;
  }, [onSelectRoute]);

  // Initialize MapLibre GL JS
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: (import.meta.env.VITE_MAP_STYLE as string) || "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: [121.0405, 14.5855], // Centered around EDSA Ortigas / Metro Manila
      zoom: 12,
      pitch: 35,
      bearing: -10,
      attributionControl: false
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");

    map.on("load", () => {
      setMapLoaded(true);

      // 1. Alternate Routes Source & Layer (Rendered below the active route)
      map.addSource("alternate-routes-source", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: []
        }
      });

      map.addLayer({
        id: "alternate-routes-line",
        type: "line",
        source: "alternate-routes-source",
        layout: {
          "line-join": "round",
          "line-cap": "round"
        },
        paint: {
          "line-color": "#64748B",
          "line-width": 5,
          "line-opacity": 0.65,
          "line-dasharray": [2, 1.5]
        }
      });

      // Hover and Click on Alternate Routes
      map.on("mouseenter", "alternate-routes-line", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "alternate-routes-line", () => {
        map.getCanvas().style.cursor = "";
      });
      map.on("click", "alternate-routes-line", (e) => {
        if (e.features && e.features[0] && onSelectRouteRef.current) {
          const clickedId = e.features[0].properties?.id;
          if (clickedId) {
            onSelectRouteRef.current(clickedId);
          }
        }
      });

      // 2. Primary Route Source & Layers
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

  // Update Route Polylines & Midpoint Comparison Pills
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // Clear old route midpoint pills
    routePillMarkersRef.current.forEach((m) => m.remove());
    routePillMarkersRef.current = [];

    const activeSource = map.getSource("route-source") as maplibregl.GeoJSONSource;
    const altSource = map.getSource("alternate-routes-source") as maplibregl.GeoJSONSource;

    // 1. Update Active Route
    if (activeSource && selectedRoute) {
      activeSource.setData({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {
              id: selectedRoute.id,
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
    } else if (activeSource) {
      activeSource.setData({ type: "FeatureCollection", features: [] });
    }

    // 2. Update Alternate Routes
    if (altSource) {
      const alternates = (routes || []).filter((r) => !selectedRoute || r.id !== selectedRoute.id);
      altSource.setData({
        type: "FeatureCollection",
        features: alternates.map((r) => ({
          type: "Feature",
          properties: {
            id: r.id,
            name: r.name,
            travel_time: r.summary.estimated_travel_time_min,
            distance: r.summary.total_distance_km
          },
          geometry: {
            type: "LineString",
            coordinates: r.geometry.coordinates
          }
        }))
      });
    }

    // 3. Add Midpoint Information Pills for All Candidate Routes
    const candidateRoutes = routes && routes.length > 0 ? routes : (selectedRoute ? [selectedRoute] : []);
    candidateRoutes.forEach((r) => {
      const coords = r.geometry.coordinates;
      if (!coords || coords.length < 2) return;
      const midIdx = Math.floor(coords.length / 2);
      const midPoint = coords[midIdx];
      const isSelected = selectedRoute && r.id === selectedRoute.id;

      const pillEl = document.createElement("div");
      pillEl.className = "cursor-pointer select-none transition-transform hover:scale-105";

      if (isSelected) {
        const badgeLabel = r.badge === "LEAST_TRAFFIC"
          ? "Least Traffic"
          : r.badge === "SHORTEST_PATH"
          ? "Shortest"
          : r.badge === "LEAST_TRAFFIC_AND_SHORTEST"
          ? "Optimal"
          : "Active";

        pillEl.innerHTML = `
          <div class="px-2.5 py-1 rounded-full bg-indigo-950/95 border border-ai-primary text-white font-mono text-[11px] font-bold shadow-ai-aura flex items-center gap-1.5 backdrop-blur-md">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>${r.summary.estimated_travel_time_min}m</span>
            <span class="text-ai-cyan font-sans text-[10px] font-normal">• [${badgeLabel}]</span>
          </div>
        `;
      } else {
        pillEl.innerHTML = `
          <div class="px-2 py-0.5 rounded-full bg-slate-900/90 hover:bg-slate-800 border border-white/20 text-slate-300 font-mono text-[10px] shadow-lg flex items-center gap-1.5 backdrop-blur-md">
            <span>${r.summary.estimated_travel_time_min}m</span>
            <span class="text-slate-400 font-sans">• ${r.summary.total_distance_km} km</span>
          </div>
        `;
      }

      pillEl.onclick = (e) => {
        e.stopPropagation();
        if (onSelectRouteRef.current) {
          onSelectRouteRef.current(r.id);
        }
      };

      const marker = new maplibregl.Marker({ element: pillEl, anchor: "center" })
        .setLngLat(midPoint as [number, number])
        .addTo(map);

      routePillMarkersRef.current.push(marker);
    });

    // 4. Fit map bounds to candidate routes
    if (selectedRoute && selectedRoute.geometry.coordinates.length > 0) {
      const coords = selectedRoute.geometry.coordinates;
      const bounds = coords.reduce(
        (b, coord) => b.extend(coord as [number, number]),
        new maplibregl.LngLatBounds(coords[0] as [number, number], coords[0] as [number, number])
      );
      map.fitBounds(bounds, { padding: 60, duration: 1000 });
    }
  }, [selectedRoute, routes, mapLoaded]);

  // Update Incident Markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // Clear old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Add precision road-anchored incident markers
    incidents.forEach((inc) => {
      if (inc.lat == null || inc.lng == null || isNaN(inc.lat) || isNaN(inc.lng)) return;

      // Determine severity styling
      let pinBg = "bg-rose-600";
      let needleBorder = "border-t-rose-600";
      let pulseColor = "bg-rose-500";
      let badgeBg = "bg-rose-950/90";
      let badgeBorder = "border-rose-500/80";
      let badgeText = "text-rose-300";

      if (inc.severity === "HIGH") {
        pinBg = "bg-amber-600";
        needleBorder = "border-t-amber-600";
        pulseColor = "bg-amber-500";
        badgeBg = "bg-amber-950/90";
        badgeBorder = "border-amber-500/80";
        badgeText = "text-amber-300";
      } else if (inc.severity === "MEDIUM") {
        pinBg = "bg-yellow-600";
        needleBorder = "border-t-yellow-600";
        pulseColor = "bg-yellow-500";
        badgeBg = "bg-yellow-950/90";
        badgeBorder = "border-yellow-500/80";
        badgeText = "text-yellow-300";
      } else if (inc.severity === "LOW") {
        pinBg = "bg-blue-600";
        needleBorder = "border-t-blue-600";
        pulseColor = "bg-blue-500";
        badgeBg = "bg-blue-950/90";
        badgeBorder = "border-blue-500/80";
        badgeText = "text-blue-300";
      }

      // Determine incident icon
      let iconName = "warning";
      if (inc.incident_type === "ACCIDENT") iconName = "car_crash";
      else if (inc.incident_type === "ROADWORK") iconName = "construction";
      else if (inc.incident_type === "FLOOD") iconName = "flood";
      else if (inc.incident_type === "STALLED_VEHICLE") iconName = "car_repair";

      const roadLabel = inc.corridor || "NCR Corridor";

      const el = document.createElement("div");
      el.className = "group relative flex flex-col items-center cursor-pointer select-none z-20";

      // HTML Structure: Road Info Pill -> Pin Head -> Sharp Needle -> Pavement Contact Dot
      el.innerHTML = `
        <div class="px-2 py-0.5 mb-1 ${badgeBg} ${badgeBorder} ${badgeText} border rounded font-mono text-[9px] font-bold shadow-lg whitespace-nowrap backdrop-blur-md flex items-center gap-1.5 transition group-hover:scale-105">
          <span class="w-1.5 h-1.5 rounded-full ${pulseColor} animate-pulse"></span>
          <span>${inc.incident_type}</span>
          <span class="opacity-40">•</span>
          <span class="font-sans font-medium text-slate-200 max-w-[120px] truncate">${roadLabel}</span>
        </div>

        <div class="relative flex items-center justify-center w-7 h-7 rounded-full ${pinBg} border-2 border-white shadow-xl text-white">
          <span class="material-symbols-outlined text-[15px] font-bold">${iconName}</span>
        </div>

        <div class="w-0 h-0 border-l-[5px] border-l-transparent border-r-[5px] border-r-transparent border-t-[7px] ${needleBorder} -mt-[1px]"></div>

        <div class="w-2.5 h-2.5 rounded-full bg-white ring-2 ring-black shadow-lg -mt-1"></div>
      `;

      // Interactive Popup
      const popup = new maplibregl.Popup({
        offset: [0, -38],
        closeButton: true,
        maxWidth: "280px"
      }).setHTML(`
        <div class="p-3 bg-slate-900/95 text-white rounded-xl text-xs font-sans border border-white/15 shadow-2xl backdrop-blur-md">
          <div class="flex items-center justify-between pb-1.5 mb-2 border-b border-white/10">
            <span class="text-[10px] uppercase font-bold ${badgeText} tracking-wider flex items-center gap-1">
              <span class="w-2 h-2 rounded-full ${pulseColor}"></span>
              ${inc.incident_type} (${inc.severity})
            </span>
            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/10 text-slate-300">LIVE REPORT</span>
          </div>
          <div class="font-bold text-slate-100 text-[12px] mb-1">${roadLabel}</div>
          <div class="text-[11px] text-slate-300 leading-relaxed mb-2">${inc.description || "Active traffic incident affecting travel flow"}</div>
          <div class="text-[10px] text-slate-400 font-mono flex items-center justify-between pt-1 border-t border-white/10 mb-2.5">
            <span>Source: <strong class="text-slate-200">${inc.data_source}</strong></span>
            <span>Coords: ${inc.lat.toFixed(4)}, ${inc.lng.toFixed(4)}</span>
          </div>
          <button id="btn-resolve-${inc.id}" class="w-full py-1.5 px-2.5 rounded bg-emerald-600/30 hover:bg-emerald-600 border border-emerald-500/50 text-emerald-200 hover:text-white font-mono text-[10px] font-bold flex items-center justify-center gap-1 transition">
            <span class="material-symbols-outlined text-[14px]">check_circle</span>
            <span>Mark Cleared / Resolved</span>
          </button>
        </div>
      `);

      popup.on("open", () => {
        const btn = document.getElementById(`btn-resolve-${inc.id}`);
        if (btn) {
          btn.onclick = () => {
            if (onResolveIncident) {
              onResolveIncident(inc.id);
            }
            popup.remove();
          };
        }
      });

      const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
        .setLngLat([inc.lng, inc.lat])
        .setPopup(popup)
        .addTo(map);

      el.onclick = (e) => {
        e.stopPropagation();
        marker.togglePopup();
      };

      markersRef.current.push(marker);
    });
  }, [incidents, mapLoaded, onResolveIncident]);

  // Update Start Point & End Point Markers on Map
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // Clear previous endpoint markers
    endpointMarkersRef.current.forEach((m) => m.remove());
    endpointMarkersRef.current = [];

    // 1. Start Point Marker (Emerald Beacon Pin)
    if (origin && origin.lat && origin.lng) {
      const startEl = document.createElement("div");
      startEl.className = "group relative cursor-pointer z-30";
      startEl.innerHTML = `
        <div class="relative flex flex-col items-center">
          <div class="px-2 py-0.5 mb-1 bg-emerald-950/90 text-emerald-300 font-mono text-[10px] font-bold rounded border border-emerald-500/40 shadow-md whitespace-nowrap backdrop-blur-sm">
            START: ${origin.name || "Origin"}
          </div>
          <div class="relative flex items-center justify-center w-7 h-7">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
            <div class="relative w-7 h-7 rounded-full bg-emerald-500 border-2 border-white shadow-xl flex items-center justify-center text-white">
              <span class="material-symbols-outlined text-[16px] font-bold">trip_origin</span>
            </div>
          </div>
        </div>
      `;
      const startMarker = new maplibregl.Marker({ element: startEl, anchor: "bottom" })
        .setLngLat([origin.lng, origin.lat])
        .addTo(map);
      endpointMarkersRef.current.push(startMarker);
    }

    // 2. End Point Marker (Rose / Finish Flag Pin)
    if (destination && destination.lat && destination.lng) {
      const endEl = document.createElement("div");
      endEl.className = "group relative cursor-pointer z-30";
      endEl.innerHTML = `
        <div class="relative flex flex-col items-center">
          <div class="px-2 py-0.5 mb-1 bg-rose-950/90 text-rose-300 font-mono text-[10px] font-bold rounded border border-rose-500/40 shadow-md whitespace-nowrap backdrop-blur-sm">
            DEST: ${destination.name || "Destination"}
          </div>
          <div class="relative flex items-center justify-center w-7 h-7">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-60"></span>
            <div class="relative w-7 h-7 rounded-full bg-rose-600 border-2 border-white shadow-xl flex items-center justify-center text-white">
              <span class="material-symbols-outlined text-[16px] font-bold">flag</span>
            </div>
          </div>
        </div>
      `;
      const endMarker = new maplibregl.Marker({ element: endEl, anchor: "bottom" })
        .setLngLat([destination.lng, destination.lat])
        .addTo(map);
      endpointMarkersRef.current.push(endMarker);
    }
  }, [origin, destination, mapLoaded]);

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

        {onOpenReportModal && (
          <button
            onClick={onOpenReportModal}
            title="Report Live Incident on Road"
            className="bg-rose-950/90 hover:bg-rose-900 border border-rose-500/50 text-rose-200 hover:text-white px-3 py-1.5 rounded text-xs font-mono shadow-md flex items-center gap-1.5 transition backdrop-blur-md"
          >
            <span className="material-symbols-outlined text-[15px]">crisis_alert</span>
            <span>+ Report Incident</span>
          </button>
        )}
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
