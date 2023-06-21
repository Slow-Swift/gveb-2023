import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import math

from data_wrangler import Dataset

JUNCTION_FILE = '../processed_data/reach_junctions.csv'

junctions = Dataset.load_file(
    JUNCTION_FILE,
    {
        'id': int,
        'crime_count': int,
        'stores_count': int,
        'transit_count': int,
        'rapid_transit_count': int,
        'schools_count': int,
        'crime_reach': float,
        'store_reach': float,
        'transit_reach': float,
        'rapid_transit_reach': float,
        'schools_reach': float,
    }
)

crime_reaches = np.array([j['crime_reach'] for j in junctions])
store_reaches = np.array([j['store_reach'] for j in junctions])
transit_reaches = np.array([j['transit_reach'] for j in junctions])
rtransit_reaches = np.array([j['rapid_transit_reach'] for j in junctions])
schools_reaches = np.array([j['schools_reach'] for j in junctions])

crime_counts = np.array([j['crime_count'] for j in junctions])
store_counts = np.array([j['stores_count'] for j in junctions])
transit_count = np.array([j['transit_count'] for j in junctions])
rtransit_count = np.array([j['rapid_transit_count'] for j in junctions])
schools_count = np.array([j['schools_count'] for j in junctions])

use_reach = True
label_names = "Reach" if use_reach else "Count"

crime_data = crime_reaches if use_reach else crime_counts
store_data = store_reaches if use_reach else store_counts
transit_data = transit_reaches if use_reach else transit_count
rtransit_data = rtransit_reaches if use_reach else rtransit_count
schools_data = schools_reaches if use_reach else schools_count

def hist_mean(x_data, y_data, bin_count):
    bins = [[0,0] for _ in range(bin_count)]
    min_x, max_x = min(x_data), max(x_data)
    width = (max_x - min_x) / bin_count
    
    for i in range(len(x_data)):
        index = math.floor((x_data[i] - min_x) / width)
        index = min(index, bin_count - 1) # The max value results in an index of bin_count
        bins[index][1] += y_data[i]
        bins[index][0] += 1
        
    bins_x = [min_x + width * i for i in range(bin_count)]
    bins_y = [b[1] / b[0] if b[0] else 0 for b in bins]
    
    bins_count_norm = [b[0] for b in bins]
    bins_count_norm = [b / max(bins_count_norm) for b in bins_count_norm]
    
    return bins_x, bins_y, bins_count_norm, width

def analyze(ax: plt.Axes, data, xlabel, ylabel):
    # Get and sort the data
    x_data, y_data = data
    sort = x_data.argsort()
    x_data = x_data[sort]
    y_data = y_data[sort]
    
    bins_x, bins_y, bins_count, width = hist_mean(x_data, y_data, 20)
    
    # Plot the data
    ax.scatter(x_data, y_data)
    ax.bar(bins_x, bins_count, width=width, align='edge', color="purple", alpha=0.5)
    ax.step([*bins_x, max(x_data)], [*bins_y, bins_y[-1]], where="post", color="green", linewidth=3)
    ax.plot(np.unique(x_data), np.poly1d(np.polyfit(x_data, y_data, 1))(np.unique(x_data)), color="red", linewidth=3)
    
    # Label the plot
    ax.set_ylabel(f'{ylabel} {label_names}')
    ax.set_xlabel(f'{xlabel} {label_names}')
  
analyze(plt.subplot(2, 2, 1), (store_data, crime_data), 'Store', 'Crime')  
analyze(plt.subplot(2, 2, 2), (transit_data, crime_data), 'Transit', 'Crime')  
analyze(plt.subplot(2, 2, 3), (rtransit_data, crime_data), 'Rapid Transit', 'Crime')  
analyze(plt.subplot(2, 2, 4), (schools_data, crime_data), 'Schools', 'Crime')  

# fig = plt.figure()
# ax = fig.add_subplot(projection='3d')
# ax.scatter(store_data, transit_data, crime_data)
# ax.set_xlabel(f"Stores {label_names}")
# ax.set_ylabel(f"Transit {label_names}")
# ax.set_zlabel(f'Crime {label_names}')

plt.show()