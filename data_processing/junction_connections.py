import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from data_wrangler import Dataset

import ast

JUNCTION_FILE = '../processed_data/junctions.csv'
SEGMENT_FILE = '../processed_data/segments.csv'

junctionData = Dataset.load_file(JUNCTION_FILE)
junctionData.convert_property('id', int)

segmentData = Dataset.load_file(
    SEGMENT_FILE, 
    {
        'id': int,
        'length_metres': float,
        'neighbors': ast.literal_eval
    }
)

junctions = { j['id']: j for j in junctionData }

for segment in segmentData:
    neighbors = segment['neighbors']
    if len(neighbors) > 2:
        print(segment['id'])
    for jid in neighbors:
        junction = junctions[jid]
        junction['neighbors'] = junction.get('neighbors', [])
        junction['neighbors'].extend([
            (neighbor_id, segment['length_metres'], segment['id']) for neighbor_id in neighbors if neighbor_id != jid
        ])
        
junctionData.write_to_file(JUNCTION_FILE)