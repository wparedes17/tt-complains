import random
from typing import Any, List
from collections import Counter
from db.populator import Populator
from driver.driver_life import DriverLife

class DriverPopulator(Populator):
    def create_record_drive(self, driver: DriverLife) -> Any:
        if not driver.trips:
            raise ValueError("Trip list cannot be empty")

        route_counts = Counter(trip.route_id for trip in driver.trips)
        most_common_route = route_counts.most_common(1)[0][0] if route_counts else None

        # Calculate complaint statistics
        complains = [trip for trip in driver.trips if trip.has_complain]
        complaint_topics = Counter(trip.complain for trip in complains)
        most_common_topic = complaint_topics.most_common(1)[0][0] if complaint_topics else None

        # Calculate status
        status = 'quit' if driver.has_quit else 'active'

        adjusted_salary = 0.0

        # Randomly assign sex (this could be modified based on your requirements)
        sex = random.choice(['M', 'F'])

        record = self.table(
            driver_id=driver.driver_id,
            age=driver.age,
            sex=sex,
            location_id=driver.location_id,
            route_list=','.join([str(i+1) for i in driver.assigned_routes]),
            number_routes=len(driver.assigned_routes),
            trip_list=','.join([str(trip.route_id) for trip in driver.trips]),
            number_trips=len(driver.trips),
            number_complains=len(complains),
            most_common_complain_topic=1,
            most_common_route=most_common_route,
            status=status,
            salary=adjusted_salary,
            experience=driver.experience
        )

        return record

    def create_record_list(self, driver_list: List[DriverLife]) -> list:
        return [self.create_record_drive(drive) for drive in driver_list]