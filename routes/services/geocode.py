"""Shared geocoding: address → (lat, lon)."""
from typing import Tuple, Optional

import requests

from django.conf import settings

GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"


def geocode_address(text: str, country: str = "USA") -> Tuple[Optional[float], Optional[float]]:
    """Return (lat, lon) or (None, None)."""
    api_key = getattr(settings, "ORS_API_KEY", None)
    print(api_key, "line14")
    if not api_key:
        return None, None

    params = {"api_key": api_key, "text": text, "boundary.country": country}
    try:
        resp = requests.get(GEOCODE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None, None

    features = data.get("features") or []
    if not features:
        return None, None
    coords = features[0].get("geometry", {}).get("coordinates")
    if not coords or len(coords) < 2:
        return None, None

    lon, lat = coords[0], coords[1]
    return float(lat), float(lon)


def geocode_origin_destination(
    origin: str,
    destination: str,
    country: str = "USA",
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Geocode start and end for routing.
    Returns ((lat_origin, lon_origin), (lat_dest, lon_dest)).
    Raises ValueError if either address fails.
    """
    lat_orig, lon_orig = geocode_address(origin, country=country)
    if lat_orig is None or lon_orig is None:
        raise ValueError(f"Could not geocode origin: {origin!r}")

    lat_dest, lon_dest = geocode_address(destination, country=country)
    if lat_dest is None or lon_dest is None:
        raise ValueError(f"Could not geocode destination: {destination!r}")

    return (lat_orig, lon_orig), (lat_dest, lon_dest)