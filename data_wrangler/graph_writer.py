from neo4j import Session

from .category import Category
from .relationship import Relationship

class GraphWriter:

    def __init__(self, session: Session):
        self._session = session
    
    def write_category(self, category: Category):
        """ Write a category to Neo4j

        Args:
            category_handle (CategoryHandle): The category to write
        """
        
        # Get a list of the properties for the nodes
        properties = category.get_nodes_properties()

        # Should be a literal string, not an f-string but this was the only way I could find to set the category
        query = (
        f"UNWIND $properties AS props "
        f'CALL {{'
        f'    WITH props '
        f'    CREATE (n: {category.name}) '
        f'    SET n = properties(props) '
        f'}} IN TRANSACTIONS'
        )

        # Execute the query
        self._session.run(
            query,                      # type: ignore  # Ignoring because it wants a literal string not an f-string
            properties = properties
        )

    def write_relation(self, relationship: Relationship, batch_size=1000):
        """ Write a relationship to Neo4j

        Args:
            relation_handle (RelationshipHandle): The relationship to write
            batch_size (int, optional): A number of nodes to write the connection for at once. Defaults to 1000.
        """
        category1 = relationship.category_1
        category2 = relationship.category_2

        # Create the links between categories
        links = relationship.get_links();

        # Create the where clauses for the query
        where_1 = f"WHERE n1.{category1.data.primary_key} = row[0]"
        where_2 = f"WHERE n2.{category2.data.primary_key} = row[1]"

        # Create the query
        # Should be a literal string, not an f-string but this was the only way I could find to set the category
        query = (
        f'UNWIND $data AS row '
        f'CALL {{ '
        f'    WITH row '
        f'    MATCH (n1: {category1.name}) {where_1} '
        f'    WITH row, n1 '
        f'    MATCH (n2: {category2.name}) {where_2} '
        f'    CREATE (n1)-[r:{relationship.name}]->(n2) '
        f'    SET r = properties(row[2]) '
        f'}} IN TRANSACTIONS'
        )

        # Run the query for each batch
        for batch in range(0, len(links), batch_size):
            sub_link_values = links[batch:batch + batch_size]
            # print(sub_link_values[0])
            
            try:
                self._session.run(
                    query, # type: ignore
                    data = sub_link_values
                )
            except:
                print("Could not run write relation.")
                exit(-1)
            
            # Update the progress information
            print(f"\rWriting {relationship.name} {((batch + len(sub_link_values)) / len(links)):.0%}" + (" " * 10), end='')
        print(f"\rWriting {relationship.name} 100%" + (" " * 10))
        
        
    def clear_category(self, category: Category):
        """ Delete all nodes in a category from the Neo4j database
        
        Any relationships connected to the nodes are also deleted

        Args:
            category (Category): The category to clear
        """
        self._session.run(
            (
                f'Match(n: {category.name})'
                 'CALL {'
                 '   WITH n'
                 '   DETACH DELETE n'
                 '} IN TRANSACTIONS'
            ) # type: ignore
        )
        
    def write_relationship_count(self, category: Category, relation: Relationship, property_name: str):
        """ Add a property to nodes in [category] which contains the number of [relation]s that node has

        Args:
            category (Category): The category to create the property for
            relation (Relationship): The relationship to count
            property_name (str): The name of the property to create
        """
        
        self._session.run((
            f'MATCH (n:{category.name})',
             'CALL {'
             '  WITH n'
            f'  MATCH (n)-[r:{relation.name}]-()'
             '  RETURN count(r) as r_count'
             '}'
            f'SET j.{property_name} = r_count'
        )) # type: ignore
        
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