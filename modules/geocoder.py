from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time


def geocode_site(csa_data: dict) -> tuple[float, float] | None:
    """Return (lat, lon) for the construction site extracted from CSA data."""
    geolocator = Nominatim(user_agent="csa_analyzer_dt_cantiere/1.0")

    # Build progressively less specific queries until one works
    queries = []

    if csa_data.get("indirizzo_cantiere") and csa_data.get("comune"):
        queries.append(
            f"{csa_data['indirizzo_cantiere']}, {csa_data['comune']}, {csa_data.get('provincia', '')}, Italia"
        )

    if csa_data.get("comune") and csa_data.get("provincia"):
        queries.append(f"{csa_data['comune']}, {csa_data['provincia']}, Italia")

    if csa_data.get("comune"):
        queries.append(f"{csa_data['comune']}, Italia")

    for query in queries:
        try:
            time.sleep(1)  # Nominatim rate limit
            location = geolocator.geocode(query, timeout=10)
            if location:
                return (location.latitude, location.longitude)
        except (GeocoderTimedOut, GeocoderServiceError):
            continue

    return None
