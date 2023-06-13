import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from data_wrangler import Dataset
from data_wrangler.conversion_functions import RowFunction

JUNCTION_FILE = '../data/junctions.csv'
SEGMENT_FILE = '../data/streetsegments.csv'

junctionData = Dataset.load_file(
    JUNCTION_FILE, 
    {
        'id': (int, "JunctionID"),
        'type': (str, "JunctionType"),
        'street_count': (int, "StreetIntersectCount"),
        'vulnerability_score': (float, "Vulnerability"),
        'longitude': float,
        'latitude': float,
        'neighbors': []
    }
)

segmentData = Dataset.load_file(
    SEGMENT_FILE, 
    {
        'id': (int, "StreetID"),
        'length_metres': (float, "Shape_Length"),
        'neighbors': RowFunction(lambda row, i: {
            int(row[key]) for key in ["pseudoJunctionID1", "pseudoJunctionID2", "adjustJunctionID1", "adjustJunctionID2"]
            if row[key] and int(row[key])
        })
    }
)

junctions = { j.id: j for j in junctionData }

for segment in segmentData:
    neighbors = segment['neighbors']
    for junction in neighbors:
        junctions[junction]['neighbors'].extend