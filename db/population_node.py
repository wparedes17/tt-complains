import random
from typing import List
from db.populator import Populator
from models.db_models import UnloadingDifficult
from logger.logger import logger

class NodePopulator(Populator):
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

    def generate_records_by_number(self, number_records: int = 32) -> list:
        """
        Populate the nodes table with fake city names

        Args:
            number_records: Number of nodes to create

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cities = self.generate_unique_cities(number_records)
            nodes = [
                    self.table(
                        name=city,
                        node_difficult=random.choice(list(UnloadingDifficult)))
                    for city in cities
                ]

            return nodes

        except Exception as e:
            logger.error(f"Error generating records: {str(e)}")
            return list()