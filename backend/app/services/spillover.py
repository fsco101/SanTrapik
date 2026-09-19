"""
Spatiotemporal Bottleneck Spillover Predictor (SP9-003).
Builds directional topological road adjacency graphs for Metro Manila arterials
and calculates upstream queue shockwave propagation (backpressure) when bottlenecks occur.
"""

from typing import List, Dict, Any, Tuple, Optional
import math

# Directional road topology (traffic flows index 0 -> index N)
CORRIDOR_TOPOLOGY: Dict[str, List[str]] = {
    "EDSA_NB": [
        "Pasay", "Magallanes", "Ayala", "Buendia", "Guadalupe",
        "Pioneer", "Shaw", "Megamall", "Ortigas", "Santolan",
        "Cubao", "Kamuning", "Quezon Ave", "North Ave", "Balintawak"
    ],
    "EDSA_SB": [
        "Balintawak", "North Ave", "Quezon Ave", "Kamuning", "Cubao",
        "Santolan", "Ortigas", "Megamall", "Shaw", "Pioneer",
        "Guadalupe", "Buendia", "Ayala", "Magallanes", "Pasay"
    ],
    "C5_NB": [
        "SLEX", "FTI", "Taguig", "Market Market", "Bagong Ilog",
        "Kalayaan", "Lanuza", "Ortigas Ave", "Libis", "Katipunan",
        "UP Diliman", "Tandang Sora"
    ],
    "C5_SB": [
        "Tandang Sora", "UP Diliman", "Katipunan", "Libis", "Ortigas Ave",
        "Lanuza", "Kalayaan", "Bagong Ilog", "Market Market", "Taguig",
        "FTI", "SLEX"
    ],
    "COMMONWEALTH_WB": [
        "Fairview", "Batasan", "Ever Gotesco", "Litex", "Don Antonio",
        "Tandang Sora", "Central", "Philcoa", "Elliptical Road"
    ],
    "COMMONWEALTH_EB": [
        "Elliptical Road", "Philcoa", "Central", "Tandang Sora", "Don Antonio",
        "Litex", "Ever Gotesco", "Batasan", "Fairview"
    ],
    "QUEZON_AVE_WB": [
        "Elliptical Road", "BIR", "Delta", "Timog", "Fisher Mall",
        "Araneta", "Welcome Rotonda"
    ],
    "QUEZON_AVE_EB": [
        "Welcome Rotonda", "Araneta", "Fisher Mall", "Timog", "Delta",
        "BIR", "Elliptical Road"
    ]
}

def match_node_in_topology(segment_name: str, topology_nodes: List[str]) -> Optional[int]:
    """Matches segment name to index in topology node list."""
    name_clean = segment_name.lower().replace("edsa", "").replace("c-5", "").replace("c5", "").strip()
    for idx, node in enumerate(topology_nodes):
        if node.lower() in name_clean or name_clean in node.lower():
            return idx
    return None

class SpilloverEngine:
    def __init__(self):
        self.topology = CORRIDOR_TOPOLOGY
        # Average urban backward shockwave propagation speed ~15 km/h
        self.shockwave_speed_kmh = 15.0

    def predict_spillover(
        self,
        route_segments: List[Dict[str, Any]],
        active_incidents: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Detects choke points in traversed route segments and computes upstream backpressure
        queuing shockwaves across contiguous road segments.
        Returns:
            (warnings, flagged_segment_ids)
        """
        warnings: List[str] = []
        flagged_segment_ids: List[str] = []

        if not route_segments:
            return warnings, flagged_segment_ids

        # 1. Identify choke points along the route
        # Severe bottleneck threshold: congestion >= 60% or speed ratio < 0.35 or active incident
        choke_points = []
        for seg in route_segments:
            cong = float(seg.get("congestion_percentage", 0.0))
            curr_spd = float(seg.get("current_speed", seg.get("average_speed_kmh", 40.0)))
            base_spd = float(seg.get("baseline_speed", 50.0))
            spd_ratio = curr_spd / base_spd if base_spd > 0 else 1.0

            has_inc = bool(seg.get("incidents") and len(seg.get("incidents")) > 0)

            if cong >= 60.0 or spd_ratio < 0.35 or has_inc:
                choke_points.append(seg)

        if not choke_points:
            return warnings, flagged_segment_ids

        # 2. Check each choke point against corridor topologies
        for choke in choke_points:
            choke_name = choke.get("name", "Active Corridor")
            choke_id = choke.get("id") or choke.get("segment_id", "")
            choke_dir = str(choke.get("direction", "NB")).upper()
            choke_road = str(choke.get("road_code") or choke_name).upper()

            # Identify matching corridor key
            corridor_key = None
            for key in self.topology.keys():
                road_prefix = key.split("_")[0]
                dir_suffix = key.split("_")[-1]
                if road_prefix in choke_road or road_prefix in choke_name.upper():
                    if dir_suffix in choke_dir or choke_dir in dir_suffix or choke_dir == "BOTH":
                        corridor_key = key
                        break

            # Fallback to sequential route order if corridor not in static topology
            if not corridor_key:
                # Upstream in route sequence is preceding segments
                try:
                    choke_idx = route_segments.index(choke)
                    if choke_idx > 0:
                        upstream_seg = route_segments[choke_idx - 1]
                        upstream_id = upstream_seg.get("id") or upstream_seg.get("segment_id", "")
                        upstream_name = upstream_seg.get("name", "Upstream segment")
                        est_mins = 15
                        flagged_segment_ids.append(upstream_id)
                        warnings.append(
                            f"Upstream slowdown expected at {upstream_name} in ~{est_mins} mins due to {choke_name} bottleneck"
                        )
                except ValueError:
                    pass
                continue

            # Traversal within matched corridor topology
            nodes = self.topology[corridor_key]
            choke_node_idx = match_node_in_topology(choke_name, nodes)

            if choke_node_idx is not None and choke_node_idx > 0:
                # In directional flow (0 -> N), upstream traffic comes from index < choke_node_idx
                # Backward shockwave propagates backwards (choke_node_idx - 1, choke_node_idx - 2)
                for step in range(1, 3):
                    upstream_node_idx = choke_node_idx - step
                    if upstream_node_idx >= 0:
                        upstream_node_name = nodes[upstream_node_idx]

                        # Match upstream node to segment in route_segments if present
                        matching_route_seg = next(
                            (s for s in route_segments if upstream_node_name.lower() in s.get("name", "").lower()),
                            None
                        )
                        if matching_route_seg:
                            u_id = matching_route_seg.get("id") or matching_route_seg.get("segment_id", "")
                            if u_id and u_id not in flagged_segment_ids:
                                flagged_segment_ids.append(u_id)

                        # Distance estimation: ~1.5 km per segment step
                        dist_km = step * 1.6
                        est_mins = max(10, min(45, int(round((dist_km / self.shockwave_speed_kmh) * 60))))

                        warning_msg = (
                            f"Upstream slowdown expected at {upstream_node_name} in ~{est_mins} mins "
                            f"due to {choke_name} bottleneck"
                        )
                        if warning_msg not in warnings:
                            warnings.append(warning_msg)

        # Always flag at least the immediately preceding segment in route if shockwaves exist
        if warnings and not flagged_segment_ids and len(route_segments) > 1:
            for choke in choke_points:
                try:
                    c_idx = route_segments.index(choke)
                    if c_idx > 0:
                        p_id = route_segments[c_idx - 1].get("id") or route_segments[c_idx - 1].get("segment_id", "")
                        if p_id:
                            flagged_segment_ids.append(p_id)
                except ValueError:
                    pass

        return warnings, flagged_segment_ids

spillover_engine = SpilloverEngine()
