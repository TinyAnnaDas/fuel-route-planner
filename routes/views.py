import math

from django.http import JsonResponse

from routes.services.routing import get_route
from routes.services.optimizer import get_optimal_fuel_stops, VEHICLE_RANGE_KM


def plan_route(request):
    """
    GET or POST: ?origin=...&destination=... (or JSON body).
    Returns JSON: { "polyline": [[lat,lon],...], "total_km": float, "fuel_stops": [{ id, name, price, lat, lon }, ...] }.
    """
    if request.method == "POST" and request.content_type == "application/json":
        import json
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        origin = body.get("origin") or body.get("origin_address")
        destination = body.get("destination") or body.get("destination_address")
    else:
        origin = request.GET.get("origin") or request.GET.get("origin_address")
        destination = request.GET.get("destination") or request.GET.get("destination_address")

    if not origin or not destination:
        return JsonResponse({"error": "origin and destination required"}, status=400)

    try:
        polyline, total_km = get_route(origin, destination)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Routing failed: {e}"}, status=502)

    max_stops = max(1, math.ceil(total_km / VEHICLE_RANGE_KM))
    stops = get_optimal_fuel_stops(polyline, total_km=total_km, range_km=VEHICLE_RANGE_KM, max_stops=max_stops)
    fuel_stops = [
        {
            "id": s.id,
            "name": s.truck_stop_name,
            "price": float(s.retail_price),
            "lat": s.latitude,
            "lon": s.longitude,
        }
        for s in stops
    ]

    return JsonResponse({
        "polyline": list(polyline),
        "total_km": total_km,
        "fuel_stops": fuel_stops,
    })