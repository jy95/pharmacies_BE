#!/usr/bin/python3

import argparse
from pathlib import Path
import json
from datetime import datetime
import re

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
        "Brussels": lambda zipCode : BXL(zipCode),
        "Flanders": lambda zipCode : VL(zipCode),
        "Wallonia": lambda zipCode : WL(zipCode)
    }.get(region, lambda _: False)


def main(argv):
    inputfile = argv.get("input")
    outputfile = argv.get("output")

    if not inputfile.exists():
        raise Exception("Input file doesn't exist")
    
    # If first time the script is run
    stats = {} if not outputfile.exists() else None
    if stats is None:
        with open(outputfile) as file:
            stats = json.load(file)
    
    # Read input file & turn it into a list of dict
    inputfile_dict = []
    with open(inputfile) as file:
        inputfile_dict = json.load(file)

    # Find key
    # If cannot be found, I made the assumption is something like "08-03-2022"
    name = inputfile.name
    naming_pattern = "pharmacies-(?P<key>.+).json"
    name_match = re.match(naming_pattern, name)
    key = name_match.group("key") if name_match else datetime.today().strftime("%d-%m-%Y")

    # Compute stats

    statsByZipCode = {}

    # Create / Update entry
    stats[key] = {
        # Needed for later reading
        "sourceFile": name,
        # For modification tracking
        "lastModification": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        # Stats for Brussels
        "Brussels": {
            "total_pharmacies": 0,
            "active_pharmacies": 0,
            "temporarily_suspended_pharmacies": 0
        },
        # Stats for Flanders
        "Flanders": {
            "total_pharmacies": 0,
            "active_pharmacies": 0,
            "temporarily_suspended_pharmacies": 0
        },
        # Stats for Wallonia
        "Wallonia": {
            "total_pharmacies": 0,
            "active_pharmacies": 0,
            "temporarily_suspended_pharmacies": 0
        },
        "statsByZipCode": statsByZipCode
    }

    # Store result
    # TODO

if __name__ == "__main__":
    parser = setUpParser()
    argv = parser.parse_args()
    try:
        main(argv)
    except Exception as e:
        print(e)
        exit(42)