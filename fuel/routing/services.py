

import json
import os

import pandas as pd
import polyline
import requests

from .utils import build_route_mileposts, haversine

# ORS_KEY = os.environ.get("eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImM1MjEyYjU2ODBhYjQ4NWRhNWQ0MDViNGY2NWY5YWE0IiwiaCI6Im11cm11cjY0In0=")
ORS_BASE_URL = "https://api.openrouteservice.org"
ORS_KEY = os.environ.get(
    "ORS_API_KEY",
    "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImM1MjEyYjU2ODBhYjQ4NWRhNWQ0MDViNGY2NWY5YWE0IiwiaCI6Im11cm11cjY0In0="
)
MAX_RANGE_MILES = 500
VEHICLE_MPG = 10
ROUTE_SEARCH_RADIUS = 25


class _StationCache:
    """
    Simple in-memory cache for station data.
    Loads station pricing and coordinates once.
    """

    stations = None

    @classmethod
    def get(cls):
        if cls.stations is None:
            cls.stations = cls._load_stations()
        return cls.stations

    @classmethod
    def _load_stations(cls):
        base_dir = cls._get_project_root()

        csv_path = os.path.join(base_dir, "data", "fuel_prices.csv")
        coords_path = os.path.join(base_dir, "data", "station_coords.json")

        fuel_df = pd.read_csv(csv_path)

        fuel_df.columns = [col.strip() for col in fuel_df.columns]
        fuel_df["City"] = fuel_df["City"].str.strip()
        fuel_df["State"] = fuel_df["State"].str.strip()

        fuel_df = fuel_df.dropna(
            subset=["City", "State", "Retail Price"]
        )

        station_coords = {}

        if os.path.exists(coords_path):
            with open(coords_path, "r") as f:
                station_coords = json.load(f)

        stations = []

        for _, row in fuel_df.iterrows():
            location_key = f"{row['City']},{row['State']}"

            if location_key not in station_coords:
                continue

            lat, lon = station_coords[location_key]

            stations.append({
                "name": row["Truckstop Name"].strip(),
                "city": row["City"],
                "state": row["State"],
                "price": float(row["Retail Price"]),
                "lat": float(lat),
                "lon": float(lon),
            })

        print(f"Loaded {len(stations)} fuel stations")

        return stations

    @classmethod
    def _get_project_root(cls):
        return os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )


class RouteService:
    """Handles geocoding and route generation using ORS."""

    def geocode(self, location):
        response = requests.get(
            f"{ORS_BASE_URL}/geocode/search",
            params={
                "api_key": ORS_KEY,
                "text": f"{location}, USA",
                "boundary.country": "US",
                "size": 1,
            },
            timeout=10,
        )

        response.raise_for_status()

        features = response.json().get("features", [])

        if not features:
            raise ValueError(f"Location not found: '{location}'")

        lon, lat = features[0]["geometry"]["coordinates"]

        return float(lat), float(lon)

    def get_route(self, start_coords, end_coords):
        response = requests.post(
            f"{ORS_BASE_URL}/v2/directions/driving-car",
            json={
                "coordinates": [
                    [start_coords[1], start_coords[0]],
                    [end_coords[1], end_coords[0]],
                ]
            },
            headers={
                "Authorization": ORS_KEY,
                "Content-Type": "application/json",
            },
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        if "routes" not in data:
            raise ValueError(
                f"ORS routing error: {data.get('error', data)}"
            )

        route = data["routes"][0]

        encoded_polyline = route["geometry"]

        decoded_points = polyline.decode(encoded_polyline)

        distance_miles = (
            route["summary"]["distance"] / 1609.34
        )

        return decoded_points, distance_miles, encoded_polyline


class FuelPlanner:
    """
    Plans fuel stops based on station pricing and vehicle range.

    If a cheaper station is available ahead within range,
    the planner only buys enough fuel to reach it.
    """

    def __init__(self):
        self.stations = _StationCache.get()

    def _find_route_stations(self, route_points):
        route_samples = build_route_mileposts(
            route_points,
            sample_every=6,
        )

        matched_stations = {}

        for route_lat, route_lon, route_miles in route_samples:

            for station in self.stations:

                distance_from_route = haversine(
                    route_lat,
                    route_lon,
                    station["lat"],
                    station["lon"],
                )

                if distance_from_route > ROUTE_SEARCH_RADIUS:
                    continue

                station_key = (
                    round(station["lat"], 4),
                    round(station["lon"], 4),
                )

                existing_station = matched_stations.get(station_key)

                if (
                    existing_station is None
                    or existing_station["route_distance"] > route_miles
                ):
                    matched_stations[station_key] = {
                        **station,
                        "route_distance": route_miles,
                    }

        return sorted(
            matched_stations.values(),
            key=lambda station: station["route_distance"]
        )

    def plan(self, route_points, total_distance):
        stations_on_route = self._find_route_stations(route_points)

        if not stations_on_route:
            return [], 0.0

        current_position = 0.0
        fuel_left = MAX_RANGE_MILES

        total_cost = 0.0
        fuel_stops = []

        remaining_stations = list(stations_on_route)

        while current_position < total_distance:

            if current_position + fuel_left >= total_distance:
                break

            reachable_stations = [
                station
                for station in remaining_stations
                if current_position < station["route_distance"]
                <= current_position + fuel_left
            ]

            if not reachable_stations:
                future_stations = [
                    station
                    for station in remaining_stations
                    if station["route_distance"] > current_position
                ]

                if not future_stations:
                    break

                reachable_stations = [future_stations[0]]

            next_stop = min(
                reachable_stations,
                key=lambda station: station["price"]
            )

            miles_to_station = (
                next_stop["route_distance"] - current_position
            )

            fuel_left_after_drive = (
                fuel_left - miles_to_station
            )

            max_reach = (
                next_stop["route_distance"] + MAX_RANGE_MILES
            )

            cheaper_stations = [
                station
                for station in remaining_stations
                if (
                    next_stop["route_distance"]
                    < station["route_distance"]
                    <= max_reach
                )
                and station["price"] < next_stop["price"]
            ]

            if cheaper_stations:
                next_cheapest = min(
                    cheaper_stations,
                    key=lambda station: station["price"]
                )

                required_miles = (
                    next_cheapest["route_distance"]
                    - next_stop["route_distance"]
                    + 30
                )

                refill_miles = max(
                    0.0,
                    min(
                        required_miles - fuel_left_after_drive,
                        MAX_RANGE_MILES - fuel_left_after_drive,
                    )
                )

            else:
                refill_miles = (
                    MAX_RANGE_MILES - fuel_left_after_drive
                )

            if refill_miles <= 0:
                remaining_stations = [
                    station
                    for station in remaining_stations
                    if station["route_distance"]
                    > next_stop["route_distance"]
                ]

                current_position = next_stop["route_distance"]
                fuel_left = fuel_left_after_drive

                continue

            gallons_needed = refill_miles / VEHICLE_MPG

            stop_cost = round(
                gallons_needed * next_stop["price"],
                2,
            )

            fuel_stops.append({
                "station": next_stop["name"],
                "city": next_stop["city"],
                "state": next_stop["state"],
                "lat": round(next_stop["lat"], 6),
                "lon": round(next_stop["lon"], 6),
                "miles_from_start": round(
                    next_stop["route_distance"],
                    1,
                ),
                "price_per_gallon": round(
                    next_stop["price"],
                    3,
                ),
                "gallons_added": round(
                    gallons_needed,
                    2,
                ),
                "stop_cost": stop_cost,
            })

            total_cost += stop_cost

            fuel_left = (
                fuel_left_after_drive + refill_miles
            )

            current_position = next_stop["route_distance"]

            remaining_stations = [
                station
                for station in remaining_stations
                if station["route_distance"] > current_position
            ]

        return fuel_stops, round(total_cost, 2)