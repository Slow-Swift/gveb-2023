from typing import Any

from .category import Category
from .dataset import Row

class Relationship:
    
    def __init__(self, name: str, category_1: Category, category_2: Category, neighbor_name: str, props: None | list[str | tuple[str, str]]=None):
        """ Define a relationship between nodes

        Args:
            name (str): The name of the relationship to use in Neo4j
            category_1 (CategoryHandle): The category that the relationship comes from
            category_2 (CategoryHandle): The category that the relationship goes to
            neighbor_name (str): The fieldname that links the primary keys of the categories
            props (list[str | tuple[str, str]], optional): The fieldnames to use for the relationship properties. Defaults to None, i.e. No properties.
        """
        
        self.name = name
        self.category_1 = category_1
        self.category_2 = category_2
        self.neighbor_name = neighbor_name
        self.props = props if props else []
        
    def has_muliple_links(self) -> bool:
        if len(self.category_1.data) == 0: return False
        return type(self.category_1.data[0][self.neighbor_name])
        
    def get_links(self) -> list[tuple[Any, Any, Row]]:
        # TODO: Come up with a better system that allows properties to be pulled from both categories
        
        data = self.category_1.data
        
        links = [ 
             [
                row[self.category_1.data.primary_key],   # From id
                row[self.neighbor_name],                 # To id(s)
                
                # Relationship properties
                { 
                    (prop[0] if type(prop) == tuple else prop):                 # type: ignore
                        (row[prop[1]] if type(prop) == tuple else row[prop])    # type: ignore
                        for prop in self.props                                  
                }                                                               
             ]
             for row in data
        ]
        
        return links                # type: ignore                                                                        