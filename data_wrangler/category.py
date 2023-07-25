from typing import Any

from .dataset import Dataset
from .conversion_functions import Row

class Category:
    """Represents a Neo4j node category
    """
    
    def __init__(self, name: str, data: Dataset, property_names: list[str | tuple[str, str]]):
        """ Create a new node category

        Args:
            name (str): The name of the category to use in Neo4j
            data (Dataset): The data used for the nodes
            property_names (list[str | tuple[str, str]]): The fieldnames to use as the properties for the nodes. 
                Fieldnames can be renamed by using a tuple where the first item is the new name and the second is the old name.
        """
        
        self.name = name
        self.data = data
        self.property_names = property_names
        
    def get_nodes_properties(self) -> list[Row]:
        """ Get a list of rows of properties from rows of data
        
        Extract the properties from each of the rows in the dataset

        Returns:
            list[Row]: The properties for each node
        """
        
        # Each property key can either be a string or it can be a tuple of two strings in which case the first string is used as the 
        # resulting property name while the first is used as the key for accessing the original data
        return [
            { 
                (prop[0] if type(prop) == tuple else prop):                 # type: ignore
                    row[prop[1] if type(prop) == tuple else prop]           # type: ignore
                for prop in self.property_names 
            } 
            for row in self.data
        ]