import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from heapq import heappush, heappop

from ast import literal_eval
from data_wrangler import Dataset

JUNCTION_FILE = '../processed_data/junctions.csv'

junctions = Dataset.load_file(JUNCTION_FILE)
junctions.convert_properties({
    'id': int,
    'crime_count': int,
    'stores_count': int,
    'transit_count': int,
    'rtransit_count': int,
    'schools_count': int,
    'neighbors': lambda v : literal_eval(v) if v else []
})

def calculate_range(junction, properties, dst_scale, limit):
    """ Calculate a modified version of Borgatti's reach formula
    
    The range formula is:  sumweight * 1 / (dst_scale * dst + 1) ^ 2
    We have +1 because we want distance of zero to be constant with respect to dst_scale
    We square the denominator because this causes it to converge
    
    TODO: Check that convergence is important and that if is whether we actually need to cube the denominator

    Args:
        junction (Row): The junction to calculate the reach for
        prop (str): The property to use for junction weights
        dst_scale (float): The value to scale distance by. Should be in the range (0, 1]. Likely close to zero.
        limit (float): The distance past which to stop calculations. This improves speed at the expense of a bit of accurracy.

    Returns:
        float: The calculated reach.
    """
    ranges = { key: 0 for key in properties}
    visited = set()
    queue = []
    heappush(queue, (0, junction['id']))
    while queue:
        dst, next_jun = heappop(queue)
        if next_jun in visited: continue
        visited.add(next_jun)
        
        # The range formula is: weight * 1 / (dst_scale * dst + 1) ^ 2
        # We have +1 because we want distance of zero to be constant with respect to dst_scale
        # We square the denominator because this causes it to converge
        
        # Update the range values
        scaled_dst = 1 / ((dst_scale * dst + 1) ** 2)
        for key in properties:
            ranges[key] += junctions[next_jun][properties[key]] * scaled_dst
              
        for neighbor, delta, s_id in junctions[next_jun]['neighbors']:
            if neighbor in visited: continue
            neighbor_dst = dst + delta
            heappush(queue, (neighbor_dst, neighbor))
    return ranges

def calculate_ranges(junctions, properties, dst_scale, limit):
    for i, junction in enumerate(junctions):
        ranges = calculate_range(junction, properties, dst_scale, limit)
        for key in ranges:
            junction[key] = ranges[key]
        
        if (i+1) % 100 == 0:
            print(f'\rCalculated {i+1}/{len(junctions)}           ', end='')
    print(f'\rCalculated {len(junctions)}/{len(junctions)}        ')
    
calculate_ranges(
    junctions, 
    {
        'crime_range': 'crime_count',
        'store_range': 'stores_count',
        'transit_range': 'transit_count',
        'rtransit_range': 'rtransit_count',
        'schools_range': 'schools_count'
    }, 
    0.01, 
    500
)
junctions.write_to_file('../processed_data/range_junctions.csv')