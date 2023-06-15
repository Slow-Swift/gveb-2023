import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

import utm

from data_wrangler import Dataset
from data_wrangler.conversion_functions import split_latitude, split_longitude

# NOTE: The reason I am using Dataset instead of Panda Dataframes is because I would have to work out how to match two Dataframes based on locations

CRIME_2021 = '../original_data/crime_2021.csv'
CRIME_2022 = '../original_data/crime_2022.csv'
JUNCTIONS = '../original_data/junctions.csv'
SEGMENTS = '../original_data/streetsegments.csv'
STORES = '../original_data/storefronts-inventory.csv'
TRANSIT = '../original_data/transitstops.csv'
RAPID_TRANSIT = '../original_data/rapid-transit-stations.csv'
SCHOOLS = '../original_data/schools.csv'

ZONE_NUMBER = 10
ZONE_LETTER = 'U'

print("Loading Data")
crime_2022 = Dataset.load_file(CRIME_2022, primary_key_start=1)
crime_2021 = Dataset.load_file(CRIME_2021, primary_key_start=len(crime_2022) + 1)
junctions = Dataset.load_file(JUNCTIONS, primary_key="JunctionID")
segments = Dataset.load_file(SEGMENTS, primary_key="StreetID")
stores = Dataset.load_file(STORES, delimiter=';')
transit = Dataset.load_file(TRANSIT, primary_key='stop_id')
rapid_transit = Dataset.load_file(RAPID_TRANSIT, delimiter=';', primary_key_start=1)
schools = Dataset.load_file(SCHOOLS, delimiter=';', primary_key_start=1)

crime_2022.merge(crime_2021)
crime = crime_2022
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
junctions.rename('JunctionID', 'id')
junctions.rename('StreetIntersectCount', 'street_count')
junctions.rename('JunctionType', 'type')
junctions.drop('Vulnerability')
junctions.convert_properties({
    'id': int,
    'latitude': float,
    'longitude': float
})
junctions.add_property_default('neighbors', [])

## Cleanup Segments ##
print()

segments.rename('StreetID', 'id')
segments.rename('streetType', 'type')
segments.rename('PropertyCount', 'property_count')
segments.rename('Avg_CURRENT_LAND_VALUE', 'current_land_val_avg')
segments.rename('SD_CURRENT_LAND_VALUE', 'current_land_val_sd')
segments.rename('Avg_CURRENT_IMPROVEMENT_VALUE', 'current_improvement_avg')
segments.rename('SD_CURRENT_IMPROVEMENT_VALUE', 'current_improvement_sd')
segments.rename('Avg_ASSESSMENT_YEAR', 'year_assessment_avg')
segments.rename('Avg_PREVIOUS_LAND_VALUE', 'prev_land_val_avg')
segments.rename('SD_PREVIOUS_LAND_VALUE', 'prev_land_val_sd')
segments.rename('Avg_PREVIOUS_IMPROVEMENT_VALUE', 'prev_improv_val_avg')
segments.rename('SD_PREVIOUS_IMPROVEMENT_VALUE', 'prev_improv_val_sd')
segments.rename('Avg_YEAR_BUILT', 'year_built_avg')
segments.rename('SD_YEAR_BUILT', 'year_built_sd')
segments.rename('Avg_BIG_IMPROVEMENT_YEAR', 'big_improvement_yr_avg')
segments.rename('SD_BIG_IMPROVEMENT_YEAR', 'big_improvement_yr_sd')
segments.rename('Avg_ALL24', 'traffic_24_avg')
segments.rename('Avg_ALL8_9', 'traffic_8_9_avg')
segments.rename('Avg_ALL10_16', 'traffic_10_16_avg')
segments.rename('Avg_ALL17_18', 'traffic_17_18_avg')
segments.rename('Shape_Length', 'length_metres')
segments.rename('Landuse', 'land_uses')

print(segments.primary_key)
segments.convert_properties({
    'id': int,
    'length_metres': float
})

# Compute segment neighbors
for segment in segments:
    segment['neighbors'] = [
        int(segment[key]) for key in ["pseudoJunctionID1", "pseudoJunctionID2", "adjustJunctionID1", "adjustJunctionID2"]
        if segment[key] and int(segment[key])
    ]

segments.filter(lambda row: len(row['neighbors']) >= 2)
print(f"Removed segments without two junctions. Remaining {len(segments)} ({len(segments)/starting_segments_count:.0%})")

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

# Filter out null locations
crime.filter(lambda row: row['X'] and row['Y'] and (float(row['X']) != 0 or float(row['Y']) != 0))
print(f"Removed crimes with null locations. Remaining: {len(crime)} ({len(crime) / starting_crime_count:.0%})")

crime.rename('TYPE', 'type')
crime.rename('HUNDRED_BLOCK', 'hundred_block')
crime.rename('NEIGHBOURHOOD', 'neighborhood')

# Calculate latitude and longitude
for row in crime:
    lat, lon = utm.to_latlon(float(row["X"]), float(row["Y"]), ZONE_NUMBER, ZONE_LETTER)
    row['latitude'] = lat
    row['longitude'] = lon
    del row['X']
    del row['Y']
    
# Match to junctions
crime.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='crime_count', distance_limit=200)
crime.filter(lambda row: row['junction_id'] != 0)
print(f"Filtered No Connections. Remaining {len(crime)} ({len(crime) / starting_crime_count:.0%})")


## Cleanup Store ##
print()
print(f"Initial Store Count {starting_stores_count}")

IDs = set()
for row in sorted(stores, key=lambda row: row['Year recorded'], reverse=True):
    if int(row['ID']) in IDs:
        stores.remove(row['id'])
    else:
        IDs.add(int(row['ID']))
        
print(f"Removed duplicate stores. Remaining {len(stores)} ({len(stores) / starting_stores_count:.0%})")

stores.rename('ID', 'id')
stores.set_primary_key('id')
stores.rename('Civic number - Parcel', 'civic_number')
stores.rename('Street name - Parcel', 'street_name')
stores.rename('Business name', 'name')
stores.rename('Retail category', 'category')

stores.add_property('latitude', lambda row: split_latitude(row['geo_point_2d']))
stores.add_property('longitude', lambda row: split_longitude(row['geo_point_2d']))

stores.drop('Year recorded')
stores.drop('Geo Local Area')
stores.drop('Geom')
stores.drop('geo_point_2d')

stores.filter(lambda store: store['category'] != 'Vacant')

print(f"Removed vacant stores. Remaining {len(stores)} ({len(stores) / starting_stores_count:.0%})")

stores.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='stores_count', distance_limit=200)
stores.filter(lambda row: row['junction_id'] != 0)
print(f"Removed stores with no connections. Remaining {len(stores)} ({len(stores) / starting_stores_count:.0%})")


## Cleanup Transit ##
print()
print(f"Initial transit count: {starting_transit_count}")

transit.rename('stop_lat', 'latitude')
transit.rename('stop_lon', 'longitude')
transit.convert_properties({
    'stop_id': int,
    'latitude': float,
    'longitude': float
})

transit.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='stores_count', distance_limit=200)
transit.filter(lambda row: row['junction_id'] != 0)
print(f"Removed transit with no connections. Remaining {len(transit)} ({len(transit) / starting_transit_count:.0%})")


## Cleanup Rapid Transit ##
print()
print(f"Initial rapid transit count: {starting_rapid_transit_count}")

rapid_transit.rename('STATION', 'name')
rapid_transit.rename('Geo Local Area', 'area')

rapid_transit.add_property('latitude', lambda row: split_latitude(row['geo_point_2d']))
rapid_transit.add_property('longitude', lambda row: split_longitude(row['geo_point_2d']))
rapid_transit.drop('geo_point_2d')

rapid_transit.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='stores_count', distance_limit=200)
rapid_transit.filter(lambda row: row['junction_id'] != 0)
print(f"Removed rapid transit with no connections. Remaining {len(rapid_transit)} ({len(rapid_transit) / starting_rapid_transit_count:.0%})")

## Cleanup Schools ##
print()
print(f"Initial school count: {starting_schools_count}")

schools.rename('ADDRESS', 'address')
schools.rename('SCHOOL_CATEGORY', 'category')
schools.rename('SCHOOL_NAME', 'name')

schools.add_property('latitude', lambda row: split_latitude(row['geo_point_2d']))
schools.add_property('longitude', lambda row: split_longitude(row['geo_point_2d']))
schools.drop('geo_point_2d')

schools.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='stores_count', distance_limit=200)
schools.filter(lambda row: row['junction_id'] != 0)
print(f"Removed schools with no connections. Remaining {len(schools)} ({len(schools) / starting_schools_count:.0%})")


## Write Data ##