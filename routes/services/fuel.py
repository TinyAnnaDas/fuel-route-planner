#  Fuel data loader + KD-tree lookup
import math
from typing import List, Tuple, Optional

import numpy as np

from scipy.spatial import KDTree

from routes.models import FuelStation

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two (lat, lon) points."""
    a = math.radians(lat2 - lat1)
    b = math.radians(lon2 - lon1)
    x = math.sin(a / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(b / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(x))


def cumulative_distances_km(points: List[Tuple[float, float]]) -> List[float]:
    """Cumulative distance in km from first point. Returns [0, d01, d01+d12, ...]."""
    if not points:
        return []
    if len(points) == 1:
        return [0.0]
    out = [0.0]
    for i in range(1, len(points)):
        d = haversine_km(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1])
        out.append(out[-1] + d)
    return out


class FuelStationKDTree:
    def __init__(self) -> None:
        self._tree: Optional[KDTree] = None
        self._coords: Optional[np.ndarray] = None
        self._station_ids: Optional[List[int]] = None

    def build(self) -> None:
        """Build KD-tree from all stations with valid coordinates."""
        qs = FuelStation.objects.filter(latitude__isnull=False, longitude__isnull=False)
        if not qs.exists():
            self._tree = None
            self._coords = None
            self._station_ids = None
            return

        coords: List[Tuple[float, float]] = []
        station_ids: List[int] = []

        for station in qs.iterator(chunk_size=2000):
            coords.append((station.latitude, station.longitude))
            station_ids.append(station.id)

        self._coords = np.asarray(coords, dtype=float)
        self._station_ids = station_ids
        self._tree = KDTree(self._coords)

    def is_ready(self) -> bool:
        return self._tree is not None

    def query_within_radius(self, lat: float, lon:float, radius_deg: float) -> List[FuelStation]:
        """Return all stations within radius_deg (degrees) of lat and lon.
            This is a an approximation; for more precise distance units, I need to convert my desired km/miles
            into ~degrees beforehand.
        """
        if self._tree is None or self._coords is None or self._station_ids is None:
            raise RuntimeError("FuelStationKDTree not built. Call build() first")

        indices = self._tree.query_ball_point([lat, lon], r=radius_deg)
        ids = [self._station_ids[int(idx)] for idx in indices]
        stations = list(FuelStation.objects.filter(id__in=ids))
        # Optional: need to sort by true distance or price for order
        return stations


_fuel_station_index: Optional[FuelStationKDTree] = None

def ensure_fuel_station_index_built() -> FuelStationKDTree:
    """Return the global station index, building it from DB if not yet ready."""
    global _fuel_station_index
    if _fuel_station_index is None:
        _fuel_station_index = FuelStationKDTree()
    if not _fuel_station_index.is_ready():
        _fuel_station_index.build()
    return _fuel_station_index


def get_stations_near_route(
    polyline_points: List[Tuple[float, float]],
    radius_deg: float = 0.3,
    max_queries: int = 200,
) -> List[FuelStation]:
    """
    Return stations within radius_deg of the route.

    polyline_points: list of (lat, lon) along the route (from routing API).
    radius_deg: search radius in degrees (~0.25–0.3 ≈ 25–35 km).
    max_queries: cap on how many points we sample along the route (avoids too many tree queries).
    """
    if not polyline_points:
        return []

    index = ensure_fuel_station_index_built()
    step = max(1, len(polyline_points) // max_queries)

    seen_ids: set = set()
    out: List[FuelStation] = []

    for i in range(0, len(polyline_points), step):
        lat, lon = polyline_points[i]
        for station in index.query_within_radius(lat, lon, radius_deg):
            if station.id not in seen_ids:
                seen_ids.add(station.id)
                out.append(station)

    return out