import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

import math

from heapq import heappush, heappop

from ast import literal_eval
from data_wrangler import Dataset

INPUT_FOLDER = '../cleaned_data'
OUTPUT_FOLDER = '../processed_data'

JUNCTION_FILE = f'{INPUT_FOLDER}/junctions.csv'

CRIME_SIGMA = 132
STANDARD_DEVIATION = 400


junctions = Dataset.load_file(JUNCTION_FILE)
junctions.convert_properties({
    'id': int,
    'crime_count': int,
    'stores_count': int,
    'transit_count': int,
    'rapid_transit_count': int,
    'schools_count': int,
    'retail_count': int,
    'neighbors': lambda v : literal_eval(v) if v else []
})

def normal_dst(distance, standard_deviation):
    scale = 1 / (2 * math.pi * (standard_deviation ** 2))
    power = distance ** 2 / (2 * standard_deviation ** 2)
    distribution = math.exp(-power)
    return scale * distribution

def reach_dst(distance, scale):
    """ Calculate a modified version of Borgatti's reach formula
    
    TODO: Check that convergence is important and that if is whether we actually need to cube the denominator
    The range formula is:  sumweight * 1 / (dst_scale * dst + 1) ^ 2
    We have +1 because we want distance of zero to be constant with respect to dst_scale
    We cube the denominator because this causes it to converge
    """
    
    return 1 / ((distance / scale + 1) ** 3)

def calculate_reach(junction, properties, dst_func, limit=float('inf')):
    """
    Args:
        junction (Row): The junction to calculate the reach for
        prop (str): The property to use for junction weights
        dst_scale (float): The value to scale distance by. Should be in the range (0, 1]. Likely close to zero.

    Returns:
        float: The calculated reach.
    """
    reaches = { key: 0 for key in properties}
    visited = set()
    queue = []
    heappush(queue, (0, junction['id']))
    while queue:
        dst, next_jun = heappop(queue)
        if next_jun in visited: continue
        visited.add(next_jun)
        if dst > limit: continue
        
        # The range formula is: weight * 1 / (dst_scale * dst + 1) ^ 2
        # We have +1 because we want distance of zero to be constant with respect to dst_scale
        # We square the denominator because this causes it to converge
        
        # Update the range values
        crime_dst = normal_dst(dst, CRIME_SIGMA)
        scaled_dst = dst_func(dst)
        for key in properties:
            if key == 'crime_reach':
                reaches[key] += junctions[next_jun][properties[key]] * crime_dst
            else:
                reaches[key] += junctions[next_jun][properties[key]] * scaled_dst
              
        for neighbor, delta, s_id in junctions[next_jun]['neighbors']:
            if neighbor in visited: continue
            neighbor_dst = dst + delta
            heappush(queue, (neighbor_dst, neighbor))
    return reaches

def calculate_reaches(junctions, properties, dst_func, limit=float('inf')):
    highest = { key: 0 for key in properties}
    
    for i, junction in enumerate(junctions):
        reaches = calculate_reach(junction, properties, dst_func, limit)
        for key in reaches:
            junction[key] = reaches[key]
            highest[key] = max(highest[key], reaches[key])
        
        if (i+1) % 100 == 0:
            print(f'\rCalculated {i+1}/{len(junctions)}           ', end='')
    print(f'\rCalculated {len(junctions)}/{len(junctions)}        ')
    print("Normalizing")
    for junction in junctions:
        for key in properties:
            junction[key] /= highest[key]
    print("Done")
    
calculate_reaches(
    junctions, 
    {
        'crime_reach': 'crime_count',
        'store_reach': 'stores_count',
        'transit_reach': 'transit_count',
        'rapid_transit_reach': 'rapid_transit_count',
        'schools_reach': 'schools_count',
        'retail_reach': 'retail_count',
    }, 
    lambda dst: normal_dst(dst, STANDARD_DEVIATION),
    limit=1000
)
junctions.write_to_file(f'{OUTPUT_FOLDER}/reach_junctions.csv')