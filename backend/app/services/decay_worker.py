"""
Automated Incident Aging and Half-Life Decay Worker
Performs asynchronous garbage collection and exponential confidence decay on active incident records,
ensuring stale, uncorroborated reports naturally decay and expire.
"""

import math
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

logger = logging.getLogger("santrapik.decay_worker")

class IncidentDecayWorker:
    def __init__(self, check_interval_seconds: int = 30):
        self.interval = check_interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None

    @staticmethod
    def apply_decay_to_incident(incident: Dict[str, Any], now: datetime) -> Dict[str, Any]:
        """
        Applies exponential confidence decay:
        Confidence(t) = Confidence_0 * exp(-lambda * delta_t)
        """
        if incident.get("status") in ["RESOLVED", "EXPIRED"]:
            return incident

        # Determine half-life: 20 mins for unverified, 60 mins for verified accidents
        half_life_minutes = 20.0 if incident.get("status") == "REPORTED" else 60.0
        decay_lambda = math.log(2) / half_life_minutes

        last_active_str = incident.get("last_corroborated_at") or incident.get("reported_at")
        try:
            last_active = datetime.fromisoformat(last_active_str)
            if last_active.tzinfo is None:
                last_active = last_active.replace(tzinfo=timezone.utc)
        except Exception:
            last_active = now

        elapsed_minutes = (now - last_active).total_seconds() / 60.0
        current_conf = incident.get("confidence", 0.50)

        # Exponential decay: Confidence(t) = Confidence_0 * (0.5 ** (elapsed / half_life))
        new_conf = round(current_conf * (0.5 ** (elapsed_minutes / half_life_minutes)), 2)
        incident["confidence"] = max(0.05, new_conf)

        # Transition to EXPIRED if confidence drops below 0.15 without fresh corroboration
        if incident["confidence"] < 0.15 and elapsed_minutes >= 30.0:
            incident["status"] = "EXPIRED"
            logger.info(f"Incident {incident.get('id')} expired due to confidence decay ({new_conf}) after {elapsed_minutes:.1f}m.")

        return incident

    def process_decay_cycle(self, active_incidents: List[Dict[str, Any]]) -> int:
        """Runs a single decay cycle across all active incidents. Returns count of expired incidents."""
        now = datetime.now(timezone.utc)
        expired_count = 0
        for inc in active_incidents:
            was_active = inc.get("status") not in ["RESOLVED", "EXPIRED"]
            self.apply_decay_to_incident(inc, now)
            if was_active and inc.get("status") == "EXPIRED":
                expired_count += 1
        return expired_count

    async def start(self, get_incidents_func):
        """Starts background decay loop."""
        self._running = True
        logger.info("Starting incident decay worker...")
        while self._running:
            try:
                incidents = get_incidents_func()
                self.process_decay_cycle(incidents)
            except Exception as e:
                logger.error(f"Error in decay worker cycle: {e}")
            await asyncio.sleep(self.interval)

    def stop(self):
        """Stops background decay worker."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

decay_worker = IncidentDecayWorker()
