from pathlib import Path
from functools import cmp_to_key
from datetime import datetime, timezone
import shutil
import re

# Constants
DATA_STORAGE = Path("data_afmps")
LAST_PHARMACIES = Path("last-pharmacies_afmps.json")

if __name__ == "__main__":

    # Extract date from name : None if no match
    def extract_date(path):
        naming_pattern = "pharmacies-(?P<key>.+).json"
        name_match = re.match(naming_pattern, path.name)
        return datetime.strptime(name_match.group("key"), "%d-%m-%Y") if name_match else None

    # Sorting function
    def more_recent_first(file_tuple_a, file_tuple_b):
        # fallback use modification time if date couldn't extracted from name
        last_date = lambda file_tuple: file_tuple[0] if file_tuple[0] is not None else datetime.fromtimestamp(file_tuple[1].stat().st_mtime, tz=timezone.utc)
        # time to compare
        a_time = last_date(file_tuple_a)
        b_time = last_date(file_tuple_b)
        if a_time > b_time:
            return 1
        elif b_time > a_time:
            return -1
        else:
            return 0

    # Find the most recent tuple    
    recent_file = max(
        [ (extract_date(file), file) for file in DATA_STORAGE.glob('*.json')],
        key=cmp_to_key(more_recent_first),
        default=None
    )

    if recent_file is None:
        raise Exception("No matching file found")
    else:
        recent_file_path = recent_file[1]
        shutil.copyfile(recent_file_path,LAST_PHARMACIES)
