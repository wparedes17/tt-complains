import pandas as pd
from typing import Any, List
from db.populator import Populator
from models.driver_models import Trip
from driver.driver_life import DriverLife

class ComplainPopulator(Populator):
    def create_record_complain(self, trip: Trip, driver_id: int) -> Any:
        if len(trip.complain) == 0:
            return None

        record = self.table(
            driver_id=driver_id,
            route_id=trip.route_id,
            connection_id=1,
            topic_id=1,
            datetime=trip.completion_datetime,
            comment=trip.complain,
            severity=1
        )

        return record

    def create_record_list(self, driver_list: List[DriverLife]) -> list:
        records = []
        for driver in driver_list:
            if not driver.trips:
                raise ValueError("Trip list cannot be empty or list is empty")
            records.extend([self.create_record_complain(trip, driver.driver_id) for trip in driver.trips])

        return records