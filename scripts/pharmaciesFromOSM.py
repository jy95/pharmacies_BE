#!/usr/bin/python3
from pathlib import Path
from osmnx.features import features_from_place
import osm_opening_hours_humanized as hoh
# from shapely.geometry import mapping, Polygon, MultiPolygon

# from datetime import datetime
import json

DATA_STORAGE = Path("data_osm")

# Utility functions
def access_localised_tag(pharmacy, key, lang):
    if lang is not None:
        return pharmacy.get("{}:{}".format(key, lang), None)
    else:
        return pharmacy.get(key, None)
def find_first_not_none(pharmacy, keys):
    try:
        return next(
            pharmacy.get(key)
            for key in keys
            if pharmacy.get(key, None) is not None
        )
    except StopIteration:
        return None
# Some entries on OSM are not correctly encoded or it is my lib fault
def opening_hours_to_human(pharmacy, lang):
    try:
        return hoh.OHParser(pharmacy['opening_hours'], locale=lang).description()
    except Exception:
        return []
# Extracts latitude and longitude coordinates from a (Multi)Polygon.
def extract_coordinates(pharmacy):
    centroid = pharmacy.geometry.centroid
    coordinates = {
        "latitude": centroid.y,
        "longitude": centroid.x
    }
    return coordinates

# Extract contact links
def extract_contact(pharmacy):
    contact_info = {}
    
    phone = find_first_not_none(pharmacy, ["contact:phone", "phone"])
    if phone:
        contact_info["phone"] = phone

    email = find_first_not_none(pharmacy, ["contact:email", "email"])
    if email:
        contact_info["email"] = email

    fax = find_first_not_none(pharmacy, ["contact:fax", "fax"])
    if fax:
        contact_info["fax"] = fax

    website = find_first_not_none(pharmacy, ["contact:website", "website", "url"])
    if website:
        contact_info["website"] = website

    # other contact like "contact:facebook" not so useful in that context
    
    return contact_info

# Build results
def extract_pharmacies(pharmacies_result):
    # some keys used the language at the end
    LANGUAGES = ["fr", "nl", None]
    # build result
    return [
        {
            "name": [
                {
                    "lang": lang,
                    "value": access_localised_tag(pharmacy, "name", lang)
                }
                for lang in LANGUAGES
                if access_localised_tag(pharmacy, "name", lang) is not None
            ],
            "geo": extract_coordinates(pharmacy),
            "contact": extract_contact(pharmacy),
            # To track Multipharma & other channels
            "brand": pharmacy.get("brand"),
            # Opening hours of the pharmacy
            "osm_opening_hours": pharmacy.get("opening_hours"), # If user wants to translate that herself / himself
            "opening_hours": [
                {
                    "lang": lang,
                    "value": opening_hours_to_human(pharmacy, lang)
                }
                # languages values : https://github.com/rezemika/humanized_opening_hours#have-nice-schedules 
                for lang in ["fr", "nl", "de"]
                # Some pharmacies have just "closed" for that and so I must skip it
                if pharmacy.get("opening_hours") is not None and pharmacy.get("opening_hours") != "closed"
            ],
            # In Belgium, we could have multiples translation for address
            # If not localised info is found, use general attributs
            "addresses": [
                {
                    "lang": lang,
                    "street": access_localised_tag(
                        pharmacy, 
                        "addr:street", 
                        lang if lang is not None and pharmacy.get("addr:street:{}".format(lang)) else None
                    ),
                    "housenumber": pharmacy.get("addr:housenumber"),
                    "unit": pharmacy.get("addr:unit"),
                    "zipCode": pharmacy.get("addr:postcode"),
                    "city": access_localised_tag(
                        pharmacy, 
                        "addr:city", 
                        lang if lang is not None and pharmacy.get("addr:city:{}".format(lang)) else None
                    )
                }
                for lang in LANGUAGES
                # 
                if access_localised_tag(pharmacy, "addr:street", lang) is not None
            ]
        }
        for idx, pharmacy in pharmacies_result.iterrows()
    ]

def write_json_file(path, pharmacies):
    with open(str(path), "w", encoding='utf8') as outfile:
        json.dump(pharmacies, outfile, ensure_ascii=False)

if __name__ == "__main__":
    # prepare constants
    path_recent = Path("last-pharmacies_osm.json")
    # json_path = DATA_STORAGE / ("pharmacies-%s.json" % (datetime.today().strftime('%d-%m-%Y')))
    # Time to search
    pharmacies_result = features_from_place('Belgium', tags={'amenity': 'pharmacy'})
    # Build result
    pharmacies = extract_pharmacies(pharmacies_result)
    # Write result
    # write_json_file(json_path, pharmacies)
    write_json_file(path_recent, pharmacies)
