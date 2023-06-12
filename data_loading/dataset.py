from __future__ import annotations

import warnings

import csv
from math import cos, sin, atan2, sqrt, pi

from typing import Callable
from typing import Any
from collections.abc import Sequence

from conversion_functions import Row
from conversion_functions import RowFunction
from conversion_functions import ConversionMap

class Dataset:
    
    def __init__(self, rows: list[Row], primary_key='id'):
        self._rows = rows
        self.primary_key = primary_key
        
        if len(self._rows) > 0 and not self.primary_key in self._rows[0]:
            warnings.warn("WARNING: Primary key not in dataset")
        
    def __len__(self):
        return len(self._rows)
    
    def __iter__(self):
        return iter(self._rows)
    
    def __getitem__(self, index):
        return self._rows[index]
    
    def for_each(self, func: Callable[[Row], None]):
        """ Run a function on every row in the data
        
        Used for setting more advanced fields that cannot be set in the initial loading

        Args:
            func (Callable[[Row], None]): The function to run on every row
        """
        for row in self:
            func(row)
            
    def match_closest(self, other_data: Dataset, distance_func: Callable[[Row, Row], float], on_match: Callable[[Row, Row, float], None]):
        """ Pair all the nodes in one data set to the closest node in another dataset
        
        WARNING: Creates a cross product between the two data sets. May run slowly for large datasets.
        
        Distance is the manhattan distance

        Args:
            other_data (Dataset): The set of nodes used for finding the closest node
            distance_func (Callable[[Row, Row], float]): The function to use for calculating distance between two rows
            on_match (Callable[[Row, Row, float], None]): The function to run when a row is matched with its closest row
        """
        
        # TODO: Add a distance limiter
        
        # Match for each node in this dataset
        for i, row_1 in enumerate(self):
            closest = None
            b_dist = float('inf')
            
            # Find the closest node in data set 2
            for row_2 in other_data:
                distance = distance_func(row_1, row_2)
                    
                # Update the closest node
                if distance < b_dist:
                    closest = row_2
                    b_dist = distance
              
            # Write the information about the closest node to [row_1]
            if closest != None:
                on_match(row_1, closest, b_dist)
            
            # Log the progress
            if i % 100 == 0:
                print(f"\r    Matched {i} nodes. {(i / len(self)):.0%} {' ' * 10}", end='')
        print(f"\r    Matched {len(self)} nodes. 100% {' ' * 10}")
        
    def match_closest_p_norm(
        self, other_data: Dataset, match_keys: list[str | tuple[str, str]], on_match: Callable[[Row, Row, float], None], p_norm:float=2
    ):
        """ Pair all the nodes in one data set to the closest node in another dataset
        
        WARNING: Creates a cross product between the two data sets. May run slowly for large datasets.
        
        Distance is the manhattan distance

        Args:
            other_data (Dataset): The set of nodes used for finding the closest node
            match_keys (list[str | tuple(str, str)]): The fieldnames to use for distance. eg: ["latitude", "longitude"] or [("latitude", "LATITUDE"), ("longitude", "LONGITUDE")]
            on_match (Callable[[Row, Row, float], None]): The function to run when a row is matched with its closest row
            p_norm (float, optional): The p_norm function to use for calculating distance. Defaults to 2 (Euclidean distance)
        """
        def distance(row_1: Row, row_2: Row) -> float:
            distance = 0
            for key in match_keys:
                if type(key) == tuple:
                    delta = row_1[key[0]] - row_2[key[1]]
                else:
                    delta = row_1[key] - row_2[key]              # type: ignore  # Ignoring type because it should be str
                distance += pow(abs(delta), p_norm)
            return pow(distance, 1/p_norm)
        
        self.match_closest(other_data, distance, on_match)
        
    def match_lat_lng(self, other_data: Dataset, match_field: str, dst_field:str):
        """ Pair all the rows in this dataset with the closest row in [other_data] based on latitude and longitude.
        
        The haversine formula is used to calculate distance in meters from latitude and longitude

        Args:
            other_data (Dataset): The data to match to
            match_field (str): The name of the field in which to store the primary key of the other row of the match
            dst_field (str): The name of the field in which to store the distance of the match
        """
        def on_match(row_1, row_2, dst):
            row_1[match_field] = row_2[other_data.primary_key]
            row_1[dst_field] = dst
            
        # Implementation of the haversine formula found at 
        # https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula#:~:text=from%20math%20import%20cos%2C%20asin,of%20completeness%3A%20Haversine%20on%20Wikipedia.
        def distance(row_1: Row, row_2: Row):
            degrees_to_radians = pi / 180
            radius = 6371   # Radius of the earth in km
            
            lat1 = row_1['latitude']
            lon1 = row_1['longitude']
            lat2 = row_2['latitude']
            lon2 = row_2['longitude']
            
            delta_lat = lat1 - lat2
            delta_lon = lon1 - lon2
            
            delta_lat_rad = delta_lat * degrees_to_radians
            delta_lon_rad = delta_lon * degrees_to_radians
            
            a = (
                sin(delta_lat_rad / 2) ** 2 + 
                cos(lat1 * degrees_to_radians) * cos(lat2 * degrees_to_radians) *
                sin(delta_lon_rad / 2) ** 2
            )
            a = min(a, 1) # Clamp a to 1 incase of floating point errors or approximations
            
            
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return radius * c * 1000
        
        self.match_closest(other_data, distance, on_match)
    
    def match_lat_lng_approx(self, other_data: Dataset, match_field: str, dst_field:str):
        """ Pair all the rows in this dataset with the aprroximated closes row in [other_data] based on latitude and longitude.
        
        The haversine formula is used to calculate distance in meters from latitude and longitude
        The approximation should be close for points that are near to each other. 
        sin(x) is approximated with x 

        Args:
            other_data (Dataset): The data to match to
            match_field (str): The name of the field in which to store the primary key of the other row of the match
            dst_field (str): The name of the field in which to store the distance of the match
        """
        
        def on_match(row_1, row_2, dst):
            row_1[match_field] = row_2[other_data.primary_key]
            row_1[dst_field] = dst
            
        # Implementation of the haversine formula found at 
        # https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula#:~:text=from%20math%20import%20cos%2C%20asin,of%20completeness%3A%20Haversine%20on%20Wikipedia.
        def distance(row_1: Row, row_2: Row):
            degrees_to_radians = pi / 180
            radius = 6371   # Radius of the earth in km
            
            lat1 = row_1['latitude']
            lon1 = row_1['longitude']
            lat2 = row_2['latitude']
            lon2 = row_2['longitude']
            
            delta_lat = lat1 - lat2
            delta_lon = lon1 - lon2
            
            delta_lat_rad = delta_lat * degrees_to_radians
            delta_lon_rad = delta_lon * degrees_to_radians
            
            # delta_lat_rad and delta_lon_rad should be quite small so sin(delta_lat_rad) can be approximated with delta_lat_rad
            a = (
                delta_lat_rad * delta_lat_rad +
                cos(lat1 * degrees_to_radians) * cos(lat2 * degrees_to_radians) *
                delta_lon_rad * delta_lon_rad
            )
            
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return radius * c * 1000
        
        self.match_closest(other_data, distance, on_match)
    
    @staticmethod
    def cross_data(data_1: Dataset, data_2: Dataset, func: Callable[[Row, Row], None]):
        """ Run a function on the cross product of two data sets
        
        WARNING: Creates a cross product between the two data sets. May run slowly for large datasets.
        
        Useful for computing something based on the combination of two data sets. eg. matching nodes
        [func] will receive every combination of pairs of rows with 1 row from data set 1 and 1 row from data set 2

        Args:
            data_1 (Dataset): The first data set
            data_2 (Dataset): The second data set
            func (Callable[[Row, Row], None]): The function to run on the cross product of the data sets
        """
        for row_1 in data_1:
            for row_2 in data_2:
                func(row_1, row_2)
    
    @staticmethod
    def load_file(filename: str, conversion_map: ConversionMap, primary_key='id', delimiter: str =',', fieldnames: Sequence[str] | None=None, has_header=True):
        """Load data from a csv file
        
        [conversion_map] is used to manipulate the read data in order to turn it into more useful formats and types. A ConversionMap is a dictionary
        mapping fieldnames to either a function on one parameter, a tuple containing a function on one parameter and a fieldname, or a RowFunction.
        The result of the function is stored in the data using the first fieldname.
        
        Example:
        ```
        {
            "id": int,
            "name": (str, "Name"),
            "indexName": RowFunction(lambda row, i: str(i) + str(row["Name"]))
        }
        ```
        
        The value matched to "id" in the input is passed to int and stored in "id" in the output.
        The value matched to "Name" in the input is passed to str and stored in "name" in the output.
        The row and an index value is passed to the lambda function which joins the index with the "Name" attribute of the input, and the result is
        stored in "indexName" of the output.

        Args:
            filename (str): The name of the file to load. Should be a csv file.
            conversion_map (ConversionMap): A mapping between fieldnames in the output data and a function on the input data.
            delimiter (str, optional): The delimiter used by the csv file. Defaults to ','.
            fieldnames (Sequence[str] | None): The names to use for the fields. Defaults to None.
            has_header (boolean): Whether or not there is a header row in the file. Must be true if fieldnames is None.

        Returns:
            RowData: The loaded data
        """        
        
        # Make sure there is fieldname information somewhere
        if (fieldnames == None and not has_header):
            raise Exception("If fieldnames is None then has_header must be True")
        
        # Open the file
        with open(filename, 'r', encoding='utf-8-sig') as input_file:
            data = []
            
            # Make all conversions using IndexedConversionMap
            conversions = Dataset._fix_conversion(conversion_map)
            
            # Read each row of the file
            rows = csv.DictReader(input_file, quoting=csv.QUOTE_MINIMAL, delimiter=delimiter, fieldnames=fieldnames)
            
            # Read the header if necessary
            if(fieldnames != None and has_header):
                next(rows)
            
            # Read each row
            for i, row in enumerate(rows):
                # Apply the conversion to the row to get a result
                result = { 
                    key: conversions[key](row, i) for key in conversions
                }
                
                data.append(result)
                
            return Dataset(data, primary_key)
        
    @staticmethod
    def _fix_conversion(conversions: ConversionMap) -> dict[str, Callable[[Row, int], Any]]:
        """Modify a ConversionMap to only used IndexedConversionFunctions   

        Args:
            conversions (ConversionMap): The conversion map to fix

        Returns:
            dict[str, IndexedConversionFunction]: The fixed conversion map
        """
        
        result = {}
        for key in conversions:
            # The conversion is (function, key_in)
            if type(conversions[key]) == tuple:
                func = conversions[key][0]                                                  # type: ignore
                fieldname = conversions[key][1]                                             # type: ignore
                
                # Have to use instantly called lambda expression wrapper to avoid late binding
                result[key] = (lambda func, fn: 
                    lambda row, index: func(row[fn]))(func, fieldname)
            # The conversion is RowFunction(function)
            elif type(conversions[key]) == RowFunction:
                # Have to use instantly called lambda expression wrapper to avoid late binding
                result[key] = (lambda rowf: rowf.f)(conversions[key])                       # type: ignore
            # The conversion is function
            else:
                # Have to use instantly called lambda expression wrapper to avoid late binding
                result[key] = (lambda key: 
                    lambda row, index: conversions[key](row[key])                           # type: ignore
                )(key)    
        return result