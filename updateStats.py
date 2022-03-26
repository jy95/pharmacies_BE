#!/usr/bin/python3

import argparse
from pathlib import Path
import json
from datetime import datetime
from itertools import groupby
import re

# Constants
REGIONS = ["Brussels", "Flanders", "Wallonia"]

def setUpParser():
    defaultOutput = Path("stats.json")
    parser = argparse.ArgumentParser(description="Update statistics file for analysis")
    parser.add_argument("-i", "--inputFile", dest="input", type=Path, required=True, help="Input file for the script")
    parser.add_argument("-o", "--outputFile", dest="output", type=Path, required=False, default=defaultOutput, help="Output file where to save result of the script")
    return parser

# Return condition to match region
def zipCodeCondition(region):

    between = lambda zipCode, start, end : start <= zipCode <= end
    # Thanks Wikipedia
    # https://fr.wikipedia.org/wiki/Liste_des_codes_postaux_belges
    BXL = lambda zipCode : between(zipCode, 1000, 1299)
    WL = lambda zipCode : between(zipCode, 1300, 1499) or between(zipCode, 4000, 7999)
    VL = lambda zipCode : between(zipCode, 1500, 3999) or between(zipCode, 8000, 9999)
    
    return {
        # Brussels
        REGIONS[0]: lambda zipCode : BXL(zipCode),
        # Flanders
        REGIONS[1]: lambda zipCode : VL(zipCode),
        # Wallonia
        REGIONS[2]: lambda zipCode : WL(zipCode)
    }.get(region, lambda _: False)

def generate_stats_for_each_zipCode(list_of_pharmacies):

    # Sort by zipCode then by authorization_id
    sorted_pharmacies = sorted(list_of_pharmacies, key= lambda x: (x["zipCode"], x["authorization_id"]))
    # Key function
    key_func = lambda x: x["zipCode"]
    statsByZipCode = {}
    for key, group in groupby(sorted_pharmacies, key_func):
        items = list(group)
        # For user friendly 
        municipality = items[0]["municipality"] if len(items) > 0 else None
        statsByZipCode[key] = {
            "municipality": municipality,
            "total_pharmacies": len(items),
            "active_pharmacies": sum(1 for _ in filter(lambda x: x["status"].casefold() == "active", items)),
            "temporarily_suspended_pharmacies": sum(1 for _ in filter(lambda x: x["status"].casefold() == "temporarily_suspended", items))
        }

    # Sorted pharmacies so that stats for each region is fast
    return statsByZipCode

def main(argv):
    inputfile = argv.input
    outputfile = argv.output

    if not inputfile.exists():
        raise Exception("Input file doesn't exist")
    
    # If first time the script is run
    stats = {} if not outputfile.exists() else None
    if stats is None:
        with open(outputfile) as file:
            stats = json.load(file)
    
    # Read input file & turn it into a list of dict
    inputfile_list = []
    with open(inputfile) as file:
        inputfile_list = json.load(file)

    # Find key
    # If cannot be found, I made the assumption is something like "08-03-2022"
    name = inputfile.name
    naming_pattern = "pharmacies-(?P<key>.+).json"
    name_match = re.match(naming_pattern, name)
    key = name_match.group("key") if name_match else datetime.today().strftime("%d-%m-%Y")

    # Compute stats
    statsByZipCode = generate_stats_for_each_zipCode(inputfile_list)

    stats[key] = {
        # Needed for later reading
        "sourceFile": name,
        # For modification tracking
        "lastModification": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "statsByZipCode": statsByZipCode
    }
    # Compute stats for each region
    for zipCode, stats_by_zipCode in statsByZipCode.items():
        # Find out in which region this zipCode is
        matching_regions = filter(lambda region: zipCodeCondition(region)(zipCode), REGIONS)
        # At least one must match
        region = next(matching_regions)

        # Initial step for reducer
        stats_for_region = stats[key].get(region, {
            "total_pharmacies": 0,
            "active_pharmacies": 0,
            "temporarily_suspended_pharmacies": 0
        })

        # Update counters
        stats_for_region["total_pharmacies"] += stats_by_zipCode["total_pharmacies"]
        stats_for_region["active_pharmacies"] += stats_by_zipCode["active_pharmacies"]
        stats_for_region["temporarily_suspended_pharmacies"] += stats_by_zipCode["temporarily_suspended_pharmacies"]
        # Store result
        stats[key][region] = stats_for_region

    # Store result
    with open(str(outputfile), "w", encoding='utf8') as outfile:
        json.dump(stats, outfile, ensure_ascii=False)

if __name__ == "__main__":
    parser = setUpParser()
    argv = parser.parse_args()
    try:
        main(argv)
        print("Statistics file successfully updated")
    except Exception as e:
        print(e)
        exit(42)