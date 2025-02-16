from faker import Faker
from typing import List, Optional
from models.db_models import Node
from db.db_manager import MySQLManager
from logger.logger import logger

class NodePopulator:
    def __init__(self, db_manager: MySQLManager, seed: Optional[int] = None):
        """
        Initialize NodePopulator with database manager and optional seed

        Args:
            db_manager: Database manager instance
            seed: Optional seed for reproducibility
        """
        self.db_manager = db_manager
        self.faker = Faker(['en_US', 'es_ES'])
        if seed is not None:
            Faker.seed(seed)

    def generate_unique_cities(self, count: int) -> List[str]:
        """
        Generate a list of unique city names

        Args:
            count: Number of cities to generate

        Returns:
            List of unique city names
        """
        cities = set()
        max_attempts = count * 2  # Maximum attempts to avoid infinite loop
        attempts = 0

        while len(cities) < count and attempts < max_attempts:
            cities.add(self.faker.city())
            attempts += 1

        return list(cities)

    def populate_nodes(self, count: int) -> bool:
        """
        Populate the nodes table with fake city names

        Args:
            count: Number of nodes to create

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cities = self.generate_unique_cities(count)
            with self.db_manager.session_scope() as session:
                nodes = [
                    Node(name=city)
                    for city in cities
                ]

                session.add_all(nodes)
                logger.info(f"Successfully added {len(nodes)} nodes to the database")
                return True

        except Exception as e:
            logger.error(f"Error populating nodes: {str(e)}")
            return False

    def get_all_nodes(self) -> List[Node]:
        """
        Get all nodes from the database

        Returns:
            List of Node objects
        """
        with self.db_manager.session_scope() as session:
            return session.query(Node).all()