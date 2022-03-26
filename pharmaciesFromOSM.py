#!/usr/bin/python3
from pathlib import Path
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import Overpass, overpassQueryBuilder
#import humanized_opening_hours as hoh
import osm_opening_hours_humanized as hoh
# from datetime import datetime
import json

DATA_STORAGE = Path("data_osm")

# Lookup for Belgium area ID
def lookup_belgium():
    nominatim = Nominatim()
    return nominatim.query("Belgium")

# Query for pharmacies in Belgium
def build_query(belgium):
    return overpassQueryBuilder(
        area=belgium.areaId(),
        # In Belgium, pharmacies are only described with node & way
        elementType=["node", "way"],
        selector=[
            '"healthcare"="pharmacy"'#,'"opening_hours"'
        ],
        out='body'
    )

# Build results
def extract_pharmacies(pharmacies_result):
    # some keys used the language at the end
    LANGUAGES = ["fr", "nl", None]
    # Utility functions
    def access_localised_tag(pharmacy, key, lang):
        if lang is not None:
            return pharmacy.tag("{}:{}".format(key, lang))
        else:
            return pharmacy.tag(key)
    def find_first_not_none(pharmacy, keys):
        try:
            return next(
                pharmacy.tag(key)
                for key in keys
                if pharmacy.tag(key) is not None
            )
        except StopIteration:
            return None
    # Some entries on OSM are not correctly encoded or it is my lib fault
    def opening_hours_to_human(pharmacy, lang):
        try:
            return hoh.OHParser(pharmacy.tag("opening_hours"), locale=lang).description()
        except Exception:
            return []
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
            "geo": {
                # For Node, it is straightforward to get lat / lon but not for way 
                "latitude": pharmacy.lat() if pharmacy.type() == "node" else pharmacy.nodes()[0].lat(),
                "longitude": pharmacy.lon() if pharmacy.type() == "node" else pharmacy.nodes()[0].lon()
            },
            "contact": {
                # Contact could be put in alternative keys
                "phone": find_first_not_none(pharmacy, ["contact:phone", "phone"]),
                "email": find_first_not_none(pharmacy, ["contact:email", "email"]),
                "fax": find_first_not_none(pharmacy, ["contact:fax", "fax"]),
                "website": find_first_not_none(pharmacy, ["contact:website", "website", "url"])
                # other contact like "contact:facebook" not so useful in that context
            },
            # To track Multipharma & other channels
            "brand": pharmacy.tag("brand"),
            # Opening hours of the pharmacy
            "osm_opening_hours": pharmacy.tag("opening_hours"), # If user wants to translate that herself / himself
            "opening_hours": [
                {
                    "lang": lang,
                    "value": opening_hours_to_human(pharmacy, lang)
                }
                # languages values : https://github.com/rezemika/humanized_opening_hours#have-nice-schedules 
                for lang in ["fr", "nl", "de"]
                # Some pharmacies have just "closed" for that and so I must skip it
                if pharmacy.tag("opening_hours") is not None and pharmacy.tag("opening_hours") != "closed"
            ],
            # In Belgium, we could have multiples translation for address
            # If not localised info is found, use general attributs
            "addresses": [
                {
                    "lang": lang,
                    "street": access_localised_tag(
                        pharmacy, 
                        "addr:street", 
                        lang if lang is not None and pharmacy.tag("addr:street:{}".format(lang)) else None
                    ),
                    "housenumber": pharmacy.tag("addr:housenumber"),
                    "unit": pharmacy.tag("addr:unit"),
                    "zipCode": pharmacy.tag("addr:postcode"),
                    "city": access_localised_tag(
                        pharmacy, 
                        "addr:city", 
                        lang if lang is not None and pharmacy.tag("addr:city:{}".format(lang)) else None
                    )
                }
                for lang in LANGUAGES
                # 
                if access_localised_tag(pharmacy, "addr:street", lang) is not None
            ]
        }
        for pharmacy in pharmacies_result.elements()
    ]

def write_json_file(path, pharmacies):
    with open(str(path), "w", encoding='utf8') as outfile:
        json.dump(pharmacies, outfile, ensure_ascii=False)

if __name__ == "__main__":
    # prepare constants
    path_recent = Path("last-pharmacies-osm.json")
    # json_path = DATA_STORAGE / ("pharmacies-%s.json" % (datetime.today().strftime('%d-%m-%Y')))
    belgium = lookup_belgium()
    # Query for pharmacies in Belgium
    query = build_query(belgium)
    # Time to search
    overpass = Overpass()
    pharmacies_result = overpass.query(query)
    # Build result
    pharmacies = extract_pharmacies(pharmacies_result)
    # Write result
    # write_json_file(json_path, pharmacies)
    write_json_file(path_recent, pharmacies)
