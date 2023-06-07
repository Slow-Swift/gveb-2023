import utm

from neo4j import GraphDatabase

from loader import GraphLoader
from loader import convert_if_not_null

from category import Category
from relationship import Relationship
from dataset import Dataset
from dataset import RowFunction

# Change this to point to the directory of your database information
DATABASE_INFO_FILEPATH = r"../../dbinfo.txt"

JUNCTION_FILE = '../data/junctions.csv'
SEGMENT_FILE = '../data/streetsegments_new.csv'
CRIME_FILE = '../data/vanc_crime_2022.csv'
TRANSIT_FILE = '../data/transitstops.csv'
RAPID_TRANSIT_FILE = '../data/rapid-transit-stations.csv'
COMMERCIAL_FILE = '../data/storefronts-inventory_new.csv'
SCHOOL_FILE = '../data/schools.csv'

ZONE_NUMBER = 10
ZONE_LETTER = 'U'

## Main Program ##

def main():
    driver = create_driver()
    if not driver: return
    
    with driver.session() as session:
        if not session: return
        
        load_data(session)
    driver.close()

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
    with open(filepath) as dbinfo:
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
            'id': (int, "JunctionID"),
            'type': (str, "JunctionType"),
            'street_count': (int, "StreetIntersectCount"),
            'vulnerability_score': (float, "Vulnerability"),
            'longitude': float,
            'latitude': float
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
            'vulnerability_score',
        ]
    )
    
    print("Loaded Junctions")
    return junctionData, junctions

def load_segments():
    print("Loading Segments")
    segmentData = Dataset.load_file(
        SEGMENT_FILE, 
        {
            'id': (int, "StreetID"),
            'hblock': str,
            'type': (str, "streetType"),
            'property_count': (convert_if_not_null, "PropertyCount"),
            'PseudoJunctionCount': int,
            'pseudoJunctionID1': int,
            'pseudoJunctionID2': int,
            'adjustJunctionID1': int,
            'adjustJunctionID2': int,
            'adjustStreetID1': lambda v: convert_if_not_null(v, on_null=None),
            'adjustStreetID2': lambda v: convert_if_not_null(v, on_null=None),
            'current_land_val_avg': (convert_if_not_null, "Avg_CURRENT_LAND_VALUE"),
            'current_land_val_sd': (convert_if_not_null, "SD_CURRENT_LAND_VALUE"),
            'current_improvement_avg': (convert_if_not_null, "Avg_CURRENT_IMPROVEMENT_VALUE"),
            'current_improvement_sd': (convert_if_not_null, "SD_CURRENT_IMPROVEMENT_VALUE"),
            'Avg_ASSESSMENT_YEAR': convert_if_not_null,
            'prev_land_val_avg': (convert_if_not_null, "Avg_PREVIOUS_LAND_VALUE"),
            'prev_land_val_sd': (convert_if_not_null, "SD_PREVIOUS_LAND_VALUE"),
            'prev_improv_val_avg': (convert_if_not_null, "Avg_PREVIOUS_IMPROVEMENT_VALUE"),
            'prev_improv_val_sd': (convert_if_not_null, "SD_PREVIOUS_IMPROVEMENT_VALUE"),
            'year_built_avg': (convert_if_not_null, "Avg_YEAR_BUILT"),
            'year_built_sd': (convert_if_not_null, "SD_YEAR_BUILT"),
            'big_improvement_yr_avg': (convert_if_not_null, "Avg_BIG_IMPROVEMENT_YEAR"),
            'big_improvement_yr_sd': (convert_if_not_null, "SD_BIG_IMPROVEMENT_YEAR"),
            'traffic_24_avg': (lambda v: convert_if_not_null(v, on_null=None), "Avg_ALL24"),
            'traffic_8_9_avg': (lambda v: convert_if_not_null(v, on_null=None), "Avg_ALL8_9"),
            'traffic_10_16_avg': (lambda v: convert_if_not_null(v, on_null=None), "Avg_ALL10_16"),
            'traffic_17_18_avg': (lambda v: convert_if_not_null(v, on_null=None), "Avg_ALL17_18"),
            'length_metres': (float, "Shape_Length"),
            'latitude': float,
            'longitude': float,
            'land_uses': (lambda v: list(str.split(v, ', ')), "Landuse"),
            'neighbors': RowFunction(lambda row, i: [
                int(row[key]) for key in ["pseudoJunctionID1", "pseudoJunctionID2", "adjustJunctionID1", "adjustJunctionID2"]
                if row[key] and int(row[key])
            ])
        }
    )
    
    segments = Category(
        "Segment",
        segmentData,
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
    
    print("Loaded Segments")
    
    return segmentData, segments

def load_transit(segment_data):
    print("Loading Transit")
    
    transit_data = Dataset.load_file(
        TRANSIT_FILE, 
        {
            'stop_id': int,
            'stop_code': int,
            'stop_name': str,
            'zone_id': str,
            'longitude': (float, 'stop_lat'),
            'latitude': (float, 'stop_lat')
        }
    )
    
    transit_data.match_lat_lng(segment_data, 'street_id', 'street_dst')
    
    transit = Category(
        "Transit",
        transit_data,
        [
            "stop_id",
            "stop_code",
            "stop_name",
            "zone_id",
            "longitude",
            "latitude"
        ]
    )
    
    print("Loaded Transit")
    return transit_data, transit

def load_crimes(junction_data):
    print("Loading Crimes")
    
    crime_data = Dataset.load_file(
        CRIME_FILE,
        {
            'crime_id': RowFunction(lambda row, i: i + 1),
            'type_of_crime': (str, 'TYPE'),
            'date_of_crime': RowFunction(lambda row, i: f"{row['YEAR']}-{create_regular_str(row['MONTH'])}-{create_regular_str(row['DAY'])}"),
            'time_of_crime': RowFunction(lambda row, i: f"{create_regular_str(row['HOUR'])}:{create_regular_str(row['MINUTE'])}"),
            'hundred_block': (str, 'HUNDRED_BLOCK'),
            'recency': (str, 'RECENCY'),
            'latitude': RowFunction(lambda row, i: utm.to_latlon(float(row["X"]), float(row["Y"]), ZONE_NUMBER, ZONE_LETTER)[0]),
            'longitude': RowFunction(lambda row, i: utm.to_latlon(float(row["X"]), float(row["Y"]), ZONE_NUMBER, ZONE_LETTER)[1]),
        }
    )
    
    match_junctions(crime_data, junction_data)
    
    crimes = Category(
        'Crime',
        crime_data,
        [
            'crime_id',
            'type_of_crime',
            'date_of_crime',
            'time_of_crime',
            'hundred_block',
            'recency',
            'latitude',
            'longitude'
        ]
    )
    
    print("Loaded Crimes")
    return crime_data, crimes

def load_stores(junction_data):
    print("Loading Stores")
    stores_data = Dataset.load_file(
        COMMERCIAL_FILE,
        {
            'id': (int, 'ID'),
            'unit': (str, 'Unit'),
            'civic_number': (int, 'Civic number - Parcel'),
            'street_name': (str, 'Street name - Parcel'),
            'name': (str, 'Business name'),
            'category': (str, 'Retail category'),
            'latitude': (lambda v: float(v.split(', ')[0]), 'geo_point_2d'),
            'longitude': (lambda v: float(v.split(', ')[1]), 'geo_point_2d'),
        }
    )
    
    match_junctions(stores_data, junction_data)
    
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

def load_rapid_transit(junction_data):
    rtransit_data = Dataset.load_file(
        RAPID_TRANSIT_FILE,
        {
            'id': RowFunction(lambda row, i: i + 1),
            'name': (str, 'STATION'),
            'area': (str, 'Geo Local Area'),
            'latitude': (lambda v: float(v.split(', ')[0]), 'geo_point_2d'),
            'longitude': (lambda v: float(v.split(', ')[1]), 'geo_point_2d'),
        },
        delimiter=';'
    )
    
    match_junctions(rtransit_data, junction_data)
    
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
    
    return rtransit_data, rtransit

def load_schools(junction_data):
    schools_data = Dataset.load_file(
        SCHOOL_FILE,
        {
            'id': RowFunction(lambda row, i: i + 1),
            'address': (str, 'ADDRESS'),
            'category': (str, 'SCHOOL_CATEGORY'),
            'name': (str, 'SCHOOL_NAME'),
            'latitude': (lambda v: float(v.split(', ')[0]), 'geo_point_2d'),
            'longitude': (lambda v: float(v.split(', ')[1]), 'geo_point_2d'),
        },
        delimiter=';'
    )
    
    match_junctions(schools_data, junction_data)
    
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
    
    return schools_data, schools

def load_data(session):
    loader = GraphLoader(session)
    
    print("Loading Data")
    junction_data, junctions = load_junctions()
    segment_data, segments = load_segments()
    transit_data, transit = load_transit(segment_data)
    crime_data, crimes = load_crimes(junction_data)
    stores_data, stores = load_stores(junction_data)
    rtransit_data, rtransit = load_rapid_transit(junction_data)
    schools_data, schools = load_schools(junction_data)
    
    categories = [
        # junctions,
        # segments,
        # transit,
        # crimes,
        # stores,
        # rtransit,
        schools
    ]
    
    continues_to = Relationship('CONTINUES_TO', segments, junctions, 'neighbors')
    
    present_in = Relationship(
        'PRESENT_IN', transit, segments, 'street_id',
        props = ['stop_id', 'street_id', ('distance', 'street_dst')]
    )
    
    nearest_crime_jn = Relationship(
        'NEAREST_CRIME_JN', crimes, junctions, 'junction_id',
        props = ['crime_id', 'junction_id', ('distance', 'junction_dst')]
    )
    
    nearest_store_jn = Relationship(
        'NEAREST_JN', stores, junctions, 'junction_id',
        props = [('store_id', 'id'), 'junction_id', ('distance', 'junction_dst')]
    )
    
    nearest_station_jn = Relationship(
        'NEAREST_STATION_JN', rtransit, junctions, 'junction_id',
        props = [('station_id', 'id'), 'junction_id', ('distance', 'junction_dst')]
    )
    
    nearest_school_jn = Relationship(
        'NEAREST_SCHOOL_JN', schools, junctions, 'junction_id',
        props = [('school_id', 'id'), 'junction_id', ('distance', 'junction_dst')]
    )
    
    relationships = [
        #  continues_to,
        #  present_in,
        #  nearest_crime_jn,
        #  nearest_store_jn,
        #  nearest_station_jn,
         nearest_school_jn
    ]
    
    print("Writing Data")
    # loader.clear_all()
    
    for category in categories:
        loader.write_category(category)
        print(f"Wrote {category.name}")
    
    for relation in relationships:
        loader.write_relation(relation)
    
    # join_junctions(session)
    
    print("Done")
    
## Helper functions ##

def join_junctions(session):
    session.run(
        '''
        MATCH (s:Segment)
        CALL {
            WITH s
            MATCH (j1:Junction)<-[:CONTINUES_TO]-(s)-[:CONTINUES_TO]->(j2:Junction)
            WITH j1, j2, s LIMIT 1
            CREATE (j1)-[c:CONNECTS_TO]->(j2)
            SET c = properties(s)
        } IN TRANSACTIONS
        '''
    )

def create_regular_str(old_str):
    if not old_str.isnumeric(): return old_str
    return old_str if int(old_str)>9 else "0"+old_str
    
def match_junctions(data, junctions):
    data.match_lat_lng(junctions, 'junction_id', 'junction_dst')
    
# Start the program
if __name__ == "__main__":
    main()