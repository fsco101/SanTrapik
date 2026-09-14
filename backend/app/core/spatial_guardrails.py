"""
Geospatial Guardrails and Input Sanitization for SanTrapik
Protects PostGIS spatial operations against coordinate injection, NaN/Infinity exploits,
and ensures coordinates fall strictly within designated Philippine / Metro Manila bounds.
"""

import re
import math
from typing import Tuple

# Metro Manila Arterial Core Bounding Box (min_lng, min_lat, max_lng, max_lat)
METRO_MANILA_STRICT_BBOX = (120.90, 14.35, 121.15, 14.80)

# Greater Manila Urban Fringe (Bulacan, Rizal, Cavite, Laguna boundaries)
GREATER_MANILA_OUTER_BBOX = (120.70, 14.15, 121.35, 15.00)

TAG_RE = re.compile(r"<[^>]+>")

def validate_philippine_coordinate(lng: float, lat: float, strict: bool = True) -> bool:
    """
    Validates that a coordinate pair is numeric, finite, and strictly falls within
    Metro Manila or Greater Manila bounds.
    """
    if not (isinstance(lng, (int, float)) and isinstance(lat, (int, float))):
        return False
    if math.isnan(lng) or math.isnan(lat) or math.isinf(lng) or math.isinf(lat):
        return False

    min_lng, min_lat, max_lng, max_lat = METRO_MANILA_STRICT_BBOX if strict else GREATER_MANILA_OUTER_BBOX
    return (min_lng <= lng <= max_lng) and (min_lat <= lat <= max_lat)

def sanitize_text_input(text: str, max_length: int = 280) -> str:
    """
    Sanitizes user-submitted text by stripping HTML tags, non-printable control characters,
    and clamping length to prevent storage bloat and XSS vectors.
    """
    if not text:
        return ""
    # Strip HTML tags
    cleaned = TAG_RE.sub("", text)
    # Remove control characters except newline and whitespace
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in "\n\r\t")
    # Normalize excessive spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_length]
