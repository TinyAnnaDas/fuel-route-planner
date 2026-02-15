# routes/services/optimizer.py
"""Pick best fuel stop(s) along the route by segment (one per range window, cheapest in segment)."""
import math
from typing import List, Tuple

from routes.models import FuelStation
from routes.services.fuel import (
    cumulative_distances_km,
    get_stations_near_route,
    haversine_km,
)

VEHICLE_RANGE_KM = 500 * 1.60934


def _distance_along_route(
    station_lat: float,
    station_lon: float,
    polyline_points: List[Tuple[float, float]],
    cumulative_km: List[float],
) -> float:
    """Return distance in km from route start to the point on route nearest to (station_lat, station_lon)."""
    best_km = 0.0
    best_d = float("inf")
    for i, (lat, lon) in enumerate(polyline_points):
        d = haversine_km(station_lat, station_lon, lat, lon)
        if d < best_d:
            best_d = d
            best_km = cumulative_km[i]
    return best_km


def get_optimal_fuel_stops(
    polyline_points: List[tuple],
    total_km: float,
    range_km: float = VEHICLE_RANGE_KM,
    max_stops: int = 10,
    radius_deg: float = 0.3,
) -> List[FuelStation]:
    """
    One stop per range_km segment along the route; in each segment pick the cheapest station.
    polyline_points: list of (lat, lon) from routing.get_route().
    """
    if not polyline_points:
        return []

    candidates = get_stations_near_route(polyline_points, radius_deg=radius_deg)
    if not candidates:
        return []

    cumulative_km = cumulative_distances_km(polyline_points)
    station_to_km = [
        (s, _distance_along_route(s.latitude, s.longitude, polyline_points, cumulative_km))
        for s in candidates
    ]

    num_segments = min(max_stops, max(1, math.ceil(total_km / range_km)))
    segment_size = total_km / num_segments
    result: List[FuelStation] = []
    used_ids = set()

    for seg in range(num_segments):
        seg_start = seg * segment_size
        seg_end = (seg + 1) * segment_size
        seg_mid = (seg_start + seg_end) / 2
        in_segment = [
            (s, km) for s, km in station_to_km
            if seg_start <= km < seg_end and s.id not in used_ids
        ]
        if not in_segment:
            unused = [(s, km) for s, km in station_to_km if s.id not in used_ids]
            if not unused:
                continue
            best = min(unused, key=lambda x: (abs(x[1] - seg_mid), x[0].retail_price))
        else:
            best = min(in_segment, key=lambda x: (x[0].retail_price, x[1]))
        result.append(best[0])
        used_ids.add(best[0].id)

    return sorted(result, key=lambda s: _distance_along_route(s.latitude, s.longitude, polyline_points, cumulative_km))