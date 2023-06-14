from typing import Any

from .dataset import Dataset

class Category:
    
    def __init__(self, name: str, data: Dataset, property_names: list[str | tuple[str, str]]):
        """ Create a new node category

        Args:
            name (str): The name of the category to use in Neo4j
            data (Dataset): The data used for the nodes
            property_matcher (list[str | tuple[str, str]]): The fieldnames to use as the properties for the nodes
            primary_key (str, optional): The fieldname that is unique for each entry. Defaults to 'id'
        """
        
        self.name = name
        self.data = data
        self.property_names = property_names
        
    def get_nodes_properties(self) -> list[dict[str, Any]]:
        """ Get a list of rows of properties from rows of data

        Returns:
            list[dict[str, Any]]: The properties for each node
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