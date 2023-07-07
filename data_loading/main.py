import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

import utm
from neo4j import GraphDatabase
from time import perf_counter

from data_wrangler import Dataset
from data_wrangler import Category
from data_wrangler import Relationship
from data_wrangler import GraphWriter

from ast import literal_eval

from data_wrangler.conversion_functions import convert_if_not_null
from data_wrangler.relationship_property_matchers import first_set_prop_match
from data_wrangler.relationship_property_matchers import match_props

# Change this to point to the directory of your database information
DATABASE_INFO_FILEPATH = r"../../dbinfo.txt"

INPUT_FOLDER = '../cleaned_data'

JUNCTION_FILE = f'../processed_data/reach_junctions.csv'
SEGMENT_FILE = f'{INPUT_FOLDER}/segments.csv'
CRIME_FILE = f'{INPUT_FOLDER}/crimes.csv'
TRANSIT_FILE = f'{INPUT_FOLDER}/transit.csv'
RAPID_TRANSIT_FILE = f'{INPUT_FOLDER}/rapid_transit.csv'
COMMERCIAL_FILE = f'{INPUT_FOLDER}/stores.csv'
SCHOOL_FILE = f'{INPUT_FOLDER}/schools.csv'
BUSINESSES_FILE = f'{INPUT_FOLDER}/businesses.csv'

ZONE_NUMBER = 10
ZONE_LETTER = 'U'

## Main Program ##

def main():
    driver = create_driver()
    if not driver: return
    
    with driver.session() as session:
        if not session: return
        
        start_time = perf_counter()
        load_data(session)
        end_time = perf_counter()
        
    driver.close()
    elapsed_time = end_time - start_time
    print(f"Completed in {(elapsed_time / 60):.0f}:{(elapsed_time % 60):.0f} minutes")

## Database Setup ##

def load_db_info(filepath):
    """ Load database access information from a file
    
    The file should be one downloaded from Neo4j when creating a database
    
    Parameters:
        filepath - String: The path to the file

    Returns:
        (uri, username, password): The access information if the file is valid
        None: When the information cannot be loaded
    """
    
    uri, user, password = None, None, None
    with open(filepath, 'r') as dbinfo:
        for line in dbinfo:
            line = line.strip()
            
            # Skip lines that don't have information or where it would be invalid
            if not "=" in line: continue
            label, value = line.split("=")
            if len(label) == 0 or len(value) == 0: continue
            
            # Set the variable that corresponds with the label
            match label:
                case "NEO4J_URI":
                    uri = value
                case "NEO4J_USERNAME":
                    user = value
                case "NEO4J_PASSWORD":
                    password = value
                    
    if not (uri and user and password): return None
    return (uri, user, password)

def create_driver():
    # Get the database information
    db_info = load_db_info(DATABASE_INFO_FILEPATH)
    if not db_info: return None
    uri, user, password = db_info

    # Connect to the database
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

## Data Loading ##

def load_junctions():
    print("Loading Junctions")
    
    junctionData = Dataset.load_file(
        JUNCTION_FILE, 
        {
            'id': int,
            'type': str,
            'longitude': float,
            'latitude': float,
            'street_count': int,
            'crime_count': int,
            'transit_count': int,
            'stores_count': int,
            'schools_count': int,
            'rapid_transit_count': int,
            'retail_count': int,
            'rapid_transit_count': int,
            'neighbor_ids': (lambda v: [n[0] for n in literal_eval(v if v else '[]')], 'neighbors'),
            'street_ids': (lambda v: [n[2] for n in literal_eval(v if v else '[]')], 'neighbors'),
            'crime_reach': float,
            'store_reach': float,
            'transit_reach': float,
            'rapid_transit_reach': float,
            'schools_reach': float,
            'retail_reach': float,
        }
    )
    
    junctions = Category(
        "Junction",
        junctionData,
        [
            'id',
            'type',
            'street_count',
            'longitude',
            'latitude',
            'crime_count',
            'transit_count',
            'stores_count',
            'schools_count',
            'rapid_transit_count',
            'retail_count',
            'crime_reach',
            'store_reach',
            'transit_reach',
            'rapid_transit_reach',
            'schools_reach',
            'retail_reach',
        ]
    )
    
    print("Loaded Junctions")
    return junctionData, junctions

def load_segments():
    print("Loading Segments")
    segmentData = Dataset.load_file(
        SEGMENT_FILE, 
        {
            'id': int,
            'hblock': str,
            'type': str,
            'property_count': convert_if_not_null,
            'current_land_val_avg': convert_if_not_null,
            'current_land_val_sd': convert_if_not_null,
            'current_improvement_avg': convert_if_not_null,
            'current_improvement_sd': convert_if_not_null,
            'year_assessment_avg': convert_if_not_null,
            'year_assessment_sd': convert_if_not_null,
            'prev_land_val_avg': convert_if_not_null,
            'prev_land_val_sd': convert_if_not_null,
            'prev_improv_val_avg': convert_if_not_null,
            'prev_improv_val_sd': convert_if_not_null,
            'year_built_avg': convert_if_not_null,
            'year_built_sd': convert_if_not_null,
            'big_improvement_yr_avg': convert_if_not_null,
            'big_improvement_yr_sd': convert_if_not_null,
            'traffic_24_avg': lambda v: convert_if_not_null(v, on_null=None),
            'traffic_8_9_avg': lambda v: convert_if_not_null(v, on_null=None),
            'traffic_10_16_avg': lambda v: convert_if_not_null(v, on_null=None),
            'traffic_17_18_avg': lambda v: convert_if_not_null(v, on_null=None),
            'length_metres': float,
            'latitude': float,
            'longitude': float,
            'land_uses': literal_eval,
            'neighbors': literal_eval
        }
    )
    
    print("Loaded Segments")
    
    return segmentData

def load_transit():
    print("Loading Transit")
    
    transit_data = Dataset.load_file(
        TRANSIT_FILE, 
        {
            'id': int,
            'stop_code': int,
            'stop_name': str,
            'zone_id': str,
            'latitude': float,
            'longitude': float,
            'junction_id': int,
            'junction_dst': float
        },
    )
    
    transit = Category(
        "Transit",
        transit_data,
        [
            "id",
            "stop_code",
            "stop_name",
            "zone_id",
            "longitude",
            "latitude"
        ]
    )
    
    print("Loaded Transit")
    return transit_data, transit

def load_crimes():
    print("Loading Crimes")
    
    crime_data = Dataset.load_file(
        CRIME_FILE,
        {
            'id': int,
            'type_of_crime': str,
            'date_of_crime': str,
            'time_of_crime': str,
            'hundred_block': str,
            'latitude': float,
            'longitude': float,
            'junction_id': int,
            'junction_dst': float
        },
    )
    
    crimes = Category(
        'Crime',
        crime_data,
        [
            'id',
            'type_of_crime',
            'date_of_crime',
            'time_of_crime',
            'hundred_block',
            'latitude',
            'longitude'
        ]
    )
    
    print("Loaded Crimes")
    return crime_data, crimes

def load_stores():
    print("Loading Stores")
    stores_data = Dataset.load_file(
        COMMERCIAL_FILE,
        {
            'id': int,
            'unit': str,
            'civic_number': str,
            'street_name': str,
            'name': str,
            'category': str,
            'latitude': float,
            'longitude': float,
            'junction_id': int,
            'junction_dst': float
        }
    )
    
    stores = Category(
        "Store",
        stores_data,
        [
            'id',
            'name',
            'category',
            'unit',
            'civic_number',
            'street_name',
            'latitude',
            'longitude'
        ]
    )
    
    print("Loaded Stores")
    return stores_data, stores

def load_rapid_transit():
    print("Loading Rapid Transit")
    rtransit_data = Dataset.load_file(
        RAPID_TRANSIT_FILE,
        {
            'id': int,
            'name': str,
            'area': str,
            'latitude': float,
            'longitude': float,
            'junction_id': int,
            'junction_dst': float
        }
    )
    
    rtransit = Category(
        "RapidTransit",
        rtransit_data,
        [
            'id',
            'name',
            'area',
            'latitude',
            'longitude'
        ]
    )
    print("Loaded Rapid Transit")
    
    return rtransit_data, rtransit

def load_schools():
    print("Loading Schools")
    
    schools_data = Dataset.load_file(
        SCHOOL_FILE,
        {
            'id': int,
            'address': str,
            'category': str,
            'name': str,
            'latitude': float,
            'longitude': float,
            'junction_id': int,
            'junction_dst': float
        }
    )
    
    schools = Category(
        "School",
        schools_data,
        [
            'id',
            'address',
            'category',
            'name',
            'latitude',
            'longitude'
        ]
    )
    
    print("Loaded Schools")
    
    return schools_data, schools

def load_businesses():
    print("Loading Businesses")
    
    businesses_data = Dataset.load_file(
        BUSINESSES_FILE,
        {
            'id': int,
            'licence_rsn': int,
            'licence_number': str,
            'name': str,
            'trade_name': str,
            'business_type': str,
            'sub_type': str,
            'employees_count': str,
            'local_area': str,
            'retail': str,
            'latitude': float,
            'longitude': float,
            'junction_id': int,
            'junction_dst': float
        }
    )
    
    businesses = Category(
        "Business",
        businesses_data,
        [
            'id',
            'licence_rsn',
            'licence_number',
            'name',
            'trade_name',
            'business_type',
            'sub_type',
            'employees_count',
            'local_area',
            'retail',
            'latitude',
            'longitude'
        ]
    )
    
    print("Loaded Schools")
    
    return businesses_data, businesses

def create_relationships(junctions, segments, transit, crimes, stores, rtransit, schools, businesses):
    def junction_prop_matcher(j1, j2):
        segment_id = j1['street_ids'][j1['neighbor_ids'].index(j2['id'])]
        segment = segments[segment_id]
        return match_props(
            segment,
            [
                'id',
                'hblock',
                'type',
                'property_count',
                'current_land_val_avg',
                'current_land_val_sd',
                'current_improvement_avg',
                'current_improvement_sd',
                'prev_land_val_avg',
                'prev_land_val_sd',
                'prev_improv_val_avg',
                'prev_improv_val_sd',
                'year_built_avg',
                'year_built_sd',
                'big_improvement_yr_avg',
                'traffic_24_avg',
                'traffic_8_9_avg',
                'traffic_10_16_avg',
                'traffic_17_18_avg',
                'length_metres',
                'latitude',
                'longitude',
                'land_uses'
            ]
        )
        
    connects_to = Relationship(
        'CONNECTS_TO', junctions, junctions, 'neighbor_ids',
        prop_matcher=junction_prop_matcher,
        remove_duplicates=True
    )
    
    nearest_transit_jn = Relationship(
        'NEAREST_TRANSIT_JN', transit, junctions, 'junction_id',
        prop_matcher=first_set_prop_match([('stop_id', 'id'), 'junction_id', ('distance', 'junction_dst')])
    )
    
    nearest_crime_jn = Relationship(
        'NEAREST_CRIME_JN', crimes, junctions, 'junction_id',
        prop_matcher=first_set_prop_match([('crime_id', 'id'), 'junction_id', ('distance', 'junction_dst')])
    )
    
    nearest_store_jn = Relationship(
        'NEAREST_STORE_JN', stores, junctions, 'junction_id',
        prop_matcher=first_set_prop_match([('store_id', 'id'), 'junction_id', ('distance', 'junction_dst')])
    )
    
    nearest_station_jn = Relationship(
        'NEAREST_STATION_JN', rtransit, junctions, 'junction_id',
        prop_matcher=first_set_prop_match([('station_id', 'id'), 'junction_id', ('distance', 'junction_dst')])
    )
    
    nearest_school_jn = Relationship(
        'NEAREST_SCHOOL_JN', schools, junctions, 'junction_id',
        prop_matcher=first_set_prop_match([('school_id', 'id'), 'junction_id', ('distance', 'junction_dst')])
    )
    
    nearest_business_jn = Relationship(
        "NEAREST_BUSINESS_JN", businesses, junctions, 'junction_id',
        prop_matcher=first_set_prop_match([('business_id', 'id'), 'junction_id', ('distance', 'junction_dst')])
    )
    
    relationships = [
        connects_to,
        nearest_transit_jn,
        nearest_crime_jn,
        nearest_store_jn,
        nearest_station_jn,
        nearest_school_jn,
        nearest_business_jn
    ]
    
    return relationships

def load_data(session):
    
    # This makes it easer to only load some of the data without having to modify too much code
    junctions = transit = crimes = stores = rtransit = schools = businesses = None
    
    print("Loading Data")
    junction_data, junctions = load_junctions()
    segment_data = load_segments()
    transit_data, transit = load_transit()
    crime_data, crimes = load_crimes()
    stores_data, stores = load_stores()
    rtransit_data, rtransit = load_rapid_transit()
    schools_data, schools = load_schools()
    businesses_data, businesses = load_businesses()
    
    categories = [
        junctions,
        transit,
        crimes,
        stores,
        rtransit,
        schools,
        businesses
    ]
    
    relationships = create_relationships(
        junctions, segment_data, transit, crimes, stores, rtransit, schools, businesses
    )
    
    print("Writing Data")
    writer = GraphWriter(session)
    writer.clear_all()
    
    print()
    print("-- Writing Categories --")
    for category in categories:
        writer.clear_category(category)
        writer.write_category(category)
        print(f"Wrote {category.name}")
    
    print()
    print("-- Writing Relationships --")
    for relation in relationships:
        writer.write_relation(relation)
    
    print()
    print("Writing Data Completed")
    
# Start the program
if __name__ == "__main__":
    main()