import csv

from neo4j import Session

from typing import Callable
from typing import Any
from typing import TypeAlias
from collections.abc import Sequence

# Type Declarations
DataHandle: TypeAlias = int
CategoryHandle: TypeAlias = int
RelationshipHandle: TypeAlias = int
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

class GraphLoader:

    def __init__(self, session: Session):
        self._session = session
        self._loaded_data: list[list[dict[str, Any]]] = []
        self._categories: list[dict[str, Any]] = []
        self._relations: list[dict[str, Any]] = []

    def load_file(self, filename: str, conversion_map: ConversionMap, delimiter: str =',', fieldnames: Sequence[str] | None=None, has_header=True) -> DataHandle:
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
            DataHandle: A handle to the loaded data
        """        
        
        # Make sure there is fieldnames information somewhere
        if (fieldnames == None and not has_header):
            raise Exception("If fieldnames is None then has_header must be True")
        
        # Open the file
        with open(filename, 'r', encoding='utf-8-sig') as input_file:
            handle = len(self._loaded_data)
            data = []
            
            # Make all conversions using IndexedConversionMap
            conversions = self._fix_conversion(conversion_map)
            
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
                
            # Store all the loaded data
            self._loaded_data.append(data)
            return handle
        
    def process_data(self, data_handle, func: Callable[[Row], None]):
        """ Run a function on every row in the data
        
        Used for setting more advanced fields that cannot be set in the initial loading

        Args:
            data_handle (DataHandle): The data to process
            func (Callable[[Row], None]): The function to run on every row
        """
        data = self._loaded_data[data_handle]
        for row in data:
            func(row)
        
    def cross_data(self, data_handle_1: DataHandle, data_handle_2: DataHandle, func: Callable[[Row, Row], None]):
        """ Run a function on the cross product of two data sets
        
        WARNING: Creates a cross product between the two data sets. May run slowly for large datasets.
        
        Useful for computing something based on the combination of two data sets. eg. matching nodes
        [func] will receive every combination of pairs of rows with 1 row from data set 1 and 1 row from data set 2

        Args:
            data_handle_1 (DataHandle): The first data set
            data_handle_2 (DataHandle): The second data set
            func (Callable[[Row, Row], None]): The function to run on the cross product of the data sets
        """
        data_1 = self._loaded_data[data_handle_1]
        data_2 = self._loaded_data[data_handle_2]
        for row_1 in data_1:
            for row_2 in data_2:
                func(row_1, row_2)
                
    def match_closest(self, data_handle_1: DataHandle, data_handle_2: DataHandle, match_keys, result_fieldnames):
        """ Pair all the nodes in one data set to the closest node in another dataset
        
        WARNING: Creates a cross product between the two data sets. May run slowly for large datasets.
        
        Distance is the manhattan distance

        Args:
            data_handle_1 (DataHandle): The set of nodes to pair
            data_handle_2 (DataHandle): The set of nodes used for finding the closest node
            match_keys (list[str | tuple(str, str)]): The fieldnames to use for distance. eg: ["latitude", "longitude"] or [("latitude", "LATITUDE"), ("longitude", "LONGITUDE")]
            result_fieldnames (dict[str, tuple | str]): The fieldnames to store the results in. Possible results include the closest node and the distance. eg: {"closest": ("near_node", "id"), "distance": "node_dist"}
        """
        
        # TODO: Add multiple distance functions
        # TODO: Add a distance limiter
        
        # Get the data that will be used
        data_1 = self._loaded_data[data_handle_1]
        data_2 = self._loaded_data[data_handle_2]
        
        # Match for each node in data set 1
        for i, row_1 in enumerate(data_1):
            closest = None
            b_dist = float('inf')
            
            # Find the closest node in data set 2
            for row_2 in data_2:
                # Calculate the distance between [row_1] and [row_2]
                # Manhattan distance
                distance = 0
                for key in match_keys:
                    if type(key) == tuple:
                        diff = row_1[key[0]] - row_2[key[1]]
                    else:
                        diff = row_1[key] - row_2[key]
                    distance += abs(diff)
                    
                # Update the closest node
                if distance < b_dist:
                    closest = row_2
                    b_dist = distance
                    
            # Write the information about the closest node to [row_1]
            if closest != None:
                if "closest" in result_fieldnames:
                   match_name, match_field = result_fieldnames["closest"]
                   row_1[match_name] = closest[match_field]
                if "distance" in result_fieldnames:
                    row_1[result_fieldnames["distance"]] = b_dist
            if i % 100 == 0:
                print(f"\r    Matched {i} nodes. {(i / len(data_1)):.0%} {' ' * 10}", end='')
        print()
        
    def define_category(self, category_name: str, data_handle: DataHandle, value_matcher: list[str | tuple[str, str]]) -> CategoryHandle:
        """ Define a category of nodes

        Args:
            category_name (str): The name of the category to use in Neo4j
            data_handle (DataHandle): The data used for the node
            value_matcher (list[str | tuple[str, str]]): The fieldnames to use as the properties for the nodes

        Returns:
            CategoryHandle: A handle for the category
        """
        handle = len(self._categories)
        self._categories.append({
                "name": category_name,
                "data_handle": data_handle,
                "value_matcher": value_matcher.copy()
        })
        return handle
    
    def define_relation(self, relation_name: str, category_1: CategoryHandle, category_2: CategoryHandle, links: tuple[str, str, str], props: None | list[str | tuple[str, str]]=None) -> RelationshipHandle:
        """ Define a relationship between nodes

        Args:
            relation_name (str): The name of the relationship to use in Neo4j
            category_1 (CategoryHandle): The category that the relationship comes from
            category_2 (CategoryHandle): The category that the relationship goes to
            links (tuple[str, str, str]): The link between categorys. (primary key for category_1, link to category_2, primary key for category_2)
            props (list[str | tuple[str, str]], optional): The fieldnames to use for the relationship properties. Defaults to list[str  |  tuple[str, str]].

        Returns:
            RelationshipHandle: A handle to the relationship
        """
        handle = len(self._relations)
        self._relations.append({
            "name": relation_name,
            "category_1": category_1,
            "category_2": category_2,
            "links": links,
            "props": props if props else []
        })
        return handle
    
    def write_category(self, category_handle: CategoryHandle):
        """ Write a category to Neo4j

        Args:
            category_handle (CategoryHandle): The category to write
        """
        
        category = self._categories[category_handle]
        data = self._loaded_data[category["data_handle"]]
        value_matcher = category["value_matcher"]
        
        # Get a list of the properties for the nodes
        properties = self._match_properties(data, value_matcher)

        # Should be a literal string, not an f-string but this was the only way I could find to set the category
        query = (
        f"UNWIND $properties AS props "
        f'CALL {{'
        f'    WITH props '
        f'    CREATE (n: {category["name"]}) '
        f'    SET n = properties(props) '
        f'}} IN TRANSACTIONS'
        )

        # Execute the query
        self._session.run(
            query,                      # type: ignore
            properties = properties
        )

    def write_relation(self, relation_handle: RelationshipHandle, batch_size=1000):
        """ Write a relationship to Neo4j

        Args:
            relation_handle (RelationshipHandle): The relationship to write
            batch_size (int, optional): A number of nodes to write the connection for at once. Defaults to 1000.
        """
        relation = self._relations[relation_handle]
        category1 = self._categories[relation["category_1"]]
        category2 = self._categories[relation["category_2"]]
        data = self._loaded_data[category1["data_handle"]]
        links = relation["links"]
        props = relation["props"]
        
        # There is no point running the query if there is no data to write
        if len(data) == 0: return
        
        data_1_key, data_match, data_2_key = links

        # Create the links between categories
        link_values = [ 
             [
                row[data_1_key],    # id for category 1
                row[data_match],    # id for category 2
                
                # Relationship properties
                { 
                 (prop[0] if type(prop) == tuple else prop): (row[prop[1]] if type(prop) == tuple else row[prop]) for prop in props 
                }
             ]
             for row in data
        ]

        # Create the where clauses for the query
        compare = "IN" if type(data[0][data_match]) == list else "="
        where_1 = f"WHERE n1.{data_1_key} = row[0]"
        where_2 = f"WHERE n2.{data_2_key} {compare} row[1]"

        # Create the query
        # Should be a literal string, not an f-string but this was the only way I could find to set the category
        query = (
        f'UNWIND $data AS row '
        f'CALL {{ '
        f'    WITH row '
        f'    MATCH (n1: {category1["name"]}) {where_1} '
        f'    WITH row, n1 '
        f'    MATCH (n2: {category2["name"]}) {where_2} '
        f'    CREATE (n1)-[r:{relation["name"]}]->(n2) '
        f'    SET r = properties(row[2]) '
        f'}} IN TRANSACTIONS'
        )

        # Run the query for each batch
        for batch in range(0, len(link_values), batch_size):
            sub_link_values = link_values[batch:batch + batch_size]
            self._session.run(
                query, # type: ignore
                data = sub_link_values
            )
            
            # Update the progress information
            print(f"\rWriting {relation['name']} {((batch + len(sub_link_values)) / len(link_values)):.0%}" + (" " * 10), end='')
        print()
        
    def clear_all(self):
        """ Delete all nodes and relationships from the Neo4j database
        """
        print("Clearing all data")
        
        # It's a complicated query to avoid running out of memory for large databases
        self._session.run(
            '''
            MATCH (n)
            CALL {
                WITH n
                DETACH DELETE n
            } IN TRANSACTIONS
            '''
        )

    def _match_properties(self, data: list[dict[str, Any]], properties: list[str  | tuple[str, str]]) -> list[dict[str, Any]]:
        """ Get a list of rows of properties from rows of data

        Args:
            data (list[dict[str, Any]]): The data to select part of
            properties (list[str   |  tuple[str, str]]): The properties to select

        Returns:
            list[dict[str, Any]]: The properties for each node
        """
        
        # Each property key can either be a string or it can be a tuple of two strings in which case the first string is used as the 
        # resulting property name while the first is used as the key for accessing the original data
        return [
            { prop[0] if type(prop) == tuple else prop: row[prop[1] if type(prop) == tuple else prop] for prop in properties } # type: ignore
            for row in data
        ]
        
    def _fix_conversion(self, conversions: ConversionMap) -> dict[str, Callable[[Row, int], Any]]:
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
            elif type(conversions[key])  == RowFunction:
                # Have to use instantly called lambda expression wrapper to avoid late binding
                result[key] = (lambda rowf: rowf.f)(conversions[key])                       # type: ignore
            # The conversion is function
            else:
                # Have to use instantly called lambda expression wrapper to avoid late binding
                result[key] = (lambda key: 
                    lambda row, index: conversions[key](row[key])                           # type: ignore
                )(key)    
        return result