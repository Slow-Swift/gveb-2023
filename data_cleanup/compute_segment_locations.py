### Computes the midpoint of a segment based on its two junctions

import csv

# Load the junctions
junctions = {}
with open('../data/original_data/junctions.csv', 'r') as jcsvinput:
    jdr = csv.DictReader(jcsvinput,quoting=csv.QUOTE_MINIMAL)
    for jdict_row in jdr:
        junctionll=[float(jdict_row["latitude"]),float(jdict_row["longitude"])]
        junctions[int(jdict_row["JunctionID"])] = junctionll
        
# Load the segments
segments = []
fieldnames = []
with open('../data/original_data/streetsegments.csv', 'r') as streetInput:
    streetReader = csv.DictReader(streetInput,quoting=csv.QUOTE_MINIMAL)
    fieldnames = streetReader.fieldnames
    for street in streetReader:
        near_junctions = [
            int(street[key]) 
            for key in ["pseudoJunctionID1", "pseudoJunctionID2", "adjustJunctionID1", "adjustJunctionID2"]
        ]
        junctionCount = sum(id > 0 for id in near_junctions)
        if junctionCount == 0:
            print(f"Streed with id {street['StreetID']} is not connected to any junctions.")
            continue
        
        latitude = sum(junctions[id][0] for id in near_junctions if id > 0) / junctionCount
        longitude = sum(junctions[id][1] for id in near_junctions if id > 0) / junctionCount
        street["latitude"] = latitude
        street["longitude"] = longitude
        segments.append(street)
        
with open('../data/original_data/streetsegments_new.csv', 'w', newline='') as streetOutput:
    writer = csv.DictWriter(f=streetOutput, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL) # type: ignore
    writer.writeheader()
    writer.writerows(segments)