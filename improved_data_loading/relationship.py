from category import Category

class Relationship:
    
    def __init__(self, name: str, category_1: Category, category_2: Category, links: tuple[str, str, str], props: None | list[str | tuple[str, str]]=None):
        """ Define a relationship between nodes

        Args:
            name (str): The name of the relationship to use in Neo4j
            category_1 (CategoryHandle): The category that the relationship comes from
            category_2 (CategoryHandle): The category that the relationship goes to
            links (tuple[str, str, str]): The link between categorys. (primary key for category_1, link to category_2, primary key for category_2)
            props (list[str | tuple[str, str]], optional): The fieldnames to use for the relationship properties. Defaults to None, i.e. No properties.
        """
        
        self.name = name
        self.category_1 = category_1
        self.category_2 = category_2
        self.links = links
        self.props = props if props else []