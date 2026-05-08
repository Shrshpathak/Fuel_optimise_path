# Fuel Route Optimizer API

A Django-based backend API that calculates the best fuel stops between two locations in the USA.

The system finds a driving route, analyzes nearby fuel stations from the provided dataset, and selects fuel stops in a cost-efficient way while respecting the vehicle’s fuel range.

---

# Project Overview

This project was built as part of a backend engineering assignment focused on:

* Route optimization
* Fuel cost calculation
* External API integration
* Performance-focused backend design
* Real-world decision-making logic

The API accepts a start and destination location inside the USA and returns:

* Total route distance
* Total fuel required
* Suggested fuel stops
* Fuel cost at each stop
* Total fuel expense
* Encoded route polyline for map rendering

The implementation uses:

* Django 6
* OpenRouteService API
* CSV-based fuel pricing dataset
* Greedy look-ahead fuel optimization logic

---

# Features

## Route Generation

Uses OpenRouteService to:

* Convert city names into coordinates
* Generate the driving route
* Return encoded route geometry

## Fuel Optimization

The planner selects fuel stations based on:

* Fuel price
* Distance from the route
* Vehicle range limit
* Future cheaper stations ahead on the route

## Cost Calculation

The API calculates:

* Fuel required for the full trip
* Gallons purchased at each stop
* Cost per stop
* Total fuel cost

## Performance Optimizations

To keep the API fast:

* Fuel station data is cached in memory
* Route polyline is sampled instead of checking every coordinate
* Only 3 routing API calls are used per request

---

# Vehicle Assumptions

| Property      | Value                   |
| ------------- | ----------------------- |
| Max Range     | 500 miles               |
| Mileage       | 10 MPG                  |
| Fuel Strategy | Cheapest reachable fuel |

---

# Project Structure

```bash
fuel/
│
├── fuel/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── routing/
│   ├── services.py
│   ├── utils.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── data/
│   ├── fuel_prices.csv
│   └── station_coords.json
│
├── manage.py
└── requirements.txt
```

---

# Main Components

## services.py

Contains the core business logic.

### RouteService

Responsible for:

* Geocoding locations
* Fetching route data
* Returning encoded route geometry

### FuelPlanner

Responsible for:

* Finding stations near the route
* Comparing fuel prices
* Choosing cost-effective stops
* Calculating total fuel cost

### _StationCache

Loads station data once and keeps it cached in memory for faster requests.

---

## utils.py

Contains helper functions.

### haversine()

Calculates straight-line distance between two GPS coordinates.

### build_route_mileposts()

Downsamples route coordinates to improve performance during station matching.

---

## views.py

Contains the API endpoint.

### plan_fuel_route

Handles:

* Request validation
* Route generation
* Fuel planning
* JSON response formatting

---

# API Endpoint

## Request

```http
POST /api/route/
```

## Sample Request Body

```json
{
  "start": "San Francisco",
  "end": "Las Vegas"
}
```

---

# Sample Response

```json
{
  "start": "San Francisco",
  "end": "Las Vegas",
  "distance_miles": 569.14,
  "total_gallons_needed": 56.91,
  "fuel_stops": [
    {
      "station": "Pilot Travel Center",
      "city": "Bakersfield",
      "state": "CA",
      "miles_from_start": 281.3,
      "price_per_gallon": 3.219,
      "gallons_added": 28.1,
      "stop_cost": 90.45
    }
  ],
  "total_fuel_cost": 183.92,
  "route_polyline": "encoded_polyline_here"
}
```

---

# Route Polyline

The API returns an encoded polyline string.

This can directly be used in:

* Google Maps
* Leaflet
* OpenRouteService
* Mapbox

The frontend can decode this polyline and draw the exact route on the map.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/Shrshpathak/Fuel_optimise_path.git
cd Fuel_optimise_path
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

### Mac/Linux

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Set OpenRouteService API Key

### Windows PowerShell

```powershell
$env:ORS_API_KEY="your_api_key"
```

### Linux/Mac

```bash
export ORS_API_KEY="your_api_key"
```

---

# Run Server

```bash
python manage.py runserver
```

---

# Testing with Postman

## Method

```http
POST
```

## URL

```http
http://127.0.0.1:8000/api/route/
```

## Headers

```json
Content-Type: application/json
```

## Body

```json
{
  "start": "San Francisco",
  "end": "Las Vegas"
}
```

---

# Performance Notes

The assignment specifically required minimizing external routing API usage.

This implementation uses:

1. One request for start geocoding
2. One request for destination geocoding
3. One request for route generation

Total:

* Only 3 API calls per request
* Within assignment limits

Additional optimizations:

* Cached station data
* Route downsampling
* Efficient greedy fuel selection

---

# Future Improvements

Some improvements that can be added later:

* Redis caching
* Async route processing
* Multi-vehicle support
* Real-time fuel pricing APIs
* Frontend map visualization
* Docker deployment
* PostgreSQL integration

---

# GitHub Push Commands

If GitHub repository is already created:

```bash
git init
```

```bash
git add .
```

```bash
git commit -m "Initial commit"
```

```bash
git branch -M main
```

```bash
git remote add origin https://github.com/Shrshpathak/Fuel_optimise_path.git
```

```bash
git push -u origin main --force
```

---

# Final Notes

This project focuses on practical backend engineering rather than only returning route data.

The goal was to simulate a real-world fuel planning workflow where route distance, fuel range, fuel prices, and future station pricing all affect the final decision.

The system is designed to remain simple, readable, and efficient while still handling realistic route planning scenarios.
