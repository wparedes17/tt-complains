import random
from typing import Any, Set, Tuple
from db.populator import Populator
from models.db_models import HighwayClassification, HighwayCondition, HighwayDifficult
from logger.logger import logger

class SimpleConnectionPopulator(Populator):
    def create_record_connection(self, start_node: int, end_node: int) -> Any:
        record = self.table(
            start_node=start_node+1,
            end_node=end_node+1,
            highway_classification=random.choice(list(HighwayClassification)),
            highway_condition=random.choice(list(HighwayCondition)),
            highway_difficult=random.choice(list(HighwayDifficult)),
            assault_risk=random.uniform(0,1)/10.0
        )

        return record

    def create_record_list(self, connection_list: Set[Tuple[int]]) -> list:
        return [self.create_record_connection(x[0], x[1]) for x in connection_list]