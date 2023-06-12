
# Graph Network Backcloth Visualizer

This work is part of a research project for Summer 2023
This is an extension of the work carried out as a part of the MITACS Globalink Research Internship 2022 @ 
British Columbia, Canada.

The project aims to simulate the street networks of the city of Vancouver, and 
derive research results based on the different factors that influence the 
susceptibility of a street segment or junction to crime.

## Tech Stack

**Frontend:** GraphXR

**Backend:** Neo4j Database

**Language used for scripts:** Python
## Screenshots

![App Screenshot](https://i.imgur.com/WMHF2JN.png)

![App Screenshot](https://i.imgur.com/ISKksp2.png)

![App Screenshot](https://i.imgur.com/X6tyhVn.png)

## Setup

In order to setup the project on a new system:
1. Create a Neo4j account and database making sure to download the file that includes the database password
2. Change DATABASE_INFO_FILEPATH in data_loading/main.py to point to the downloaded database info file
3. From the project root folder run pip install -r requirements.txt
4. From the data_loading folder run python main.py to load the data into the database. This could take a while.
5. Create a GraphXR account and create a project that is conencted to the Neo4j database
6. From GraphXR open Project/Extensions and select grove. Then select the three dots and choose import files and import the grove scripts from grove_notebooks.
7. Create a Google developers account and create a Google Maps Javascript API key. Create a new secret called 'Google API key' under settings on grove. The value of the secret should be the Google Maps API key.