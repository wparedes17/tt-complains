from faker import Faker
from typing import List, Optional, Any
from db.db_manager import MySQLManager
from logger.logger import logger
from abc import ABC, abstractmethod

class Populator:
    def __init__(self, db_manager: MySQLManager, table: Any, seed: Optional[int] = None):
        """
        Initialize NodePopulator with database manager and optional seed

        Args:
            db_manager: Database manager instance
            seed: Optional seed for reproducibility
        """
        self.db_manager = db_manager
        self.table = table
        self.faker = Faker(['en_US', 'es_ES'])
        if seed is not None:
            Faker.seed(seed)

    def generate_records_by_number(self, number_records: int):
        if number_records < 0:
            logger.error("Number of records must be at least 1 or list_record should be declared")
            raise ValueError("Number of records must be at least 1 or list_record should be declared")
        return []

    def populate(self, number_records: int = -1, list_records: list = None):
        if (not list_records is None) and (not isinstance(list_records[0], self.table)):
            logger.error("Records are not compatible with stated table")
            raise TypeError("Records are not compatible with stated table")
        if list_records is None:
            list_records = self.generate_records_by_number(number_records=number_records)

        if len(list_records) == 0:
            logger.error("Method has not been implemented yet or list is empty")
            raise ValueError("Method has not been implemented yet or list is empty")

        with self.db_manager.session_scope() as session:
            session.add_all(list_records)
            logger.info(f"Successfully inserted {len(list_records)} records")




