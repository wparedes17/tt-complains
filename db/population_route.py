from typing import Any, List
from db.populator import Populator
from models.route_info import RouteInfo
from models.constants import AVERAGE_SPEED, MINIMUM_SPEED

class RoutePopulator(Populator):
    def create_record_route(self, route: RouteInfo) -> Any:
        record = self.table(
            start_node=route.start + 1,
            end_node=route.end + 1,
            price=route.total_price,
            distance=route.total_distance,
            min_completion_time = route.total_distance/AVERAGE_SPEED,
            max_completion_time = route.total_distance/MINIMUM_SPEED,
            intermediate_nodes = ','.join([str(node+1) for node in route.path]),
        )

        return record

    def create_record_list(self, route_list: List[RouteInfo]) -> list:
        return [self.create_record_route(route) for route in route_list]