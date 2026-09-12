"""
NCR Places & Landmark Autocomplete Endpoint for SanTrapik
Searches real-time landmarks, districts, streets, and hubs within National Capital Region (NCR)
using OpenStreetMap Nominatim with local bounding box filtering and caching.
"""

import logging
import httpx
from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.core.config import settings

logger = logging.getLogger("santrapik.places")
router = APIRouter()

class PlaceSuggestion(BaseModel):
    name: str
    display_name: str
    city: Optional[str] = None
    lat: float
    lng: float

# Pre-indexed popular key NCR hubs for instant sub-millisecond matching
POPULAR_NCR_PLACES = [
    # Quezon City
    {"name": "Quezon Memorial Circle", "display_name": "Quezon Memorial Circle, Diliman, Quezon City", "city": "Quezon City", "lat": 14.6515, "lng": 121.0494},
    {"name": "SM North EDSA", "display_name": "SM North EDSA, Bago Bantay, Quezon City", "city": "Quezon City", "lat": 14.6571, "lng": 121.0313},
    {"name": "TriNoma Mall", "display_name": "TriNoma, North Avenue, Quezon City", "city": "Quezon City", "lat": 14.6534, "lng": 121.0335},
    {"name": "UP Diliman", "display_name": "University of the Philippines Diliman, Quezon City", "city": "Quezon City", "lat": 14.6537, "lng": 121.0685},
    {"name": "Ateneo de Manila / Katipunan", "display_name": "Ateneo de Manila University, Katipunan Ave, Quezon City", "city": "Quezon City", "lat": 14.6396, "lng": 121.0776},
    {"name": "Araneta City / Cubao", "display_name": "Araneta City (Smart Araneta Coliseum), Cubao, Quezon City", "city": "Quezon City", "lat": 14.6219, "lng": 121.0532},
    {"name": "Eastwood City", "display_name": "Eastwood City Cyberpark, Bagumbayan, Quezon City", "city": "Quezon City", "lat": 14.6105, "lng": 121.0805},
    
    # Makati
    {"name": "Ayala Triangle / Makati CBD", "display_name": "Ayala Triangle Gardens, Makati Avenue, Makati City", "city": "Makati", "lat": 14.5573, "lng": 121.0234},
    {"name": "Glorietta / Greenbelt", "display_name": "Glorietta & Greenbelt Complex, Ayala Center, Makati", "city": "Makati", "lat": 14.5516, "lng": 121.0258},
    {"name": "Circuit Makati", "display_name": "Circuit Makati, AP Reyes St, Carmona, Makati", "city": "Makati", "lat": 14.5765, "lng": 121.0180},
    {"name": "Guadalupe Commercial Complex", "display_name": "Guadalupe Nuevo, EDSA, Makati", "city": "Makati", "lat": 14.5670, "lng": 121.0450},

    # Taguig / BGC
    {"name": "BGC High Street", "display_name": "Bonifacio High Street, BGC, Taguig City", "city": "Taguig", "lat": 14.5512, "lng": 121.0505},
    {"name": "Market! Market!", "display_name": "Market! Market!, Bonifacio Global City, Taguig", "city": "Taguig", "lat": 14.5450, "lng": 121.0570},
    {"name": "Venice Grand Canal Mall", "display_name": "Venice Grand Canal Mall, McKinley Hill, Taguig", "city": "Taguig", "lat": 14.5338, "lng": 121.0508},

    # City of Manila
    {"name": "UST España", "display_name": "University of Santo Tomas, España Blvd, Sampaloc, Manila", "city": "Manila", "lat": 14.6095, "lng": 120.9890},
    {"name": "Rizal Park / Luneta", "display_name": "Rizal Park (Luneta), Roxas Boulevard, Ermita, Manila", "city": "Manila", "lat": 14.5831, "lng": 120.9794},
    {"name": "Intramuros", "display_name": "Intramuros Historical District, Manila", "city": "Manila", "lat": 14.5898, "lng": 120.9747},
    {"name": "Binondo Chinatown", "display_name": "Binondo Chinatown, Ongpin St, Manila", "city": "Manila", "lat": 14.6002, "lng": 120.9754},
    {"name": "DLSU Taft", "display_name": "De La Salle University, Taft Avenue, Malate, Manila", "city": "Manila", "lat": 14.5648, "lng": 120.9932},

    # Mandaluyong / Pasig
    {"name": "SM Megamall", "display_name": "SM Megamall, EDSA corner Doña Julia Vargas, Mandaluyong", "city": "Mandaluyong", "lat": 14.5842, "lng": 121.0568},
    {"name": "Ortigas Center / Robinsons Galleria", "display_name": "Robinsons Galleria, EDSA corner Ortigas Ave, Quezon City / Pasig", "city": "Pasig", "lat": 14.5902, "lng": 121.0592},
    {"name": "Capitol Commons", "display_name": "Capitol Commons, Meralco Ave, Pasig", "city": "Pasig", "lat": 14.5772, "lng": 121.0628},

    # Pasay & Parañaque
    {"name": "SM Mall of Asia (MOA)", "display_name": "SM Mall of Asia, Seaside Blvd, Pasay City", "city": "Pasay", "lat": 14.5352, "lng": 120.9822},
    {"name": "NAIA Terminal 3", "display_name": "Ninoy Aquino International Airport Terminal 3, Pasay", "city": "Pasay", "lat": 14.5204, "lng": 121.0152},
    {"name": "NAIA Terminal 1 & 2", "display_name": "NAIA Terminal 1 & 2, Parañaque / Pasay", "city": "Parañaque", "lat": 14.5085, "lng": 121.0002},
    {"name": "PITX Terminal", "display_name": "Parañaque Integrated Terminal Exchange (PITX), Parañaque", "city": "Parañaque", "lat": 14.5097, "lng": 120.9904},

    # Caloocan / Malabon / Navotas / Valenzuela (CAMANAVA)
    {"name": "Monumento Circle", "display_name": "Bonifacio Monument (Monumento), Caloocan City", "city": "Caloocan", "lat": 14.6575, "lng": 120.9998},
    {"name": "SM City Grand Central", "display_name": "SM City Grand Central, Rizal Ave Extension, Caloocan", "city": "Caloocan", "lat": 14.6548, "lng": 120.9840},
    {"name": "Valenzuela City Hall", "display_name": "Valenzuela City Hall, MacArthur Highway, Valenzuela", "city": "Valenzuela", "lat": 14.6812, "lng": 120.9634},

    # South: Muntinlupa & Las Piñas
    {"name": "Alabang Town Center", "display_name": "Alabang Town Center, Alabang-Zapote Rd, Muntinlupa", "city": "Muntinlupa", "lat": 14.4255, "lng": 121.0298},
    {"name": "Festival Mall Alabang", "display_name": "Festival Mall, Filinvest City, Alabang, Muntinlupa", "city": "Muntinlupa", "lat": 14.4172, "lng": 121.0408},
    {"name": "SM Southmall", "display_name": "SM Southmall, Alabang-Zapote Rd, Las Piñas", "city": "Las Piñas", "lat": 14.4338, "lng": 121.0112},

    # Marikina & San Juan
    {"name": "Marikina River Park", "display_name": "Marikina River Park & Sports Center, Marikina City", "city": "Marikina", "lat": 14.6360, "lng": 121.0968},
    {"name": "Greenhills Shopping Center", "display_name": "Greenhills Shopping Center, Ortigas Ave, San Juan", "city": "San Juan", "lat": 14.6022, "lng": 121.0503}
]

# Simple in-memory search cache
_search_cache: Dict[str, List[PlaceSuggestion]] = {}

@router.get("/places/search", response_model=List[PlaceSuggestion], summary="Search Places & Landmarks in National Capital Region (NCR)")
async def search_places(
    q: str = Query(..., min_length=1, description="Place, landmark, or street name to search"),
    limit: int = Query(7, ge=1, le=15)
):
    """
    Returns verified places, landmarks, and districts across Metro Manila / National Capital Region (NCR).
    Searches pre-indexed popular NCR hubs first, then queries OpenStreetMap Nominatim bounded to NCR.
    """
    clean_q = q.strip().lower()
    if not clean_q:
        return []

    cache_key = f"{clean_q}_{limit}"
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    results: List[PlaceSuggestion] = []
    seen_names = set()

    # 1. Match local curated NCR places
    for p in POPULAR_NCR_PLACES:
        if clean_q in p["name"].lower() or clean_q in p["display_name"].lower():
            if p["name"] not in seen_names:
                results.append(PlaceSuggestion(
                    name=p["name"],
                    display_name=p["display_name"],
                    city=p["city"],
                    lat=p["lat"],
                    lng=p["lng"]
                ))
                seen_names.add(p["name"])
                if len(results) >= limit:
                    _search_cache[cache_key] = results
                    return results

    # 2. Live Query to Nominatim bounded strictly to Metro Manila
    min_lng, min_lat, max_lng, max_lat = settings.METRO_MANILA_BBOX
    nominatim_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": q,
        "format": "json",
        "countrycodes": "ph",
        "viewbox": f"{min_lng},{max_lat},{max_lng},{min_lat}",
        "bounded": 1,
        "limit": limit
    }
    headers = {
        "User-Agent": "SanTrapik-MetroManila/1.0 (https://santrapik.ph)"
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(nominatim_url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    lat = float(item["lat"])
                    lng = float(item["lon"])
                    
                    # Ensure within NCR bounds
                    if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
                        continue

                    display = item.get("display_name", "")
                    parts = [p.strip() for p in display.split(",") if p.strip()]
                    short_name = parts[0] if parts else q
                    
                    # Extract city if found
                    city = "Metro Manila"
                    for part in parts:
                        if any(c in part.lower() for c in [
                            "quezon", "manila", "makati", "taguig", "pasig", "mandaluyong",
                            "pasay", "caloocan", "parañaque", "muntinlupa", "las piñas",
                            "marikina", "valenzuela", "malabon", "navotas", "san juan", "pateros"
                        ]):
                            city = part
                            break

                    if short_name not in seen_names:
                        results.append(PlaceSuggestion(
                            name=short_name,
                            display_name=display,
                            city=city,
                            lat=lat,
                            lng=lng
                        ))
                        seen_names.add(short_name)
                        if len(results) >= limit:
                            break
    except Exception as e:
        logger.warning(f"Live Nominatim place search error for '{q}': {e}")

    _search_cache[cache_key] = results
    return results
