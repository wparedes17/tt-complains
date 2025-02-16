from db.node_population import NodePopulator

def init_populator(db_manager, num_nodes: int = 32):
    node_data = NodePopulator(db_manager=db_manager)
    node_data.populate_nodes(count=num_nodes)