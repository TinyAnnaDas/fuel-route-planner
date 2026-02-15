# ORS API client

# routes/services/routing.py
"""Get driving route from A to B (one Directions call, addresses accepted)."""
from typing import List, Tuple
import requests

def _decode_polyline(encoded: str) -> List[Tuple[float, float]]:
    """Decode ORS/Google-style encoded polyline to list of (lat, lon)."""
    try:
        import polyline
        return polyline.decode(encoded)
    except Exception as e:
         print(e)



def parse_ors_route_response(data: dict) -> Tuple[List[Tuple[float, float]], float]:
    """
    Parse ORS structured response: routes[0].geometry (encoded polyline),
    routes[0].summary.distance (meters). Returns (polyline as (lat, lon), total_km).
    """
    routes = data.get("routes") or []
    if not routes:
        raise RuntimeError("ORS: no routes in response")

    route = routes[0]
    enc = route.get("geometry")
    if not enc or not isinstance(enc, str):
        raise RuntimeError("ORS: route has no geometry")

    polyline_points = _decode_polyline(enc)
    summary = route.get("summary") or {}
    total_m = summary.get("distance", 0)
    return polyline_points, total_m / 1000.0

ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def get_route_ors(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> Tuple[List[Tuple[float, float]], float]:
    """
    Get driving route from ORS using coordinates.
    ORS expects [lon, lat]. Returns (polyline as (lat, lon), total_km).
    """
    from django.conf import settings

    api_key = getattr(settings, "ORS_API_KEY", None) or getattr(settings, "GEOAPIFY_KEY", None)
    if not api_key:
        raise ValueError("ORS_API_KEY required for get_route_ors")

    # ORS: coordinates as [lon, lat]
    body = {
        "coordinates": [[origin_lon, origin_lat], [dest_lon, dest_lat]],
    }
    headers = {"Authorization": api_key}
    resp = requests.post(ORS_DIRECTIONS_URL, json=body, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    # print(data, "line64")
    return parse_ors_route_response(data)



def get_route(
    origin: str,
    destination: str,
) -> Tuple[List[Tuple[float, float]], float]:
    """
    Get driving route from origin to destination (addresses or "City, State").
    Geocodes both, then calls ORS. Returns (polyline as (lat, lon), total_km).
    """
    from routes.services.geocode import geocode_origin_destination

    (lat_orig, lon_orig), (lat_dest, lon_dest) = geocode_origin_destination(origin, destination)
    return get_route_ors(lat_orig, lon_orig, lat_dest, lon_dest)
