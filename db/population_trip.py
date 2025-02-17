import pandas as pd
from typing import Any, List
from db.populator import Populator
from models.driver_models import Trip
from driver.driver_life import DriverLife

class TripPopulator(Populator):
    def create_record_trip(self, trip: Trip, driver_id: int, route_df: pd.DataFrame) -> Any:
        if not trip.start_datetime:
            raise ValueError("Start datetime is required")

        # Calculate total payment
        payment = self.compute_payment(
            route_id = trip.route_id,
            route_df = route_df
        )

        record = self.table(
            driver_id=driver_id,
            route_id=trip.route_id,
            complete=trip.on_time,
            has_complain=trip.has_complain,
            start_datetime=trip.start_datetime,
            end_datetime=trip.completion_datetime,
            total_payment=payment
        )

        return record

    def create_record_list(self, driver_list: List[DriverLife], route_df: pd.DataFrame) -> list:
        records = []
        for driver in driver_list:
            if not driver.trips:
                raise ValueError("Trip list cannot be empty or list is empty")
            records.extend([self.create_record_trip(trip, driver.driver_id,  route_df) for trip in driver.trips])

        return records

    @staticmethod
    def compute_payment(route_id: int, route_df: pd.DataFrame) -> float:
        return route_df[route_df['route_id'] == route_id]['price'].iloc[0]