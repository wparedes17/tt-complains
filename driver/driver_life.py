import random
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Set, Tuple
from driver.risk_score import calculate_trouble_score
from driver.driver_prompts import PromptGenerator, driver_context
from models.driver_models import DriverProfile, Trip
from open_ai.open_ai_handler import OpenAIHandler

prompter = PromptGenerator()
gpt_chat = OpenAIHandler()

@dataclass
class DriverLife:
    def __init__(self,
                 driver_id: int,
                 number_locations: int,
                 route_data: dict = None,
                 node_df: pd.DataFrame = None,
                 connection_df: pd.DataFrame = None,
                 start_date: datetime = datetime(2024, 1, 1),
                 mean_trips: float = 150,
                 sd_trips: float = 20,
                 mean_exp: float = 7.5,
                 sd_exp: float = 2,
                 min_routes: int = 3,
                 max_routes: int = 10,
                 total_routes: int = 50,
                 rate_hours: float = 1 / 48,
                 complain_threshold: float = 0.7,
                 quit_threshold: float = 1.6,
                 stress_decay: float = 0.3
                 ):
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
        self.driver_id = driver_id
        self.stress_score = 0.0
        self.has_quit = False
        self.complain_threshold = complain_threshold
        self.quit_threshold = quit_threshold
        self.stress_decay = stress_decay
        self.location_id = np.random.randint(1, number_locations + 1)
        self.start_date = start_date

        # Generate driver's characteristics
        self.age = int(max(30.0, np.random.normal(40, 3)))
        self.experience = int(max(0.0, np.random.normal(mean_exp, sd_exp)))
        self.number_trips = int(max(1.0, np.random.normal(mean_trips, sd_trips)))

        # Assign random routes to driver
        num_routes = np.random.randint(min_routes, max_routes + 1)
        self.assigned_routes: Set[int] = set(np.random.choice(total_routes,
                                                              size=num_routes,
                                                              replace=False))

        # Simulate trips
        self.trips: List[Trip] = self._simulate_trips(rate_hours, route_data, connection_df, node_df)

        # Calculate derived statistics
        self._calculate_statistics()

    @staticmethod
    def get_connections(path_string) -> List[Tuple[int, int]]:
        """Get list of node connections in route."""
        nodes = [int(x) for x in path_string.split(',')]
        return list(zip(nodes[:-1], nodes[1:]))

    @staticmethod
    def _calculate_stress_impact(trouble_score: float) -> float:
        """
        Calculate stress impact based on trouble score using fuzzy logic.

        Args:
            trouble_score: Current trip's trouble score

        Returns:
            Float representing stress impact
        """
        if trouble_score < 0.01:
            return 0.0
        elif trouble_score <= 0.7:
            return trouble_score
        else:
            return 0.7 * 1.2

    def _update_stress_score(self, trouble_score: float) -> Tuple[bool, bool]:
        """
        Update driver's stress score and determine if they complain or quit.

        Args:
            trouble_score: Current trip's trouble score

        Returns:
            Tuple of (has_complain, has_quit)
        """
        # Apply decay to current stress
        self.stress_score *= (1 - self.stress_decay)

        # Add new stress from trouble
        stress_impact = self._calculate_stress_impact(trouble_score)
        self.stress_score = self.stress_score + stress_impact

        # Check for complain and quit conditions
        has_complain = (self.stress_score >= self.complain_threshold)
        has_quit = self.stress_score >= self.quit_threshold
        if has_quit:
            self.has_quit = True

        return has_complain, has_quit

    def _simulate_trouble(
            self,
            path_string: str,
            path_distance: float,
            end_node: int,
            time_ok: bool,
            assaulted: bool,
            connection_df: pd.DataFrame,
            node_df: pd.DataFrame
    ) -> float:
        """
        Simulate trouble possibility for each connection in route.

        Args:
            path_string: String with path trip
            connection_df: DataFrame with assault risk for each connection
            node_df: DataFrame with node difficulty

        Returns:
            float: Trouble score
        """

        # if the driver is assaulted, the trouble score is 1
        if assaulted:
            return 1.0

        # in other case, the trouble score is calculated based on the connections
        trouble_score = 0.0
        omit_unloading = True
        path_connections = self.get_connections(path_string=path_string)
        for start, end in path_connections:
            connection_row = connection_df[(connection_df['start_node'] == start) & (connection_df['end_node'] == end)]
            highway_classification = connection_row['highway_classification'].iloc[0]
            highway_condition = connection_row['highway_condition'].iloc[0]
            highway_difficulty = connection_row['highway_difficult'].iloc[0]
            unloading_difficulty = node_df[node_df['node_id'] == end]['node_difficult'].iloc[0]
            if end == end_node:
                omit_unloading = False

            trouble_score += calculate_trouble_score(
                highway_class=highway_classification,
                highway_condition=highway_condition,
                highway_difficulty=highway_difficulty,
                unloading_difficulty=unloading_difficulty,
                driver_experience=self.experience,
                distance=path_distance,
                omit_unloading=omit_unloading
            )

        on_time_factor = 0.8 if time_ok else 1.0

        return trouble_score*on_time_factor

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
            assault_risk = float(connection_df[(connection_df['start_node'] == start) & (connection_df['end_node'] == end)]['assault_risk'].iloc[0])
            is_connection_assaulted = random.random() < assault_risk
            was_assaulted = was_assaulted or is_connection_assaulted

        # If assaulted, generate random completion time reduction
        completion_time_reduction = random.uniform(0.05, 0.20) if was_assaulted else 0.0

        return was_assaulted, completion_time_reduction

    def _simulate_trips(
            self,
            rate_hours: float,
            route_data: dict,
            connection_df: pd.DataFrame,
            node_df: pd.DataFrame
        ) -> List[Trip]:
        """Simulate all trips for the driver over the year."""

        trips = []
        trouble_score = 0.0
        decay_factor = 0.5
        current_time = self.start_date + timedelta(hours=np.random.exponential(1 / rate_hours))

        for _ in range(self.number_trips):
            complain = ''
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
            trouble_score = (0.2*trouble_score*decay_factor + 0.8*self._simulate_trouble(
                path_string=route_data[route_id]['intermediate_nodes'],
                path_distance=route_data[route_id]['distance'],
                end_node=route_data[route_id]['end_node'],
                time_ok=on_time,
                assaulted=was_assaulted,
                connection_df=connection_df,
                node_df=node_df
            ))
            has_complain, has_quit = self._update_stress_score(trouble_score)
            # Create and store trip
            simulated_trip =Trip(
                route_id=route_id,
                start_datetime=current_time,
                completion_datetime=completion_time,
                on_time=on_time,
                min_completion_time=min_completion_time,
                complain=complain,
                assaulted=was_assaulted,
                trouble_score=trouble_score,
                stress_score=self.stress_score,
                has_complain=has_complain,
                driver_quit=has_quit
            )

            if has_complain:
                profile = DriverProfile(id=self.driver_id, age=self.age, years_experience=self.experience)
                prompt = prompter.generate_prompt(
                    trip = simulated_trip,
                    driver = profile
                )
                complain = gpt_chat.chat_complete_with_model(
                    system_role='system',
                    system_content=driver_context,
                    prompt=prompt
                )
                simulated_trip.complain = complain
            trips.append(simulated_trip)
            # Stop simulation if driver has quit
            if has_quit:
                break

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