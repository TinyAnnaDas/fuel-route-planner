# Fuel Route Planner API

A Django REST API that returns a route between two US locations, optimal fuel-stop recommendations along the route (cost-effective, 500-mile vehicle range), and total estimated fuel cost at 10 MPG. Built for Django 6 with Django REST Framework.

## Features

- **Input**: Start and finish locations (USA only).
- **Output**:
  - Route geometry (for map display).
  - Optimal fuel-up locations along the route (cost-effective, based on provided fuel prices).
  - Multiple fuel stops when the route exceeds 500 miles range.
  - Total money spent on fuel (assuming 10 miles per gallon).
- **Routing**: Uses a free routing API (minimal calls; one route request is the goal).
- **Fuel data**: Uses the provided fuel-prices CSV for retail prices and station locations.

## Tech Stack

- **Django** 6.x (latest stable)
- **Django REST Framework**
- **django-environ** for configuration
- **OpenRouteService (ORS)** for routing and map geometry ([openrouteservice.org](https://openrouteservice.org/) — free tier available)

## Project Structure

```text
fuel_route_planner/
├── fuel_route_planner/     # Project settings, URLs
├── routes/                 # Main app
│   ├── data/              # Fuel prices CSV
│   ├── services/
│   │   ├── routing.py     # ORS API client (route + geometry)
│   │   ├── fuel.py        # Fuel data loader + nearest-station lookup
│   │   └── optimizer.py   # Fuel-stop optimization (500 mi range, cost)
│   ├── serializers.py     # Request/response validation
│   └── views.py           # API endpoint(s)
├── manage.py
├── pyproject.toml / uv.lock
└── .env                    # Not committed; see below
```

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install dependencies

```bash
# With uv
uv sync

# Or with pip
pip install -e .
```

### Environment variables

Copy the example below into a `.env` file in the project root (do not commit `.env`):

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# OpenRouteService (free API key at https://openrouteservice.org/dev/#/signup)
ORS_API_KEY=your-ors-api-key
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Run the server

```bash
python manage.py runserver
```

## API

### Intended contract (for implementation and Postman/Loom demo)

- **Endpoint**: e.g. `POST /api/plan/` or `GET /api/plan/?start=...&finish=...` (depending on your implementation).
- **Input**: Start and finish (addresses or coordinates, USA only).
- **Response** (JSON):
  - `route`: Geometry (e.g. GeoJSON or encoded polyline) for drawing the route on a map.
  - `fuel_stops`: List of recommended stop locations with name, address, price per gallon, and gallons needed (or cost per stop).
  - `total_fuel_cost`: Total estimated fuel cost (10 MPG over the route distance).

Routing should call the external map/routing API as few times as possible (ideally one call; two or three acceptable).

## Fuel Data

- **File**: `routes/data/fuel-prices-for-be-assessment.csv`
- **Columns**: OPIS Truckstop ID, Truckstop Name, Address, City, State, Rack ID, **Retail Price**
- Used to choose cost-effective fuel stops along the route and to compute total fuel cost.

## Assignment Deliverables

- **Code**: This repository.
- **Loom (≤5 min)**: Use Postman (or similar) to demonstrate the API, plus a short overview of the codebase.
- **Performance**: API responds quickly; minimal calls to the external routing API.

## License

Assignment project; use as required by the hiring team.
