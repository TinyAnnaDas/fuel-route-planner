from django.apps import AppConfig


class RoutesConfig(AppConfig):
    name = 'routes'

    def ready(self):
        """Build fuel station KD-tree at startup so first request is fast."""
        try:
            from routes.services.fuel import ensure_fuel_station_index_built
            ensure_fuel_station_index_built()
        except Exception:
            # DB may not be ready (e.g. migrate not run) or no stations; build on first use
            pass