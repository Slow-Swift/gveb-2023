import utm

from neo4j import GraphDatabase

from loader import GraphLoader
from loader import convert_if_not_null
from loader import RowFunction

# Change this to point to the directory of your database information
DATABASE_INFO_FILEPATH = r"E:\Environmental Backcloth\dbinfo.txt"

JUNCTION_FILE = '../data/junctions.csv'
SEGMENT_FILE = '../data/streetsegments_new.csv'
CRIME_FILE = '../data/vanc_crime_2022.csv'
TRANSIT_FILE = '../data/transitstops.csv'
COMMERCIAL_FILE = '../data/storefronts-inventory_new.csv'

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

def load_junctions(loader: GraphLoader):
    print("Loading Junctions")
    
    junctionData = loader.load_file(
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
    
    junctions = loader.define_category(
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

def load_segments(loader: GraphLoader):
    print("Loading Segments")
    segmentData = loader.load_file(
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
    
    segments = loader.define_category(
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

def load_transit(loader: GraphLoader, segment_data):
    print("Loading Transit")
    
    transit_data = loader.load_file(
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
    
    loader.match_closest(
        transit_data, segment_data, 
        ['longitude', 'latitude'],
        {
            'closest': ('street_id', 'id'),
            'distance': 'street_dst'
        }
    )
    
    transit = loader.define_category(
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

def load_crimes(loader: GraphLoader, junction_data):
    print("Loading Crimes")
    
    crime_data = loader.load_file(
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
    
    loader.match_closest(
        crime_data, junction_data, 
        ['latitude', 'longitude'],
        {
            'closest': ('junction_id', 'id'),
            'distance': 'junction_dst'
        }
    ),
    
    crimes = loader.define_category(
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

def load_stores(loader: GraphLoader, junction_data):
    print("Loading Stores")
    stores_data = loader.load_file(
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
    
    loader.match_closest(
        stores_data, junction_data,
        ['latitude', 'longitude'],
        {
            'closest': ('junction_id', 'id'),
            'distance': 'junction_dst'
        }
    )
    
    stores = loader.define_category(
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

def load_data(session):
    loader = GraphLoader(session)
    
    print("Loading Data")
    junction_data, junctions = load_junctions(loader)
    # segment_data, segments = load_segments(loader)
    # transit_data, transit = load_transit(loader, segment_data)
    # crime_data, crimes = load_crimes(loader, junction_data)
    stores_data, stores = load_stores(loader, junction_data)
    
    # continues_to = loader.define_relation(
    #     "CONTINUES_TO",
    #     segments,
    #     junctions,
    #     ("id", "neighbors", "id") 
    # )
    
    # present_in = loader.define_relation(
    #     'PRESENT_IN',
    #     transit,
    #     segments,
    #     ('stop_id', 'street_id', 'id'),
    #     props = ['stop_id', 'street_id', ('distance', 'street_dst')]
    # )
    
    # nearest_crime_jn = loader.define_relation(
    #     'NEAREST_CRIME_JN',
    #     crimes,
    #     junctions,
    #     ('crime_id', 'junction_id', 'id'),
    #     props = ['crime_id', 'junction_id', ('distance', 'junction_dst')]
    # )
    
    nearest_store_jn = loader.define_relation(
        'NEAREST_JN',
        stores,
        junctions,
        ('id', 'junction_id', 'id'),
        props = [('store_id', 'id'), 'junction_id', ('distance', 'junction_dst')]
    )
    
    # loader.clear_all()
    
    # print("Writing Data")
    # loader.write_category(junctions)
    # print("Wrote Junctions")
    
    # loader.write_category(segments)
    # print("Wrote Segments")
    
    # loader.write_category(transit)    
    # print("Wrote Transit")
    
    # loader.write_category(crimes)
    # print("Wrote Crimes")
    
    loader.write_category(stores)
    print("Wrote Stores")
    
    # loader.write_relation(continues_to)
    # loader.write_relation(present_in)
    # loader.write_relation(nearest_crime_jn)
    loader.write_relation(nearest_store_jn)
    
    # session.run(
    #     '''
    #     MATCH (s:Segment)
    #     CALL {
    #         WITH s
    #         MATCH (j1:Junction)<-[:CONTINUES_TO]-(s)-[:CONTINUES_TO]->(j2:Junction)
    #         WITH j1, j2, s LIMIT 1
    #         CREATE (j1)-[c:CONNECTS_TO]->(j2)
    #         SET c = properties(s)
    #     } IN TRANSACTIONS
    #     '''
    # )
    
## Helper functions ##

def create_regular_str(old_str):
    if not old_str.isnumeric(): return old_str
    return old_str if int(old_str)>9 else "0"+old_str
    
# Start the program
if __name__ == "__main__":
    main()