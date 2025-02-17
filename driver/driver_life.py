import random
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Set, Tuple
from driver.risk_score import calculate_trouble_score

@dataclass
class Trip:
    route_id: int
    start_datetime: datetime
    completion_datetime: datetime
    on_time: bool
    min_completion_time: float
    assaulted: bool = False


@dataclass
class DriverLife:
    def __init__(self,
                 number_locations: int,
                 route_data: dict = None,
                 connection_df: pd.DataFrame = None,
                 start_date: datetime = datetime(2024, 1, 1),
                 mean_trips: float = 75,
                 sd_trips: float = 25,
                 mean_exp: float = 7.5,
                 sd_exp: float = 2,
                 min_routes: int = 3,
                 max_routes: int = 10,
                 total_routes: int = 50,
                 rate_hours: float = 1 / 48):
        """
        Initialize a driver with their characteristics and simulate their trips

        Args:
            location_id: Node ID where driver is based
            start_date: Beginning of simulation period
            mean_trips: Mean number of trips per year
            sd_trips: Standard deviation of trips per year
            mean_exp: Mean years of experience
            sd_exp: Standard deviation of years of experience
            min_routes: Minimum number of routes assigned to driver
            max_routes: Maximum number of routes assigned to driver
            total_routes: Total number of routes available
            rate_hours: Rate parameter for exponential distribution of inter-trip times
        """
        self.location_id = np.random.randint(1, number_locations + 1)
        self.start_date = start_date

        # Generate driver's characteristics
        self.experience = int(max(0.0, np.random.normal(mean_exp, sd_exp)))
        self.number_trips = int(max(1.0, np.random.normal(mean_trips, sd_trips)))

        # Assign random routes to driver
        num_routes = np.random.randint(min_routes, max_routes + 1)
        self.assigned_routes: Set[int] = set(np.random.choice(total_routes,
                                                              size=num_routes,
                                                              replace=False))

        # Simulate trips
        self.trips: List[Trip] = self._simulate_trips(rate_hours, route_data, connection_df)

        # Calculate derived statistics
        self._calculate_statistics()

    @staticmethod
    def get_connections(path_string) -> List[Tuple[int, int]]:
        """Get list of node connections in route."""
        nodes = [int(x) for x in path_string.split(',')]
        return list(zip(nodes[:-1], nodes[1:]))

    def _simulate_trouble(self, path_string: str, connection_df: pd.DataFrame, node_df: pd.DataFrame) -> float:
        """
        Simulate trouble possibility for each connection in route.

        Args:
            path_string: String with path trip
            connection_df: DataFrame with assault risk for each connection
            node_df: DataFrame with node difficulty

        Returns:
            float: Trouble score
        """
        trouble_score = 0.0

        for start, end in self.get_connections(path_string=path_string):
            connection = connection_df[
                (connection_df['start_node'] == start) & (connection_df['end_node'] == end)
            ]
            node_start = node_df[node_df['node_id'] == start]
            node_end = node_df[node_df['node_id'] == end]

            if not connection.empty:
                trouble_score += calculate_trouble_score(
                    connection=connection,
                    node_start=node_start,
                    node_end=node_end
                )

        return trouble_score

    def _simulate_assault(self, path_string: str, connection_df: pd.DataFrame) -> Tuple[
        bool, float]:
        """
        Simulate assault possibility for each connection in route.

        Args:
            path_string: String with path trip
            connection_df: DataFrame with assault risk for each connection

        Returns:
            Tuple of (was_assaulted, connection_status, completion_time_reduction)
        """
        was_assaulted = False

        for start, end in self.get_connections(path_string=path_string):
            assault_risk = float(connection_df[(connection_df['start_node'] == 16) & (connection_df['end_node'] == 29)]['assault_risk'].iloc[0])
            is_connection_assaulted = random.random() < assault_risk
            was_assaulted = was_assaulted or is_connection_assaulted

        # If assaulted, generate random completion time reduction
        completion_time_reduction = random.uniform(0.05, 0.20) if was_assaulted else 0.0

        return was_assaulted, completion_time_reduction

    def _simulate_trips(self, rate_hours: float, route_data: dict, connection_df: pd.DataFrame) -> List[Trip]:
        """Simulate all trips for the driver over the year."""
        trips = []
        current_time = self.start_date + timedelta(hours=np.random.exponential(1 / rate_hours))

        for _ in range(self.number_trips):
            # Select random route from driver's assigned routes
            route_id = int(np.random.choice(list(self.assigned_routes)) + 1)

            # Get minimum completion time for this route (this should come from route data)
            min_completion_time = route_data[route_id]['min_completion_time']
            max_completion_time = route_data[route_id]['max_completion_time']

            # Generate completion time using Weibull distribution
            completion_noise = np.random.normal(0.95, 0.1)
            completion_hours = np.random.uniform(min_completion_time, max_completion_time)*completion_noise

            completion_time = current_time + timedelta(hours=completion_hours)
            was_assaulted, completion_time_reduction = self._simulate_assault(
                path_string=route_data[route_id]['intermediate_nodes'],
                connection_df=connection_df)

            if was_assaulted:
                completion_time = completion_time - timedelta(hours=completion_hours * completion_time_reduction)

            on_time = (completion_hours <= max_completion_time) and (not was_assaulted)

            # Create and store trip
            trips.append(Trip(
                route_id=route_id,
                start_datetime=current_time,
                completion_datetime=completion_time,
                on_time=on_time,
                min_completion_time=min_completion_time,
                assaulted=was_assaulted
            ))

            # Calculate next trip start time
            inter_trip_hours = np.random.exponential(1 / rate_hours)
            current_time = completion_time + timedelta(hours=inter_trip_hours)

        return trips

    def _calculate_statistics(self):
        """Calculate derived statistics from trips."""
        self.number_routes = len(self.assigned_routes)
        self.number_trips = len(self.trips)

        if self.trips:
            route_counts = {}
            for trip in self.trips:
                route_counts[trip.route_id + 1] = route_counts.get(trip.route_id + 1, 0) + 1
            self.most_common_route = max(route_counts.items(), key=lambda x: x[1])[0]