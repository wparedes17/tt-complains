import random
import networkx as nx
import matplotlib.pyplot as plt

from typing import Optional
from logger.logger import logger
from models.route_info import RouteInfo
from models.constants import KM_PRICE

class SyntheticGraph:
    """
    A class to create and manage a synthetic directed graph with bidirectional connections
    and different weights for each direction.
    """

    def __init__(self, num_nodes: int = 32, random_seed: Optional[int] = None):
        """
        Initialize the synthetic graph.

        Args:
            num_nodes: Number of nodes in the graph (default: 32)
            random_seed: Seed for random number generation (default: None)

        Raises:
            ValueError: If num_nodes is less than 2
        """
        if num_nodes < 2:
            logger.error(f"Graph Error: Number of nodes must be at least 2")
            raise ValueError("Graph Error: Number of nodes must be at least 2")

        self.num_nodes = num_nodes
        self._random_edges = list()
        self._simple_edges = list()
        self.graph = nx.DiGraph()

        if random_seed is not None:
            random.seed(random_seed)

        self._create_graph()

    @property
    def graph_edges(self):
        return set(self._simple_edges + self._random_edges)

    def _create_graph(self) -> None:
        """
            Procedure to create the graph
        """
        nodes = range(self.num_nodes)

        # Create spanning tree
        self._create_spanning_tree(nodes)

        # Add extra random edges
        self._add_random_edges(nodes)

    def _create_spanning_tree(self, nodes: range) -> None:
        """
            Procedure to create initial graph

            Args:
                nodes: Range of numbers of nodes to connect (full range generate a fully connected graph)

            Raises:
                ValueError: When some nodes in range don't belong to the graph. E.g. range(33) for 32 node graph

            Notes:
                - Initial spanning edges.
                - We are assuming country is full connected.
                - Node i is connected to node i+1.

        """
        node_list = [i for i in nodes]
        if max(node_list) >= self.num_nodes:
            logger.error("Graph Error: Node range is out of scope")
            raise ValueError("Graph Error: Node range is out of scope")

        spanning_edges = [(i, (i + 1) % self.num_nodes) for i in node_list]
        for u, v in spanning_edges:
            self._simple_edges.extend([(u,v), (v,u)])
            self._add_bidirectional_edge(u, v)

    def _add_random_edges(self, nodes: range, density_param: int = 2) -> None:
        """
            Procedure to add some random biderectional edges

            Args:
                nodes: Range of numbers of nodes to connect in a random way.
                density_param: Parameter to control density. Higher value involves higher density (default: 2)
        """
        for _ in range(self.num_nodes * density_param):
            u, v = random.sample(list(nodes), 2)
            self._random_edges.extend([(u,v), (v,u)])
            self._add_bidirectional_edge(u, v)

    def _add_bidirectional_edge(self, u: int, v: int) -> None:
        """
        Add a bidirectional edge between two nodes with random weights

        Args:
            u: Source node
            v: Target node
        """
        # Forward edge data
        # Random distance, price is directly proportional to distance
        distance = random.randint(300, 1000)
        price = distance * KM_PRICE

        # Forward edge
        self.graph.add_edge(u, v,
                            distance=distance,
                            price=price)

        # Reverse edge with different data
        # Distance might be different, price also can be different
        self.graph.add_edge(v, u,
                            distance=distance + random.randint(-10, 10),
                            price=price + random.randint(-1, 1))

    def get_random_route(self) -> Optional[RouteInfo]:
        """
        Generate a random route between two nodes using the shortest path.

        Returns:
            RouteInfo object containing route details or None if no route is found
        """
        nodes = list(self.graph.nodes)
        start = random.choice(nodes)

        reachable_nodes = list(nx.descendants(self.graph, start))
        if not reachable_nodes:
            return None

        end = random.choice(reachable_nodes)
        try:
            return self.get_path_info(start, end)
        except nx.NetworkXNoPath:
            return None

    def get_path_info(self, start: int, end: int, weight: str = "distance") -> Optional[RouteInfo]:
        """
        Get information about the shortest path between two nodes.

        Args:
            start: Starting node
            end: Ending node
            weight: Weight to use for shortest path calculation ("distance" or "price")

        Returns:
            RouteInfo object containing path details or None if no path exists

        Raises:
            ValueError: If weight is not "distance" or "price"
            ValueError: If start or end nodes don't exist in graph
        """
        if weight not in ["distance", "price"]:
            raise ValueError('Weight must be either "distance" or "price"')

        if start not in self.graph.nodes or end not in self.graph.nodes:
            raise ValueError("Start and end nodes must exist in the graph")

        try:
            path = nx.shortest_path(self.graph, source=start, target=end, weight=weight)
            total_distance = sum(self.graph[u][v]["distance"] for u, v in zip(path, path[1:]))
            total_price = sum(self.graph[u][v]["price"] for u, v in zip(path, path[1:]))

            return RouteInfo(
                start=start,
                end=end,
                path=path,
                total_distance=total_distance,
                total_price=total_price
            )
        except nx.NetworkXNoPath:
            return None

    def visualize(self, save_path: Optional[str] = None) -> None:
        """
        Visualize the graph using matplotlib.

        Args:
            save_path: Optional path to save the visualization
        """
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph)

        nx.draw_networkx_nodes(self.graph, pos, node_color='lightblue',
                               node_size=500)
        nx.draw_networkx_edges(self.graph, pos, edge_color='gray',
                               arrows=True, arrowsize=20)
        nx.draw_networkx_labels(self.graph, pos)

        if save_path:
            plt.savefig(save_path)
        plt.show()