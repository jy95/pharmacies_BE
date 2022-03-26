#!/usr/bin/python3
from haversine import haversine, Unit
from pathlib import Path
import json

# Files to read
PATH_AFMPS = Path("last-pharmacies_afmps.json")
PATH_OSM = Path("last-pharmacies_osm.json")
PATH_RESULT = Path("last-pharmacies_enhancedVersion.json")

# read json
def read_file(path):
    with open(str(path)) as file:
        return json.load(file)

# write json
def write_file(path, pharmacies):
    with open(str(path), "w", encoding='utf8') as outfile:
        json.dump(pharmacies, outfile, ensure_ascii=False)

# Data structure to make comparaison with OSM data faster
def generate_data_structure_osm(osm_list):
    return [
        (
            idx, 
            (
                row["geo"]["latitude"], 
                row["geo"]["longitude"]
            ),
            row, 
            False
        )
        for idx, row in enumerate(
            # Sorting now will spare iteration time for next run
            sorted(osm_list, key=lambda k: [k["geo"]["latitude"], k["geo"]["longitude"]])
        )
    ]

# Data structure to make comparaison with AFMPS data faster
def generate_data_structure_afmps(afmps_list):
    return [
        (
            # TODO change that quick later
            (
                pharmacy["geo"][1]["latitude"], 
                pharmacy["geo"][1]["longitude"]
            ),
            pharmacy
        )
        for pharmacy in sorted(
            afmps_list, key=lambda k: [k["geo"][1]["latitude"], k["geo"][1]["longitude"]]
        )
    ]

# To make final payload lighter without all this null values
def stripNone(data):
    if isinstance(data, dict):
        # No need to add "k is not None and" as my keys are not none for the moment
        return {k:stripNone(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [stripNone(item) for item in data if item is not None]
    elif isinstance(data, tuple):
        return tuple(stripNone(item) for item in data if item is not None)
    elif isinstance(data, set):
        return {stripNone(item) for item in data if item is not None}
    else:
        return data 

# Generator for building result
def combine_data(afmps, osm):
    # To make iteration faster for next runs 
    osm_list = generate_data_structure_osm(osm)
    afmps_list = generate_data_structure_afmps(afmps)
    # For the algorithm matching process (in meters)
    MAX_DISTANCE = 15
    
    for (afmps_coords, pharmacy) in afmps_list:
        # find index of first matching element
        # Hint : a pharmacy is a special kind of "business" : two pharmacies cannot be too close geographically speaking
        try:
            (pharmacy_osm_idx, osm_coords, pharmacy_osm) = next(
                (idx, osm_coords, pharmacy_osm)
                for (idx, osm_coords, pharmacy_osm, alreadyChecked) in osm_list
                if alreadyChecked is False and haversine(afmps_coords, osm_coords, unit=Unit.METERS) < MAX_DISTANCE
            )
            # we have a match ; cherry pick attributes
            pharmacy["names"] = pharmacy_osm["name"]
            pharmacy["contact"] = pharmacy_osm["contact"]
            pharmacy["geo"].append({
                "format": "epsg:4326", 
                "description": "WGS 84",
                "source": "https://www.openstreetmap.org/",
                "latitude": osm_coords[0],
                "longitude": osm_coords[1]
            })
            pharmacy["brand"] = pharmacy_osm["brand"]
            pharmacy["osm_opening_hours"] = pharmacy_osm["osm_opening_hours"]
            pharmacy["opening_hours"] = pharmacy_osm["opening_hours"]
            pharmacy["addresses"] = pharmacy_osm["addresses"]

            # Put flag to true so that we won't use that tuple anymore
            osm_list[pharmacy_osm_idx] = (None, None, None, True)

            # yield result
            yield pharmacy

        except StopIteration:
            # No match was found, return obj as it
            yield pharmacy

if __name__ == "__main__":
    # load files of json array
    print("Loading data ....")
    afmps = read_file(PATH_AFMPS)
    osm = read_file(PATH_OSM)
    # Combine data (& strip none I hate in json files)
    print("It's matching time")
    pharmacies = [
        stripNone(pharmacy)
        for pharmacy in combine_data(afmps, osm)
    ]
    # Save result
    print("Saving result")
    write_file(PATH_RESULT, pharmacies)