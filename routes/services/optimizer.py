#  Fuel stop optimization algorithm


# routes/services/optimizer.py
"""Pick best fuel stop(s) along the route (cost-effective = lowest price)."""
from typing import List

from routes.models import FuelStation
from routes.services.fuel import get_stations_near_route


def get_optimal_fuel_stops(
    polyline_points: List[tuple],
    radius_deg: float = 0.3,
    max_stops: int = 1,
) -> List[FuelStation]:
    """
    Return up to max_stops stations along the route with lowest price per gallon.
    polyline_points: list of (lat, lon) from routing.get_route().
    """
    if not polyline_points:
        return []

    candidates = get_stations_near_route(polyline_points, radius_deg=radius_deg)
    if not candidates:
        return []

    by_price = sorted(candidates, key=lambda s: s.retail_price)
    return by_price[:max_stops]