#!/usr/bin/python3
from pathlib import Path
from datetime import datetime
import json

# File to read
PATH_FILE = Path("last-pharmacies_enhancedVersion.json")

# File to write
PATH_RESULT = Path("pharmacies-%s.geojson" % datetime.today().strftime("%d-%m-%Y"))

# read json
def read_file(path):
    with open(str(path), encoding="utf8") as file:
        return json.load(file)

# write json
def write_file(path, geoJson):
    with open(str(path), "w", encoding='utf8') as outfile:
        json.dump(geoJson, outfile, ensure_ascii=False)

# Generator for building result
def generate_feature(pharmacy):
    # TODO change that quick later
    geo_afmps = pharmacy["geo"][1]

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
# In GeoJSON longitude is first
            "coordinates": [
                geo_afmps["longitude"],
                geo_afmps["latitude"]
            ]
        },
        "properties": {
            "name": pharmacy["name"],
            "status": pharmacy["status"],
            "contact": pharmacy.get("contact", None),
            "osm_opening_hours": pharmacy.get("osm_opening_hours", None),
            "authorization_id": pharmacy["authorization_id"],
            "authorization_holder": pharmacy["authorization_holder"],
            "operator": pharmacy["operator"],
            "zipCode": pharmacy["zipCode"]
        }
    }

def generate_geoJson(pharmacies):
    return {
        "type": "FeatureCollection",
        "features": [ generate_feature(pharmacy) for pharmacy in pharmacies ]
    }

if __name__ == "__main__":
    pharmacies = read_file(PATH_FILE)
    geoJson = generate_geoJson(pharmacies)
    write_file(PATH_RESULT, geoJson)