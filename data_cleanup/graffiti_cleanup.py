### Connects the various data layers together and uses those connections to do some more filtering

import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from ast import literal_eval

import os
import utm

from data_wrangler import Dataset
from data_wrangler.conversion_functions import RowFunction
from data_wrangler.conversion_functions import generate_id
from data_wrangler.conversion_functions import create_regular_str
from data_wrangler.conversion_functions import split_latitude, split_longitude

# NOTE: The reason I am using Dataset instead of Panda Dataframes is because I would have to work out how to match two Dataframes based on locations

INPUT_FOLDER = '../data/original_data'
OUTPUT_FOLDER = '../data/cleaned_data'

GRAFFITI = f'{INPUT_FOLDER}/graffiti.csv'
OBSERVATIONS = f'{INPUT_FOLDER}/observations.csv'
JUNCTIONS = f'{OUTPUT_FOLDER}/junctions.csv'

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    
print("Pre-processing Graffiti")
graffiti = Dataset.load_file(
    GRAFFITI, 
    {
        'id': generate_id,
        'count': (int, "COUNT"),
        'area': (str, 'Geo Local Area'),
        
        # Getting lat and lon fom "lat, lon" format
        'latitude': (split_latitude, 'geo_point_2d'),
        'longitude': (split_longitude, 'geo_point_2d'),
    },
    delimiter=';'
)

print("Pre-processing Observations")
observations = Dataset.load_file(
    OBSERVATIONS, 
    {
        'id': (int, "id"),
        'patrol_id': (str, "patrol_id"),
        'datetime': (str, 'datetime'),
        'title': (str, 'title'),
        'description': (str, 'description'),
        'crime_likelihood': (int, 'likelihood_of_crime'),
        'crime_type': (int, 'type_of_crime_most_feared'),
        'crime_likelihood': (int, 'likelihood_of_crime'),
        'crime_type_description': (str, 'type_of_crime_other'),
        
        # Getting lat and lon fom "lat, lon" format
        'latitude': (float, 'lat'),
        'longitude': (float, 'long'),
    }
)

junctions = Dataset.load_file(JUNCTIONS)
junctions.convert_properties({
    'id': int,
    'latitude': float,
    'longitude': float
})


starting_graffiti_count = len(graffiti)
starting_observation_count = len(observations)

## Cleanup Graffiti ##
print()
print(f"Initial graffiti count: {starting_graffiti_count}")

graffiti.match_lat_lng(junctions, 'junction_id', 'junction_dst', count_field='graffiti_count', distance_limit=200, count_attrib='count')
graffiti.filter(lambda row: row['junction_id'] != 0)
print(f"Removed graffiti with no connections. Remaining {len(graffiti)} ({len(graffiti) / starting_graffiti_count:.0%})")

## Cleanup Observations ##
print()
print(f"Initial observation count: {starting_observation_count}")

def on_match(row_1, row_2, dst):
    row_1['junction_id'] = row_2[junctions.primary_key]
    row_1['junction_dst'] = dst
    
    row_2['observation_count'] = row_2['observation_count'] + 1
    if (row_1['crime_type'] == 1): row_2['theft_likelihood'] += row_1['crime_likelihood']
    if (row_1['crime_type'] == 2): row_2['mischief_likelihood'] += row_1['crime_likelihood']
    if (row_1['crime_type'] == 3): row_2['breakins_likelihood'] += row_1['crime_likelihood']
    if (row_1['crime_type'] == 4): row_2['assault_likelihood'] += row_1['crime_likelihood']
    if (row_1['crime_type'] == 5): row_2['other_likelihood'] += row_1['crime_likelihood']
    
for row in junctions:
    row['observation_count'] = 0
    row['theft_likelihood'] = 0
    row['mischief_likelihood'] = 0
    row['breakins_likelihood'] = 0
    row['assault_likelihood'] = 0
    row['other_likelihood'] = 0

observations.match_lat_lng_custom(junctions, on_match=on_match, distance_limit=200)
#observations.match_lat_lng(junctions, 'junction_id', 'junction_dst', count_field='observation_count', distance_limit=200)
observations.filter(lambda row: row['junction_id'] != 0)
print(f"Removed observations with no connections. Remaining {len(observations)} ({len(observations) / starting_observation_count:.0%})")

for row in junctions:
    c = row['observation_count']
    if c == 0: continue
    row['theft_likelihood'] /= c
    row['mischief_likelihood'] /= c
    row['breakins_likelihood'] /= c
    row['assault_likelihood'] /= c
    row['other_likelihood'] /= c

junctions.write_to_file(f'{OUTPUT_FOLDER}/junctions.csv')
graffiti.write_to_file(f'{OUTPUT_FOLDER}/graffiti.csv')
observations.write_to_file(f'{OUTPUT_FOLDER}/observations.csv')