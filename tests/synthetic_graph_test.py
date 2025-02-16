import pytest
import networkx as nx
from graph_city.synthetic_graph import SyntheticGraph, RouteInfo


@pytest.fixture
def graph():
    """Fixture to create a test graph instance."""
    return SyntheticGraph(num_nodes=5, random_seed=42)


def test_init_invalid_nodes():
    """Test initialization with invalid number of nodes."""
    with pytest.raises(ValueError, match="Number of nodes must be at least 2"):
        SyntheticGraph(num_nodes=1)


def test_graph_properties(graph):
    """Test basic graph properties."""
    # Test number of nodes
    assert len(graph.graph.nodes) == 5

    # Test if graph is directed
    assert graph.graph.is_directed()


def test_bidirectional_edges(graph):
    """Test if edges are bidirectional."""
    for u, v in graph.graph.edges():
        assert graph.graph.has_edge(v, u), f"Missing bidirectional edge between {v} and {u}"


def test_edge_weights(graph):
    """Test if edge weights are within expected ranges."""
    for u, v, data in graph.graph.edges(data=True):
        assert 'distance' in data, f"Missing distance for edge {u}->{v}"
        assert 'price' in data, f"Missing price for edge {u}->{v}"
        assert 1 <= data['distance'] <= 20, f"Distance out of range for edge {u}->{v}"
        assert 1 <= data['price'] <= 100, f"Price out of range for edge {u}->{v}"


def test_graph_connectivity(graph):
    """Test if graph is strongly connected."""
    assert nx.is_strongly_connected(graph.graph), "Graph is not strongly connected"


def test_random_route(graph):
    """Test random route generation."""
    route = graph.get_random_route()

    # Test return type
    assert isinstance(route, RouteInfo), "Route should be instance of RouteInfo"

    # Test route properties
    assert route.start in graph.graph.nodes, "Invalid start node"
    assert route.end in graph.graph.nodes, "Invalid end node"
    assert len(route.path) > 0, "Route path should not be empty"
    assert route.total_distance > 0, "Total distance should be positive"
    assert route.total_price > 0, "Total price should be positive"


def test_route_validity(graph):
    """Test if generated route is valid."""
    route = graph.get_random_route()

    # Check if path is continuous
    for i in range(len(route.path) - 1):
        current_node, next_node = route.path[i], route.path[i + 1]
        assert graph.graph.has_edge(current_node, next_node), \
            f"Invalid path segment between {current_node} and {next_node}"


@pytest.mark.parametrize("num_nodes,seed", [
    (5, 42),
    (10, 123),
    (32, 999),
])
def test_different_graph_sizes(num_nodes, seed):
    """Test graph creation with different sizes."""
    graph = SyntheticGraph(num_nodes=num_nodes, random_seed=seed)
    assert nx.is_strongly_connected(graph.graph)


def test_route_calculation_correctness(graph):
    """Test if route calculations (distance and price) are correct."""
    route = graph.get_random_route()

    # Manually calculate totals
    calculated_distance = sum(
        graph.graph[u][v]["distance"]
        for u, v in zip(route.path, route.path[1:])
    )
    calculated_price = sum(
        graph.graph[u][v]["price"]
        for u, v in zip(route.path, route.path[1:])
    )

    assert route.total_distance == calculated_distance, "Incorrect distance calculation"
    assert route.total_price == calculated_price, "Incorrect price calculation"


def test_visualization(graph, tmp_path):
    """Test graph visualization method."""
    # Test saving to a file
    save_path = tmp_path / "graph.png"
    graph.visualize(save_path=str(save_path))
    assert save_path.exists(), "Visualization file was not created"


def test_reproducibility():
    """Test if random seed produces consistent results."""
    graph1 = SyntheticGraph(num_nodes=5, random_seed=42)
    graph2 = SyntheticGraph(num_nodes=5, random_seed=42)

    # Compare edge sets
    edges1 = set(graph1.graph.edges())
    edges2 = set(graph2.graph.edges())
    assert edges1 == edges2