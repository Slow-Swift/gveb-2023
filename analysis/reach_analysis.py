import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

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

crime_reaches = [j['crime_reach'] for j in junctions]
store_reaches = [j['store_reach'] for j in junctions]
transit_reaches = [j['transit_reach'] for j in junctions]
rtransit_reaches = [j['rapid_transit_reach'] for j in junctions]
schools_reaches = [j['schools_reach'] for j in junctions]

crime_counts = [j['crime_count'] for j in junctions]
store_counts = [j['stores_count'] for j in junctions]
transit_count = [j['transit_count'] for j in junctions]
rtransit_count = [j['rapid_transit_count'] for j in junctions]
schools_count = [j['schools_count'] for j in junctions]

use_reach = True

crime_data = crime_reaches if use_reach else crime_counts
store_data = store_reaches if use_reach else store_counts
transit_data = transit_reaches if use_reach else transit_count
rtransit_data = rtransit_reaches if use_reach else rtransit_count
schools_data = schools_reaches if use_reach else schools_count

WIDTH = 2
HEIGHT = 2

plt.figure()
plt.subplot(2, 2, 1)
plt.scatter(store_data, crime_data)
plt.ylabel('Crime Reach')
plt.xlabel('Store Reach')

plt.subplot(2, 2, 2)
plt.scatter(transit_data, crime_data)
plt.ylabel('Crime Reach')
plt.xlabel('Transit Reach')

plt.subplot(2, 2, 3)
plt.scatter(rtransit_data, crime_data)
plt.ylabel('Crime Reach')
plt.xlabel('Rapid Transit Reach')

plt.subplot(2, 2, 4)
plt.scatter(schools_data, crime_data)
plt.ylabel('Crime Reach')
plt.xlabel('Schools Reach')

fig = plt.figure()
ax = fig.add_subplot(projection='3d')
ax.scatter(store_data, transit_data, crime_data)
ax.set_xlabel("Stores Reach")
ax.set_ylabel("Transit Reach")
ax.set_zlabel("Crime Reach")

plt.show()