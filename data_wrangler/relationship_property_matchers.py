from typing import TypeAlias
from typing import Callable

from .conversion_functions import Row

RelationPropertyMatcher: TypeAlias = Callable[[Row, Row], Row]

def first_set_prop_match(properties: list[str]) -> RelationPropertyMatcher:
    """Select properties from the first dataset in a relationship

    Args:
        properties (list[str]): The names of the properties

    Returns:
        RelationPropertyMatcher: The property matcher
    """
    return lambda row1, row2: match_props(row1, properties)

def second_set_prop_match(properties: list[str]) -> RelationPropertyMatcher:
    """Select properties from the seconds dataset in a relationship

    Args:
        properties (list[str]): The names of the properties

    Returns:
        RelationPropertyMatcher: The property matcher
    """
    return lambda row1, row2: match_props(row2, properties)
    
def dual_set_prop_match(set_1_properties: list[str], set_2_properties: list[str]) -> RelationPropertyMatcher:
    """Select properties from both datasets in a relationship

    Args:
        set_1_properties (list[str]): The names of the properties to pull from dataset 1
        set_2_properties (list[str]): The names of the properties to pull from dataset 2

    Returns:
        RelationPropertyMatcher: The property matcher
    """
    return lambda row1, row2: match_props(row1, set_1_properties) | match_props(row2, set_2_properties)

def match_props(row: Row, properties: list[str]) -> Row:
    """Get the properties from a row

    Args:
        row (Row): The row to get the properties from
        properties (list[str]): The properties to get

    Returns:
        Row: The properties
    """
    
    #TODO: Simplify this as the tuple type does not need to be checked
    return { 
        (prop[0] if type(prop) == tuple else prop):                 # type: ignore
            (row[prop[1]] if type(prop) == tuple else row[prop])    # type: ignore
        for prop in properties                                  
    }