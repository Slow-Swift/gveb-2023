import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from ast import literal_eval

from data_wrangler import Dataset
from data_wrangler.conversion_functions import split_latitude, split_longitude

# NOTE: The reason I am using Dataset instead of Panda Dataframes is because I would have to work out how to match two Dataframes based on locations

INPUT_FOLDER = '../temp'
OUTPUT_FOLDER = '../cleaned_data'

CRIME = f'{INPUT_FOLDER}/crimes.csv'
JUNCTIONS = f'{INPUT_FOLDER}/junctions.csv'
SEGMENTS = f'{INPUT_FOLDER}/segments.csv'
STORES = f'{INPUT_FOLDER}/stores.csv'
TRANSIT = f'{INPUT_FOLDER}/transit.csv'
RAPID_TRANSIT = f'{INPUT_FOLDER}/rapid_transit.csv'
SCHOOLS = f'{INPUT_FOLDER}/schools.csv'

ZONE_NUMBER = 10
ZONE_LETTER = 'U'

print("Loading Data")
crime = Dataset.load_file(CRIME)
junctions = Dataset.load_file(JUNCTIONS)
segments = Dataset.load_file(SEGMENTS)
stores = Dataset.load_file(STORES)
transit = Dataset.load_file(TRANSIT)
rapid_transit = Dataset.load_file(RAPID_TRANSIT)
schools = Dataset.load_file(SCHOOLS)
print("Loaded Data")

starting_crime_count = len(crime)
starting_junction_count = len(junctions)
starting_segments_count = len(segments)
starting_stores_count = len(stores)
starting_transit_count = len(transit)
starting_rapid_transit_count = len(rapid_transit)
starting_schools_count = len(schools)

## Cleanup Junctions ##
print()
print(f"Initial junction count: {starting_junction_count}")
junctions.convert_properties({
    'id': int,
    'latitude': float,
    'longitude': float
})
junctions.add_property_default('neighbors', [])

## Cleanup Segments ##
print()
print(f"Initial segment count: {starting_segments_count}")
segments.convert_properties({
    'id': int,
    'length_metres': float,
    'neighbors': literal_eval
})

segments.filter(lambda row: len(row['neighbors']) >= 2)
print(f"Removed segments with less than 2 junctions. Remaining {len(segments)} ({len(segments)/starting_segments_count:.0%})")

# Match segments with junctions
for segment in segments:
    neighbors = segment['neighbors']
    for junction_id in neighbors:
        junction = junctions[junction_id]
        junction['neighbors'].extend([
            (neighbor_id, segment['length_metres'], segment['id']) for neighbor_id in neighbors if neighbor_id != junction_id
        ])
        
junctions.filter(lambda row: len(row['neighbors']) > 0)

print(f"Removed junctions with no connections. Remaining {len(junctions)} ({len(junctions) / starting_junction_count:.0%})")

## Cleanup Crimes ##
print()
print(f"Initial crime count: {starting_crime_count}")

crime.convert_properties({
    'id': int,
    'latitude': float,
    'longitude': float
})

# Filter out null locations
crime.filter(lambda row: row['latitude'] != 0 or row['longitude'] != 0)
print(f"Removed crimes with null locations. Remaining: {len(crime)} ({len(crime) / starting_crime_count:.0%})")
    
# Match to junctions
crime.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='crime_count', distance_limit=200)
crime.filter(lambda row: row['junction_id'] != 0)
print(f"Removed crimes more than 200 meters from a junction. Remaining {len(crime)} ({len(crime) / starting_crime_count:.0%})")


## Cleanup Store ##
print()
print(f"Initial Store Count {starting_stores_count}")

stores.convert_properties({
    'id': int,
    'store_id': int,
    'year_recorded': int,
    'latitude': float,
    'longitude': float
})

# Sort the stores based on year recorded and only keep the first one with a duplicate ID
IDs = set()
for row in sorted(stores, key=lambda row: row['year_recorded'], reverse=True):
    if int(row['store_id']) in IDs:
        stores.remove(row['id'])
    else:
        IDs.add(int(row['store_id']))
        
# Update the id property to use the actual store id
stores.rename('store_id', 'id')
stores.set_primary_key('id')
stores.drop('year_recorded')
        
print(f"Removed duplicate stores. Remaining {len(stores)} ({len(stores) / starting_stores_count:.0%})")

stores.filter(lambda store: store['category'] != 'Vacant')
print(f"Removed vacant stores. Remaining {len(stores)} ({len(stores) / starting_stores_count:.0%})")

stores.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='stores_count', distance_limit=200)
stores.filter(lambda row: row['junction_id'] != 0)
print(f"Removed stores with no connections. Remaining {len(stores)} ({len(stores) / starting_stores_count:.0%})")


## Cleanup Transit ##
print()
print(f"Initial transit count: {starting_transit_count}")

transit.convert_properties({
    'id': int,
    'latitude': float,
    'longitude': float
})

transit.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='transit_count', distance_limit=200)
transit.filter(lambda row: row['junction_id'] != 0)
print(f"Removed transit with no connections. Remaining {len(transit)} ({len(transit) / starting_transit_count:.0%})")


## Cleanup Rapid Transit ##
print()
print(f"Initial rapid transit count: {starting_rapid_transit_count}")

rapid_transit.convert_properties({
    'id': int,
    'latitude': float,
    'longitude': float
})

rapid_transit.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='rapid_transit_count', distance_limit=200)
rapid_transit.filter(lambda row: row['junction_id'] != 0)
print(f"Removed rapid transit with no connections. Remaining {len(rapid_transit)} ({len(rapid_transit) / starting_rapid_transit_count:.0%})")

## Cleanup Schools ##
print()
print(f"Initial school count: {starting_schools_count}")

schools.convert_properties({
    'id': int,
    'latitude': float,
    'longitude': float
})

schools.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='schools_count', distance_limit=200)
schools.filter(lambda row: row['junction_id'] != 0)
print(f"Removed schools with no connections. Remaining {len(schools)} ({len(schools) / starting_schools_count:.0%})")


## Write Data ##

junctions.write_to_file(f'{OUTPUT_FOLDER}/junctions.csv')
segments.write_to_file(f'{OUTPUT_FOLDER}/segments.csv')
crime.write_to_file(f'{OUTPUT_FOLDER}/crimes.csv')
stores.write_to_file(f'{OUTPUT_FOLDER}/stores.csv')
transit.write_to_file(f'{OUTPUT_FOLDER}/transit.csv')
rapid_transit.write_to_file(f'{OUTPUT_FOLDER}/rapid_transit.csv')
schools.write_to_file(f'{OUTPUT_FOLDER}/schools.csv')