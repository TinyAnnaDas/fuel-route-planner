# Fuel Route Planner API

A Django REST API that returns a route between two US locations and optimal fuel-stop recommendations along the route. Uses a 500-mile vehicle range, cost-effective stops from the fuel-prices dataset, and a single routing call plus geocoding via OpenRouteService.

## Features

- **Input**: Start and finish locations (USA; addresses or place names).
- **Output**:
  - Route geometry as a polyline (list of `[lat, lon]` for map display).
  - Total route distance in km.
  - Optimal fuel stops along the route (one per range segment, cheapest in segment).
- **Routing**: One ORS Directions call per request; origin/destination geocoded via ORS Geocode (two calls).
- **Fuel data**: Loaded from CSV into the `FuelStation` model; optimizer selects stations near the route by segment and picks the cheapest in each.

## Tech Stack

- **Django** 6.x
- **Django REST Framework**
- **django-environ** for configuration
- **OpenRouteService (ORS)** for geocoding and driving directions ([openrouteservice.org](https://openrouteservice.org/) — free tier available)
- **PostgreSQL** (via psycopg2-binary) for fuel-station data
- **numpy**, **scipy**, **polyline**, **requests**

## Project Structure

```text
fuel_route_planner/
├── fuel_route_planner/     # Project settings, root URLs
├── routes/                 # Main app
│   ├── data/
│   │   └── fuel-prices.csv
│   ├── management/commands/
│   │   ├── load_fuel_prices.py
│   │   ├── geocode_fuel_stations.py
│   │   └── delete_non_us_states.py
│   ├── services/
│   │   ├── geocode.py      # ORS geocode (address → lat, lon)
│   │   ├── routing.py      # ORS Directions (route + polyline)
│   │   ├── fuel.py         # Fuel data: nearest stations along route
│   │   └── optimizer.py    # Fuel-stop selection (500 mi range, by segment)
│   ├── models.py           # FuelStation
│   ├── serializers.py
│   ├── views.py            # plan_route endpoint
│   └── urls.py
├── manage.py
├── pyproject.toml
├── uv.lock
└── .env                    # Not committed; see below
```

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- PostgreSQL (for fuel-station data)

### Install dependencies

```bash
# With uv
uv sync

# Or with pip
pip install -e .
```

### Environment variables

Create a `.env` file in the project root (do not commit it):

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=fuel_route_planner
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# OpenRouteService (free API key at https://openrouteservice.org/dev/#/signup)
ORS_API_KEY=your-ors-api-key
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Database and fuel data

```bash
python manage.py migrate
python manage.py load_fuel_prices          # Load routes/data/fuel-prices.csv
python manage.py geocode_fuel_stations    # Optional: fill lat/lon for stations
```

### Run the server

```bash
python manage.py runserver
```

## API

### Endpoint

- **URL**: `POST /api/plan-route/` or `GET /api/plan-route/?origin=...&destination=...`
- **Methods**: GET (query params) or POST (JSON body with `origin` / `origin_address` and `destination` / `destination_address`).

### Request

- **GET**: `origin` and `destination` (or `origin_address` / `destination_address`) as query parameters.
- **POST**: JSON body, e.g. `{"origin": "New York, NY", "destination": "Los Angeles, CA"}`.

### Response (JSON)

- **`polyline`**: List of `[lat, lon]` for drawing the route.
- **`total_km`**: Total route distance in kilometers.
- **`fuel_stops`**: List of recommended stops, each with:
  - `id`, `name`, `price` (retail price per gallon), `lat`, `lon`.

Errors: `400` (missing/invalid input, geocode failure), `502` (routing failure).

### Example

```bash
curl "http://localhost:8000/api/plan-route/?origin=Chicago,IL&destination=Dallas,TX"
```

## Fuel Data

- **File**: `routes/data/fuel-prices.csv`
- **Columns**: OPIS Truckstop ID, Truckstop Name, Address, City, State, Rack ID, Retail Price. After geocoding, stations have latitude/longitude for proximity to the route.
- **Optimizer**: 500-mile range; one stop per segment; within each segment the cheapest station near the route is chosen.

## Assignment Deliverables

- **Code**: This repository.
- **Loom (≤5 min)**: Use Postman (or similar) to demonstrate the API and a short overview of the codebase.
- **Performance**: Single directions call per plan; geocoding limited to origin and destination.

## License

Assignment project; use as required by the hiring team.
