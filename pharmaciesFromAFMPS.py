from pyproj import CRS, Transformer
import pandas as pd
from urllib.request import urlopen
from pathlib import Path
import re
from datetime import datetime
from openpyxl import load_workbook
import json
import numpy as np

# Constants
FILENAME = "Lst_Pharmacies_pub_Extended.xlsx"
FETCH_URL = "https://www.fagg.be/sites/default/files/content/INSP/OFFICINES/Lst_Pharmacies_pub_Extended.xlsx"
DATA_STORAGE = "data_afmps"

# Download recent file from afmps
def download_afmps_file(path):
    # Download from URL
    with urlopen(FETCH_URL) as webpage:
        content = webpage.read()
        # Save to file
        with open(path, 'wb') as download:
            download.write(content)

# Get Last-Modified from AFMPS
def get_afmps_last_modified():
    with urlopen(FETCH_URL) as webpage:
        raw_string = webpage.getheader("Last-Modified")
        last_modified_pattern = "%a, %d %b %Y %H:%M:%S GMT"
        return datetime.strptime(raw_string, last_modified_pattern).astimezone()

# Get Modification date from file, if exist
# I have to rely on Excel metadata (when the author indeed created that file & not when I downloaded it)
def get_file_last_modified(path):
    if not path.exists():
        return None
    else:
        wb = load_workbook(str(path))
        # https://openpyxl.readthedocs.io/en/stable/api/openpyxl.packaging.core.html?highlight=lastModifiedBy#module-openpyxl.packaging.core 
        # print(wb.properties.lastModifiedBy)
        return wb.properties.modified.astimezone()

# Read 
def read_footer_from_afmps_file(path, rows):
    # rows + 2 as we must count the header in skiprows
    return pd.read_excel(path, nrows=1, skiprows=rows+2, header=None).iat[0, 0]

def extract_pharmacies_from_afmps(path):
    # First & Last row in excel file are useless for this part
    df = pd.read_excel(path, skiprows=[0], skipfooter=1)
    # Footer is needed for temporary suspension date to be extracted
    footer = read_footer_from_afmps_file(path, len(df.index))
    update_pattern = "\(.*update\s:\s(?P<update_date>.+)\)"
    update_date_match = re.search(update_pattern, footer)
    update_date = update_date_match.group("update_date") if update_date_match else datetime.today().strftime("%d-%m-%Y")
    # Rename columns to make them dev friendly
    df.columns = [
        "authorization_id",
        "name",
        "textual_address",
        "zipCode",
        "municipality",
        "status",
        "authorization_holder",
        "operator",
        "lambert2008_x",
        "lambert2008_y"
    ]
    # Regex to extract name & entreprise number (always present)
    naming_pattern = "(?P<name>.+)\s\(KBO-BCE\s:\s(?P<cbe>.+)\)"

    # Time to build result
    results = []
    print("\t Found %d pharmacie(s)" % (len(df.index)))
    for idx in df.index:
        # Lambert 2008 to WGS 84
        lat, long = lambert_2008_2_wgs_84(
            df["lambert2008_x"][idx],
            df["lambert2008_y"][idx]
        )
        # Extract holder / operator info
        # For operator, it is most of the time identical to the holder ("Idem")
        match_holder = re.match(naming_pattern, df["authorization_holder"][idx])
        holder_info = match_holder.groupdict() if match_holder else {}
        match_operator = re.match(naming_pattern, df["operator"][idx])
        operator_info = match_operator.groupdict() if match_operator else holder_info
        # common properties
        pharmacy = {
            "authorization_id": df["authorization_id"][idx],
            "name": df["name"][idx],
            "textual_address": df["textual_address"][idx],
            "zipCode": df["zipCode"][idx],
            "municipality": df["municipality"][idx],
            "geo": [
                {
                    "format": "epsg:3812",
                    "description": "Belgian Lambert 2008",
                    "source": "https://www.ngi.be/",
                    "x": df["lambert2008_x"][idx],
                    "y": df["lambert2008_y"][idx]
                },
                {
                    "format": "epsg:4326",
                    "description": "WGS 84",
                    "source": "https://gisgeography.com/wgs84-world-geodetic-system/",
                    "latitude": lat,
                    "longitude": long 
                }
            ],
            "authorization_holder": {
                "name": holder_info.get("name", None),
                "entreprise_number": holder_info.get("cbe", None)
            },
            "operator": {
                "name": operator_info.get("name", None),
                "entreprise_number": operator_info.get("cbe", None)
            },
            "status": "ACTIVE" if df["status"][idx] is None else "TEMPORARILY_SUSPENDED"
        }

        # store pharmacy in result set
        results.append(pharmacy)

    return update_date, results

# Dump pharmacies into a json
def pharmacies_2_json(json_path, pharmarcies):
    # Needed as pandas somehow converted python types to numpy types
    # Credits to https://stackoverflow.com/a/57915246/6149867 
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NpEncoder, self).default(obj)
    # Finally the work
    with open(str(json_path), "w") as outfile:
        json.dump(pharmarcies, outfile, cls=NpEncoder)

# Function to turn Lambert 2008 to WGS 84 (lat, long)
def lambert_2008_2_wgs_84(x, y):
    # EPSG:3812 ETRS89 / Belgian Lambert 2008 
    lambert2008 = CRS('epsg:3812')
    # EPSG:4326 WGS 84
    wgs84 = CRS('epsg:4326')
    transformer = Transformer.from_crs(lambert2008, wgs84)
    return transformer.transform(x, y)

if __name__ == "__main__":
    path_afmps = Path(FILENAME)
    path_data = Path(DATA_STORAGE)

    try:
        print("Checking if newer version was published")
        afmps_last_modified = get_afmps_last_modified()
        file_last_modified = get_file_last_modified(path_afmps)
        print("\t HTTP AFMPS Last-Modified : %s" % (afmps_last_modified))
        print("\t Local file Last-Modified : %s" % (file_last_modified))
        if afmps_last_modified > file_last_modified:
            print("Fetching XLSX file from AFMPS ...")
            download_afmps_file(path_afmps)
            print("Extracting pharmacies from XLSX file")
            update_date, pharmacies = extract_pharmacies_from_afmps(path_afmps)
            print("Saving pharmacies into a JSON file ...")
            json_path = path_data / ("pharmacies-%s.json" % (update_date))
            pharmacies_2_json(json_path, pharmacies)
            print("File successfully created")

        else:
            print("No changes since last pull - Stopping the script ...")

    except Exception as e:
        print(e)