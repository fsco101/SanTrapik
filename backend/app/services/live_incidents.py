"""
Live Incident Feed Ingestion Service for SanTrapik
Handles incoming crowdsourced alerts, public advisory reports, and MMDA-formatted feeds.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.services.telemetry import telemetry_service

class LiveIncidentFeedService:
    def process_incident_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates, normalizes, and ingests a live incident into active monitoring.
        Accepts user reports, emergency services alerts, or scraped feeds.
        """
        lng = float(report_data.get("lng", 121.0))
        lat = float(report_data.get("lat", 14.58))
        
        incident_type = report_data.get("incident_type", "OTHER").upper()
        severity = report_data.get("severity", "MEDIUM").upper()
        description = report_data.get("description", "Reported traffic obstruction")
        data_source = report_data.get("data_source", "COMMUTER_REPORT")

        incident_record = {
            "id": f"inc_live_{uuid.uuid4().hex[:8]}",
            "incident_type": incident_type,
            "description": description,
            "severity": severity,
            "status": "ACTIVE",
            "point_lng_lat": [lng, lat],
            "corridor": report_data.get("corridor", "Metro Manila Arterial"),
            "minutes_ago": 0,
            "data_source": data_source
        }

        # Register into live telemetry service
        telemetry_service.add_live_incident(incident_record)
        return incident_record

    def bulk_ingest_advisories(self, advisories: List[Dict[str, Any]]) -> int:
        """Processes a list of external road advisories."""
        count = 0
        for adv in advisories:
            try:
                self.process_incident_report(adv)
                count += 1
            except Exception:
                continue
        return count

live_incident_feed_service = LiveIncidentFeedService()
