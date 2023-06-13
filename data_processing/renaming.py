import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

import utm

from data_wrangler import Dataset
from data_wrangler.conversion_functions import RowFunction
from data_wrangler.conversion_functions import generate_id
from data_wrangler.conversion_functions import create_regular_str
from data_wrangler.conversion_functions import split_latitude, split_longitude

ZONE_NUMBER = 10
ZONE_LETTER = 'U'

JUNCTION_FILE = '../original_data/junctions.csv'
SEGMENT_FILE = '../original_data/streetsegments.csv'
CRIME_FILE = '../original_data/vanc_crime_2022.csv'
TRANSIT_FILE = '../original_data/transitstops.csv'
RAPID_TRANSIT_FILE = '../original_data/rapid-transit-stations.csv'
COMMERCIAL_FILE = '../original_data/storefronts-inventory.csv'
SCHOOL_FILE = '../original_data/schools.csv'

Dataset.load_file(
    JUNCTION_FILE, 
    {
        'id': (int, "JunctionID"),
        'type': (str, "JunctionType"),
        'street_count': (int, "StreetIntersectCount"),
        'vulnerability_score': (float, "Vulnerability"),
        'longitude': float,
        'latitude': float
    }
).write_to_file('../processed_data/junctions.csv')

Dataset.load_file(
    SEGMENT_FILE, 
    {
        'id': (int, "StreetID"),
        'hblock': str,
        'type': (str, "streetType"),
        'property_count': (str, "PropertyCount"),
        'PseudoJunctionCount': int,
        'pseudoJunctionID1': int,
        'pseudoJunctionID2': int,
        'adjustJunctionID1': int,
        'adjustJunctionID2': int,
        'adjustStreetID1': str,
        'adjustStreetID2': str,
        'current_land_val_avg': (str, "Avg_CURRENT_LAND_VALUE"),
        'current_land_val_sd': (str, "SD_CURRENT_LAND_VALUE"),
        'current_improvement_avg': (str, "Avg_CURRENT_IMPROVEMENT_VALUE"),
        'current_improvement_sd': (str, "SD_CURRENT_IMPROVEMENT_VALUE"),
        'Avg_ASSESSMENT_YEAR': str,
        'prev_land_val_avg': (str, "Avg_PREVIOUS_LAND_VALUE"),
        'prev_land_val_sd': (str, "SD_PREVIOUS_LAND_VALUE"),
        'prev_improv_val_avg': (str, "Avg_PREVIOUS_IMPROVEMENT_VALUE"),
        'prev_improv_val_sd': (str, "SD_PREVIOUS_IMPROVEMENT_VALUE"),
        'year_built_avg': (str, "Avg_YEAR_BUILT"),
        'year_built_sd': (str, "SD_YEAR_BUILT"),
        'big_improvement_yr_avg': (str, "Avg_BIG_IMPROVEMENT_YEAR"),
        'big_improvement_yr_sd': (str, "SD_BIG_IMPROVEMENT_YEAR"),
        'traffic_24_avg': (str, "Avg_ALL24"),
        'traffic_8_9_avg': (str, "Avg_ALL8_9"),
        'traffic_10_16_avg': (str, "Avg_ALL10_16"),
        'traffic_17_18_avg': (str, "Avg_ALL17_18"),
        'length_metres': (float, "Shape_Length"),
        'latitude': float,
        'longitude': float,
        
        # Converting land uses to a list
        'land_uses': (lambda v: list(str.split(v, ', ')), "Landuse"),
        
        # Generating a list of the neighboring junctions
        'neighbors': RowFunction(lambda row, i: [
            int(row[key]) for key in ["pseudoJunctionID1", "pseudoJunctionID2", "adjustJunctionID1", "adjustJunctionID2"]
            if row[key] and int(row[key])
        ])
    }
).write_to_file('../processed_data/segments.csv')

Dataset.load_file(
    TRANSIT_FILE, 
    {
        'stop_id': int,
        'stop_code': int,
        'stop_name': str,
        'zone_id': str,
        'latitude': (float, 'stop_lat'),
        'longitude': (float, 'stop_lon'),
    },
    primary_key='stop_id'
).write_to_file('../processed_data/transit.csv')

Dataset.load_file(
    CRIME_FILE,
    {
        # Generating id because crime doesn't have id already
        'id': generate_id,
        'type_of_crime': (str, 'TYPE'),
        
        # Creating a date field in format yyyy-mm-dd
        'date_of_crime': RowFunction(lambda row, i: f"{row['YEAR']}-{create_regular_str(row['MONTH'])}-{create_regular_str(row['DAY'])}"),
        
        # Creating a time field in the format HH:MM
        'time_of_crime': RowFunction(lambda row, i: f"{create_regular_str(row['HOUR'])}:{create_regular_str(row['MINUTE'])}"),
        'hundred_block': (str, 'HUNDRED_BLOCK'),
        'recency': (str, 'RECENCY'),
        
        # Determining latitude and longitude from utm location
        'latitude': RowFunction(lambda row, i: utm.to_latlon(float(row["X"]), float(row["Y"]), ZONE_NUMBER, ZONE_LETTER)[0]),
        'longitude': RowFunction(lambda row, i: utm.to_latlon(float(row["X"]), float(row["Y"]), ZONE_NUMBER, ZONE_LETTER)[1]),
    },
).write_to_file('../processed_data/crime.csv')

Dataset.load_file(
    COMMERCIAL_FILE,
    {
        'id': (int, 'ID'),
        'unit': (str, 'Unit'),
        'civic_number': (int, 'Civic number - Parcel'),
        'street_name': (str, 'Street name - Parcel'),
        'name': (str, 'Business name'),
        'category': (str, 'Retail category'),
        
        # Getting lat and lon fom "lat, lon" format
        'latitude': (split_latitude, 'geo_point_2d'),
        'longitude': (split_longitude, 'geo_point_2d'),
    }
).write_to_file('../processed_data/stores.csv')

rtransit_data = Dataset.load_file(
    RAPID_TRANSIT_FILE,
    {
        'id': generate_id,
        'name': (str, 'STATION'),
        'area': (str, 'Geo Local Area'),
        
        # Getting lat and lon fom "lat, lon" format
        'latitude': (split_latitude, 'geo_point_2d'),
        'longitude': (split_longitude, 'geo_point_2d'),
    },
    delimiter=';'
).write_to_file('../processed_data/rapid_transit.csv')

Dataset.load_file(
    SCHOOL_FILE,
    {
        'id': generate_id,
        'address': (str, 'ADDRESS'),
        'category': (str, 'SCHOOL_CATEGORY'),
        'name': (str, 'SCHOOL_NAME'),
        
        # Getting lat and lon fom "lat, lon" format
        'latitude': (split_latitude, 'geo_point_2d'),
        'longitude': (split_longitude, 'geo_point_2d'),
    },
    delimiter=';'
).write_to_file('../processed_data/schools.csv')