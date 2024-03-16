import sys
sys.path.append('../') # This should probably be changed to a more sofisticated system at some point. i.e. install the package

from ast import literal_eval

from data_wrangler import Dataset
import requests

INPUT_FOLDER = '../data/cleaned_data'
OUTPUT_FOLDER = '../data/cleaned_data'
JUNCTIONS = f'{INPUT_FOLDER}/reach_junctions.csv'

junctions = Dataset.load_file(JUNCTIONS)

junctions.convert_property("latitude", float)
junctions.convert_property("longitude", float)

url = "https://api.open-elevation.com/api/v1/lookup"
locations = [{'longitude': junction['longitude'], 'latitude': junction['latitude']} for junction in junctions]
response = requests.post(url, json={'locations': locations})

results = response.json()["results"]
junctions.add_property("elevation", value=0)
nonZero = False
for junction, result in zip(junctions, results):
    junction["elevation"] = result["elevation"]
    if result["elevation"] != 0:
        print(result["elevation"])
        nonZero = True

junctions.write_to_file(f'{OUTPUT_FOLDER}/reach_junctions.csv')
        