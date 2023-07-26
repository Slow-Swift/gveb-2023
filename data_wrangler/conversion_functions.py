from typing import Callable
from typing import Any
from typing import TypeAlias

Row: TypeAlias = dict[str, Any]
ConversionFunction: TypeAlias = Callable[[Any], Any]

class RowFunction:
    """Deprecated do not use
    """
    def __init__(self, f: Callable[[Row, int], Any]):
        self.f = f

ConversionMap: TypeAlias = dict[str, ConversionFunction | RowFunction | tuple[ConversionFunction, str]]
"""Deprecated do not use"""

def is_not_null(val: Any) -> bool:
    """Determine whether a value is null
    
    Only None or '' is considered a null value

    Args:
        val (Any): The value to check

    Returns:
        bool: True if the value is not null
    """
    return (val or str.isspace(val) or val == 0)

def convert_if_not_null(val: Any, convert=float, on_null: Any=0) -> Any:
    """Apply convert if val is not null otherwise return on_null

    Args:
        val (Any): The value to convert
        convert (Callable[[Any], Any], optional): The function used to convert. Defaults to float.
        on_null (Any, optional): The value to return when val is null. Defaults to 0.

    Returns:
        Any: The converted value
    """
    return convert(val) if is_not_null(val) else on_null

def create_regular_str(old_str: str) -> str:
    """Make a numberic string at least two digits long padding with zeros on the left

    Args:
        old_str (str): The original string

    Returns:
        str: The regular string
    """
    if not old_str.isnumeric(): return old_str
    return old_str if int(old_str)>9 else "0"+old_str

def split_latitude(latlng: str) -> float:
    """Return the latitude portion of a string 'latitude, longitude'

    Args:
        latlng (str): The lat long string

    Returns:
        float: The latitude
    """
    return float(latlng.split(',')[0])

def split_longitude(latlng: str) -> float:
    """Return the longitude portion of a string 'latitude, longitude'

    Args:
        latlng (str): The lat long string

    Returns:
        float: The longitude
    """
    return float(latlng.split(',')[1])

generate_id = RowFunction(lambda row, i: i + 1)
"""Deprecated. Do not use."""