class Category:
    
    def __init__(self, name: str, data_handle, value_matcher: list[str | tuple[str, str]]):
        """ Create a new node category

        Args:
            name (str): The name of the category to use in Neo4j
            data_handle (DataHandle): The data used for the nodes
            value_matcher (list[str | tuple[str, str]]): The fieldnames to use as the properties for the nodes
        """
        
        self.name = name
        self.data_handle = data_handle
        self.value_matcher = value_matcher