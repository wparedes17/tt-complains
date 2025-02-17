import pandas as pd
from typing import Any, List
from db.populator import Populator
from models.driver_models import Trip
from driver.driver_life import DriverLife

class TopicPopulator(Populator):
    def create_record_list(self) -> list:
        return [
            self.table(topic_name='Finance'),
            self.table(topic_name='Operations'),
            self.table(topic_name='HR'),
        ]
