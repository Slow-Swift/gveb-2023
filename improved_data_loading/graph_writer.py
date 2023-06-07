from neo4j import Session

from category import Category
from relationship import Relationship

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
        compare = "IN" if relationship.has_muliple_links() == list else "="
        where_1 = f"WHERE n1.{category1.data.primary_key} = row[0]"
        where_2 = f"WHERE n2.{category2.data.primary_key} {compare} row[1]"

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
            self._session.run(
                query, # type: ignore
                data = sub_link_values
            )
            
            # Update the progress information
            print(f"\rWriting {relationship.name} {((batch + len(sub_link_values)) / len(links)):.0%}" + (" " * 10), end='')
        print(f"\rWriting {relationship.name} 100%" + (" " * 10))
        
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