import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from data_wrangler import Dataset

JUNCTION_FILE = '../processed_data/junctions.csv'
SEGMENT_FILE = '../processed_data/segments.csv'
CRIME_FILE = '../processed_data/crime.csv'
TRANSIT_FILE = '../processed_data/transit.csv'
RAPID_TRANSIT_FILE = '../processed_data/rapid_transit.csv'
COMMERCIAL_FILE = '../processed_data/stores.csv'
SCHOOL_FILE = '../processed_data/schools.csv'

junctions = Dataset.load_file(JUNCTION_FILE)
junctions.convert('id', int)
junctions.convert('longitude', float)
junctions.convert('latitude', float)

transit = Dataset.load_file(TRANSIT_FILE, primary_key='stop_id')
transit.convert('stop_id', int)
transit.convert('latitude', float)
transit.convert('longitude', float)

crime = Dataset.load_file(CRIME_FILE)
crime.convert('id', int)
crime.convert('latitude', float)
crime.convert('longitude', float)

stores = Dataset.load_file(COMMERCIAL_FILE)
stores.convert('id', int)
stores.convert('latitude', float)
stores.convert('longitude', float)

rtransit = Dataset.load_file(RAPID_TRANSIT_FILE)
rtransit.convert('id', int)
rtransit.convert('latitude', float)
rtransit.convert('longitude', float)

schools = Dataset.load_file(SCHOOL_FILE)
schools.convert('id', int)
schools.convert('latitude', float)
schools.convert('longitude', float)

transit.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='transit_count')
crime.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='crime_count')
stores.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='stores_count')
rtransit.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='rtransit_count')
schools.match_lat_lng_approx(junctions, 'junction_id', 'junction_dst', count_field='schools_count')

junctions.write_to_file(JUNCTION_FILE)
transit.write_to_file(TRANSIT_FILE)
crime.write_to_file(CRIME_FILE)
stores.write_to_file(COMMERCIAL_FILE)
rtransit.write_to_file(RAPID_TRANSIT_FILE)
schools.write_to_file(SCHOOL_FILE)