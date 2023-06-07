from __future__ import annotations

import warnings

import csv

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
            
    def match_closest(self, other_data: Dataset, match_keys: list[str | tuple[str, str]], on_match: Callable[[Row, Row, float], None]):
        """ Pair all the nodes in one data set to the closest node in another dataset
        
        WARNING: Creates a cross product between the two data sets. May run slowly for large datasets.
        
        Distance is the manhattan distance

        Args:
            other_data (Dataset): The set of nodes used for finding the closest node
            match_keys (list[str | tuple(str, str)]): The fieldnames to use for distance. eg: ["latitude", "longitude"] or [("latitude", "LATITUDE"), ("longitude", "LONGITUDE")]
            result_fieldnames (dict[str, tuple | str]): The fieldnames to store the results in. Possible results include the closest node and the distance. eg: {"closest": ("near_node", "id"), "distance": "node_dist"}
        """
        
        # TODO: Add multiple distance functions
        # TODO: Add a distance limiter
        
        # Match for each node in this dataset
        for i, row_1 in enumerate(self):
            closest = None
            b_dist = float('inf')
            
            # Find the closest node in data set 2
            for row_2 in other_data:
                # Calculate the distance between [row_1] and [row_2]
                # Manhattan distance
                distance = 0
                for key in match_keys:
                    if type(key) == tuple:
                        diff = row_1[key[0]] - row_2[key[1]]
                    else:
                        diff = row_1[key] - row_2[key]              # type: ignore  # Ignoring type because it should be str
                    distance += abs(diff)
                    
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
        
    def match_lat_lng(self, other_data: Dataset, match_field: str, dst_field:str):
        def on_match(row_1, row_2, dst):
            row_1[match_field] = row_2[other_data.primary_key]
            row_1[dst_field] = dst
        
        self.match_closest(
            other_data,
            ['latitude', 'longitude'],
            on_match=on_match
        )
    
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