from typing import Callable
from typing import Any
from typing import TypeAlias
from collections.abc import Sequence

Row: TypeAlias = dict[str, Any]
ConversionFunction: TypeAlias = Callable[[Any], Any]

class RowFunction:
    def __init__(self, f: Callable[[Row, int], Any]):
        self.f = f

ConversionMap: TypeAlias = dict[str, ConversionFunction | RowFunction | tuple[ConversionFunction, str]]

def is_not_null(val):
    return (val or str.isspace(val) or val == 0)

def convert_if_not_null(val, convert=float, on_null: Any=0):
    return convert(val) if is_not_null(val) else on_null

def create_regular_str(old_str):
    if not old_str.isnumeric(): return old_str
    return old_str if int(old_str)>9 else "0"+old_str

def split_latitude(latlng):
    return float(latlng.split(',')[0])

def split_longitude(latlng):
    return float(latlng.split(',')[1])

generate_id = RowFunction(lambda row, i: i + 1)