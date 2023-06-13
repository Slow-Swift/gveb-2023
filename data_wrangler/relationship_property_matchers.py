from typing import TypeAlias
from typing import Callable

from .conversion_functions import Row

RelationPropertyMatcher: TypeAlias = Callable[[Row, Row], Row]

def first_set_prop_match(properties: list[str | tuple[str, str]]) -> Callable[[Row, Row], Row]:
    return lambda row1, row2: match_props(row1, properties)

def second_set_prop_match(properties: list[str | tuple[str, str]]) -> Callable[[Row, Row], Row]:
    return lambda row1, row2: match_props(row2, properties)
    
def dual_set_prop_match(set_1_properties: list[str | tuple[str, str]], set_2_properties: list[str | tuple[str, str]]) -> Callable[[Row, Row], Row]:
    return lambda row1, row2: match_props(row1, set_1_properties) | match_props(row2, set_2_properties)

def match_props(row: Row, properties: list[str | tuple[str, str]]) -> Row:
    return { 
        (prop[0] if type(prop) == tuple else prop):                 # type: ignore
            (row[prop[1]] if type(prop) == tuple else row[prop])    # type: ignore
        for prop in properties                                  
    }