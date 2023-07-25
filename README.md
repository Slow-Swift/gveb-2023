
# Graph Network Backcloth Visualizer

This work is part of a research project for Summer 2023
This is an extension of the work carried out as a part of the MITACS Globalink Research Internship 2022 @ 
British Columbia, Canada.

The project aims to simulate the street networks of the city of Vancouver, and 
derive research results based on the different factors that influence the 
susceptibility of a street segment or junction to crime.

For more in depth details about the project check out project_description.md or project_description.pdf.

## Tech Stack

**Graph Visualization:** GraphXR

**Graph Database:** Neo4j Database

**Data Processing:** Python

## Screenshots

![App Screenshot](https://i.imgur.com/WMHF2JN.png)

![App Screenshot](https://i.imgur.com/ISKksp2.png)

![App Screenshot](https://i.imgur.com/X6tyhVn.png)

## Quick Setup

In order to setup the project on a new system:
1. Clone the repository to your device
1. (Optional) Create and activate a virtual environment
    - Create with `python -m venv env_name`
    - On Windows activate with `env_name/scripts/activate`
    - On Linux or Mac activate with `source env_name/bin/activate`
1. From the project root folder run `pip install -r requirements.txt`
1. Create a Neo4j account and database making sure to download the file that includes the database password
1. Change DATABASE_INFO_FILEPATH in data_loading/main.py to point to the downloaded database info file
1. From the data_loading folder run python main.py to load the data into the database. This could take a while.
1. Create a GraphXR account and create a project that is conencted to the Neo4j database
1. From GraphXR open Project/Extensions and select grove. Then select the three dots and choose import files and import the grove scripts from grove_notebooks.
1. (Optional. Required for street view to work) Create a Google developers account and create a Google Maps Javascript API key. Create a new secret called 'Google API key' under settings on grove. The value of the secret should be the Google Maps API key.

## Using
The data_wrangler folder provides various classes to easily cleanup and analyze data and then load the data into Neo4j. The documentation for data_wrangler is unfortunately very limited at the moment. The best way to understand how it works is to refer to examples of its use in data_cleanup and in data_loading/main.py. data_loading/main.py shows how data can be loaded to the Neo4j database.

Neo4j is currently only used as an intermediary for storing the graph model in a way that GraphXR can understand. In the future it would be useful to look into how to do advanced analysis using Neo4j.

GraphXR can be used to visualize the graph network. Once setup to load data from the Neo4j database, the data can be loaded
by using the graph management grove script under extensions. This script allows one to easily load/unload part or the whole of the graph network. To visualize the graph on a map the map icon on the left sidebar of GraphXR can be clicked. GraphXR provides many tools for visually analyzing the graph and is useful for better understanding the model.