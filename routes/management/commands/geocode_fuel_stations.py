from django.conf import settings
from django.core.management.base import BaseCommand
import time

import requests

from routes.models import FuelStation

GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
# GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"

RATE_LIMIT_DELAY = 0.65  # seconds between requests (stay under 100/min)


def geocode_address(text: str, country: str = "USA"):
    """Call ORS Geocode Search; return (lat, lon) or (None, None)."""
    # api_key = getattr(settings, "ORS_API_KEY", None)
    api_key = getattr(settings, "GEOAPIFY_KEY", None)

    if not api_key:
        return None, None
    params = {
        "api_key": api_key,
        "text": text,
        "boundary.country": country
    }
    try:
        resp = requests.get(GEOCODE_URL, params=params, timeout=10)
        print(resp.request.url)  # full U
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(e)
        return None, None

    features = data.get("features") or []
    if not features:
        return None, None
    coords = features[0].get("geometry", {}).get("coordinates")
    if not coords or len(coords) < 2:
        return None, None

    lon, lat = coords[0], coords[1]

    return float(lat), float(lon)

class Command(BaseCommand):
    help = "Fill latitude/logitude for FuelStation rows"
    def add_arguments(self, parser):
       parser.add_argument(
           "--dry-run",
           action = "store_true",
           help = "Only print how many would be geocoded, do not call API or save"
       )
       parser.add_argument(
           "--limit",
           type=int,
           default = 0,
           help="Max number of station to geocode (0 = no limit)"
       )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        qs = FuelStation.objects.filter(latitude__isnull=True) | FuelStation.objects.filter(
            longitude__isnull=True
        )[:100]
        qs_l = FuelStation.objects.filter(latitude__isnull=False) | FuelStation.objects.filter(
            longitude__isnull=False
        )
        qs_t = FuelStation.objects.all()
        total = qs.count()
        self.stdout.write(f"Stations missing coordinates: {total}")
        self.stdout.write(f"Stations with coordinates: {qs_l.count()}")
        self.stdout.write(f"All Stations: {qs_t.count()}")
        if total == 0:
            return
        if dry_run:
            self.stdout.write("Dry run: no API calls or saves.")
            return
        done = 0
        for station in qs.iterator(chunk_size=500):
            if limit and done >= limit:
                break
            address_str = f"{station.address}, {station.city}, {station.state}, USA"
            lat, lon = geocode_address(address_str)
            if lat is not None and lon is not None:
                station.latitude = lat
                station.longitude = lon
                station.save(update_fields=["latitude", "longitude"])
                done +=1
                self.stdout.write(f"GeoCoded {done} : {station.truck_stop_name} -> {lat: .4f}, {lon: .4f}")
            else:
                self.stdout.write(self.style.WARNING(f"No result: {address_str}"))
            time.sleep(RATE_LIMIT_DELAY)
        self.stdout.write(self.style.SUCCESS(f"Geocoded {done} stations."))



