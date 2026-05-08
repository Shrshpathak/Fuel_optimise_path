"""
Run ONCE: python manage.py geocode_stations
Uses OpenStreetMap Nominatim — free, no API key, no ORS calls.
Resumes automatically if interrupted.
"""

import os, json, time
import requests
import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "One-time geocoding using OpenStreetMap (free, no API key)"

    def handle(self, *args, **kwargs):
        root = self._project_root()
        csv_path = os.path.join(root, "data", "fuel_prices.csv")
        cache_path = os.path.join(root, "data", "station_coords.json")

        df = pd.read_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]
        df["City"] = df["City"].str.strip()
        df["State"] = df["State"].str.strip()
        df = df.dropna(subset=["City", "State"])
        pairs = df[["City", "State"]].drop_duplicates().values.tolist()
        total = len(pairs)

        
        coords = {}
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                coords = json.load(f)
            self.stdout.write(f"Resuming from {len(coords)}/{total}\n")

        failed = 0
        for i, (city, state) in enumerate(pairs):
            key = f"{city},{state}"
            if key in coords:
                continue
            try:
                lat, lon = self._geocode(city, state)
                coords[key] = [lat, lon]
                self.stdout.write(f"  [{i+1}/{total}] {key} → {lat:.4f}, {lon:.4f}")
            except Exception as e:
                failed += 1
                self.stdout.write(f"  [{i+1}/{total}] {key} → skipped ({e})")

            if (i + 1) % 50 == 0:
                self._save(coords, cache_path)

            time.sleep(1.1)  

        self._save(coords, cache_path)
        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {len(coords)} geocoded, {failed} skipped."
        ))

    def _geocode(self, city, state):
       
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{city}, {state}, USA", "format": "json", "limit": 1, "countrycodes": "us"},
            headers={"User-Agent": "fuel-routing-app/1.0"},  
            timeout=10,
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            raise ValueError("not found")
        return float(results[0]["lat"]), float(results[0]["lon"])

    def _save(self, data, path):
        with open(path, "w") as f:
            json.dump(data, f)

    def _project_root(self):
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )