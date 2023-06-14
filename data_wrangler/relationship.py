from typing import Any

from .category import Category
from .dataset import Row
from .relationship_property_matchers import RelationPropertyMatcher

class Relationship:
    
    def __init__(self, name: str, category_1: Category, category_2: Category, neighbor_name: str, prop_matcher: None | RelationPropertyMatcher = None, remove_duplicates=False):
        """ Define a relationship between nodes

        Args:
            name (str): The name of the relationship to use in Neo4j
            category_1 (CategoryHandle): The category that the relationship comes from
            category_2 (CategoryHandle): The category that the relationship goes to
            neighbor_name (str): The fieldname that links the primary keys of the categories
            prop_matcher (RelationPropertyMatcher, optional): The function that gives the relationship properties given two rows. Defaults to None, i.e. No properties.
        """
        
        self.name = name
        self.category_1 = category_1
        self.category_2 = category_2
        self.neighbor_name = neighbor_name
        self.prop_matcher = prop_matcher if prop_matcher else (lambda r1, r2: dict())
        self.remove_duplicates = remove_duplicates
        
    def get_links(self) -> list[tuple[Any, Any, Row]]:
        from_data = self.category_1.data
        to_data = self.category_2.data
        
        processed = set()
        
        links = []
        for row in from_data:
            neighbors = row[self.neighbor_name]
            if type(neighbors) != list:
                neighbors = [neighbors]
                
            for neighbor in neighbors:
                primary_key = row[self.category_1.data.primary_key]
                
                if self.remove_duplicates and (((primary_key, neighbor) in processed) or ((neighbor, primary_key) in processed)): continue
                
                processed.add((primary_key, neighbor))
                links.append([
                    row[self.category_1.data.primary_key],
                    neighbor,
                    self.prop_matcher(row, to_data[neighbor])
                ])
        
        return links                                                                     