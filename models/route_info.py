from typing import Optional, List
from dataclasses import dataclass

@dataclass
class RouteInfo:
    start: int
    end: int
    path: List[int]
    total_distance: float
    total_price: float