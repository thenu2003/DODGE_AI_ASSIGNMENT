import networkx as nx
import os
import pickle
from graph_builder import GraphBuilder

GRAPH_CACHE = r"d:\train\backend\graph.pkl"

class GraphService:
    def __init__(self, rebuild=False):
        if rebuild or not os.path.exists(GRAPH_CACHE):
            self.G = GraphBuilder().build()
            with open(GRAPH_CACHE, 'wb') as f:
                pickle.dump(self.G, f)
        else:
            with open(GRAPH_CACHE, 'rb') as f:
                self.G = pickle.load(f)

    def get_node(self, node_id):
        if self.G.has_node(node_id):
            return {"id": node_id, "data": self.G.nodes[node_id]}
        return None

    def get_neighbors(self, node_id, direction="out"):
        if not self.G.has_node(node_id): return []
        if direction == "out":
            return [{"source": node_id, "target": v, "type": d['relationship_type']} for u, v, d in self.G.out_edges(node_id, data=True)]
        else:
            return [{"source": u, "target": node_id, "type": d['relationship_type']} for u, v, d in self.G.in_edges(node_id, data=True)]

    def trace_path(self, start_node, end_node):
        try:
            path = nx.shortest_path(self.G, start_node, end_node)
            return path
        except:
            return []

    def get_stats(self):
        types = {}
        for n, d in self.G.nodes(data=True):
            nt = d.get('node_type', 'Unknown')
            types[nt] = types.get(nt, 0) + 1
        
        edges = {}
        for u, v, d in self.G.edges(data=True):
            et = d.get('relationship_type', 'Unknown')
            edges[et] = edges.get(et, 0) + 1

        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "node_types": types,
            "edge_types": edges
        }

if __name__ == "__main__":
    service = GraphService(rebuild=True)
    stats = service.get_stats()
    print("--- GRAPH STATISTICS ---")
    print(f"Total Nodes: {stats['total_nodes']}")
    print(f"Total Edges: {stats['total_edges']}")
    print("\nNode Distribution:")
    for t, c in stats['node_types'].items():
        print(f"  {t}: {c}")
    print("\nEdge Distribution:")
    for t, c in stats['edge_types'].items():
        print(f"  {t}: {c}")

    # Trace Sample Path (e.g., from a SalesOrder to its items)
    sample_so = list(node for node, data in service.G.nodes(data=True) if data.get('node_type') == 'SalesOrder')[0]
    items = service.get_neighbors(sample_so)
    print(f"\nExample Traversal for {sample_so}:")
    for item in items:
        print(f"  -> {item['type']} -> {item['target']}")
