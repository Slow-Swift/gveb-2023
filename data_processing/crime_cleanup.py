import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

import utm

ZONE_NUMBER = 10
ZONE_LETTER = 'U'

from data_wrangler import Dataset
from data_wrangler.conversion_functions import generate_id
from data_wrangler.conversion_functions import RowFunction
from data_wrangler.conversion_functions import create_regular_str

JUNCTION_FILE = '../processed_data/junctions.csv'
DATA_2022 = '../original_data/crime_2022.csv'
DATA_2021 = '../original_data/crime_2021.csv'

junctions = Dataset.load_file(JUNCTION_FILE)
junctions.convert_property('id', int)
junctions.convert_property('longitude', float)
junctions.convert_property('latitude', float)
for junction in junctions:
    junction['crime_count'] = 0

properties = {
    'type': (str, 'TYPE'),
    
    # Creating a date field in format yyyy-mm-dd
    'date': RowFunction(lambda row, i: f"{row['YEAR']}-{create_regular_str(row['MONTH'])}-{create_regular_str(row['DAY'])}"),
    
    # Creating a time field in the format HH:MM
    'time': RowFunction(lambda row, i: f"{create_regular_str(row['HOUR'])}:{create_regular_str(row['MINUTE'])}"),
    'hundred_block': (str, 'HUNDRED_BLOCK'),
    
    # Determining latitude and longitude from utm location
    'latitude': RowFunction(lambda row, i: utm.to_latlon(float(row["X"]), float(row["Y"]), ZONE_NUMBER, ZONE_LETTER)[0] if row["X"] and float(row["X"]) else 0),
    'longitude': RowFunction(lambda row, i: utm.to_latlon(float(row["X"]), float(row["Y"]), ZONE_NUMBER, ZONE_LETTER)[1] if row["X"] and float(row["X"]) else 0),
}

crimes_2022 = Dataset.load_file(
    DATA_2022,
    { 'id': generate_id } | properties
)
maxid = max(crimes_2022._rows)

crimes_2021 = Dataset.load_file (
    DATA_2021,
    { 'id': RowFunction(lambda row, i: i + maxid + 1)}
)


crimes_2022.merge(crimes_2021)
crimes = crimes_2022

original_crime_number = len(crimes)
print(f"Collected {original_crime_number} crimes")
crimes.filter(lambda row: row['latitude'] != 0 or row['longitude'] != 0)
print(f"Filtered Null Locations. Remaining {len(crimes)} ({len(crimes) / original_crime_number:.0%})")

crimes.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='crime_count', distance_limit=200)
crimes.filter(lambda row: row['junction_id'] != 0)
print(f"Filteres No Connections. Remaining {len(crimes)} ({len(crimes) / original_crime_number:.0%})")

crimes.write_to_file('../processed_data/crime.csv')

junctions.write_to_file(JUNCTION_FILE)