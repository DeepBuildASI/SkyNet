# A818SN - City Loader
# Downloads world cities from public dataset

import requests
import json

CITY_DATA_URL = "https://raw.githubusercontent.com/joelacus/world-cities/main/world_cities.json"

def load_cities():
    print("Downloading world cities database...")
    response = requests.get(CITY_DATA_URL)
    response.raise_for_status()
    raw = response.json()
    
    cities = {}
    for entry in raw:
        name = entry["name"]
        lat = float(entry["lat"])
        lon = float(entry["lng"])
        cities[name] = (lat, lon)
    
    print(f"Loaded {len(cities)} cities.")
    return cities

if __name__ == "__main__":
    cities = load_cities()
    print("Sample:", list(cities.items())[:5])