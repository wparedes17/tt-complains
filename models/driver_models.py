from datetime import datetime
from dataclasses import dataclass

@dataclass
class Trip:
    route_id: int
    start_datetime: datetime
    completion_datetime: datetime
    on_time: bool
    min_completion_time: float
    complain: str
    assaulted: bool = False
    trouble_score: float = 0.0
    stress_score: float = 0.0
    has_complain: bool = False
    driver_quit: bool = False

@dataclass
class DriverProfile:
    id: int
    age: int
    years_experience: int
