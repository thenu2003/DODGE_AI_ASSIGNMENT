from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import networkx as nx
from graph_service import GraphService
from dotenv import load_dotenv
from chat_models import ChatQueryRequest, ChatQueryResponse
from query_executor import QueryExecutor
from chat_controller import ChatQueryController

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="SAP O2C Graph API", description="Graph-based API for SAP Order-to-Cash data exploration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load graph service as a global singleton
graph_service = GraphService()
chat_controller = ChatQueryController(QueryExecutor(graph_service=graph_service))

class NodeModel(BaseModel):
    id: str
    type: str
    metadata: Dict[str, Any]

class EdgeModel(BaseModel):
    source: str
    target: str
    relationship: str

class GraphResponse(BaseModel):
    nodes: List[NodeModel]
    edges: List[EdgeModel]


ABSTRACT_FLOW_NODES = [
    ("Customer", "Customer"),
    ("SalesOrder", "SalesOrder"),
    ("Delivery", "Delivery"),
    ("BillingDocument", "BillingDocument"),
    ("Payment", "Payment"),
]


def _major_flow_graph() -> GraphResponse:
    nodes = [NodeModel(id=node_id, type=node_type, metadata={"is_abstract": True}) for node_id, node_type in ABSTRACT_FLOW_NODES]
    edges = [
        EdgeModel(source="Customer", target="SalesOrder", relationship="PLACED"),
        EdgeModel(source="SalesOrder", target="Delivery", relationship="FULFILLED_BY"),
        EdgeModel(source="Delivery", target="BillingDocument", relationship="BILLED_AS"),
        EdgeModel(source="BillingDocument", target="Payment", relationship="SETTLED_BY"),
    ]
    return GraphResponse(nodes=nodes, edges=edges)

@app.get("/graph", response_model=GraphResponse)
def get_full_graph():
    """Returns the complete graph structure for visualization."""
    nodes = []
    for n_id, data in graph_service.G.nodes(data=True):
        nodes.append(NodeModel(id=n_id, type=data.get("node_type", "Unknown"), metadata=data))
    
    edges = []
    for u, v, data in graph_service.G.edges(data=True):
        edges.append(EdgeModel(source=u, target=v, relationship=data.get("relationship_type", "Unknown")))
    
    return GraphResponse(nodes=nodes, edges=edges)

@app.get("/graph/summary", response_model=GraphResponse)
def get_summary_graph(limit: int = 100):
    """Returns a lightweight summary graph focusing on header-level entities."""
    core_types = ["Customer", "SalesOrder", "Delivery", "BillingDocument", "Payment"]
    
    nodes = []
    node_ids = set()
    
    # Prioritize core types
    for n_id, data in graph_service.G.nodes(data=True):
        if data.get("node_type") in core_types:
            nodes.append(NodeModel(id=n_id, type=data.get("node_type"), metadata=data))
            node_ids.add(n_id)
            if len(nodes) >= limit:
                break
    
    # If we have space, add a few more or just stop
    edges = []
    for u, v, data in graph_service.G.edges(data=True):
        if u in node_ids and v in node_ids:
            edges.append(EdgeModel(source=u, target=v, relationship=data.get("relationship_type", "Unknown")))
            
    return GraphResponse(nodes=nodes, edges=edges)


@app.get("/graph/business-flow", response_model=GraphResponse)
def get_business_flow_graph():
    """Returns only high-level O2C business entities for first render."""
    return _major_flow_graph()


@app.get("/graph/expand/{node_id}", response_model=GraphResponse)
def expand_business_node(node_id: str, limit: int = 20):
    """
    Expand abstract business nodes to concrete graph instances.
    For real node IDs, falls back to neighborhood expansion.
    """
    abstract_to_type = {
        "Customer": "Customer",
        "SalesOrder": "SalesOrder",
        "Delivery": "Delivery",
        "BillingDocument": "BillingDocument",
        "Payment": "Payment",
    }

    if node_id in abstract_to_type:
        target_type = abstract_to_type[node_id]
        selected_ids = []
        nodes = [NodeModel(id=node_id, type=target_type, metadata={"is_abstract": True})]
        for n_id, data in graph_service.G.nodes(data=True):
            if data.get("node_type") == target_type:
                selected_ids.append(n_id)
                nodes.append(NodeModel(id=n_id, type=target_type, metadata=data))
                if len(selected_ids) >= max(1, min(limit, 100)):
                    break

        edges = [EdgeModel(source=node_id, target=real_id, relationship="INSTANCE_OF") for real_id in selected_ids]
        return GraphResponse(nodes=nodes, edges=edges)

    if not graph_service.G.has_node(node_id):
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    nodes = []
    edges = []
    seen_nodes = {node_id}
    data = graph_service.G.nodes[node_id]
    nodes.append(NodeModel(id=node_id, type=data.get("node_type", "Unknown"), metadata=data))

    for u, v, d in graph_service.G.out_edges(node_id, data=True):
        if len(nodes) >= limit + 1:
            break
        if v not in seen_nodes:
            neighbor_data = graph_service.G.nodes[v]
            nodes.append(NodeModel(id=v, type=neighbor_data.get("node_type", "Unknown"), metadata=neighbor_data))
            seen_nodes.add(v)
        edges.append(EdgeModel(source=u, target=v, relationship=d.get("relationship_type", "Unknown")))

    for u, v, d in graph_service.G.in_edges(node_id, data=True):
        if len(nodes) >= (2 * limit) + 1:
            break
        if u not in seen_nodes:
            neighbor_data = graph_service.G.nodes[u]
            nodes.append(NodeModel(id=u, type=neighbor_data.get("node_type", "Unknown"), metadata=neighbor_data))
            seen_nodes.add(u)
        edges.append(EdgeModel(source=u, target=v, relationship=d.get("relationship_type", "Unknown")))

    return GraphResponse(nodes=nodes, edges=edges)

@app.get("/node/{node_id}")
def get_node_details(node_id: str):
    """Returns detailed information about a specific node including its immediate neighbors."""
    node = graph_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    incoming = graph_service.get_neighbors(node_id, direction="in")
    outgoing = graph_service.get_neighbors(node_id, direction="out")
    
    return {
        "node": node,
        "incoming": incoming,
        "outgoing": outgoing
    }

@app.get("/node/{node_id}/neighbors", response_model=GraphResponse)
def get_node_neighbors(node_id: str):
    """Fetches immediate neighbors for a node to support on-demand expansion."""
    if not graph_service.G.has_node(node_id):
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        
    nodes = []
    edges = []
    seen_nodes = {node_id}
    
    # Add source node
    data = graph_service.G.nodes[node_id]
    nodes.append(NodeModel(id=node_id, type=data.get("node_type", "Unknown"), metadata=data))
    
    # Add outgoing
    for u, v, d in graph_service.G.out_edges(node_id, data=True):
        if v not in seen_nodes:
            neighbor_data = graph_service.G.nodes[v]
            nodes.append(NodeModel(id=v, type=neighbor_data.get("node_type", "Unknown"), metadata=neighbor_data))
            seen_nodes.add(v)
        edges.append(EdgeModel(source=u, target=v, relationship=d.get("relationship_type", "Unknown")))
            
    # Add incoming
    for u, v, d in graph_service.G.in_edges(node_id, data=True):
        if u not in seen_nodes:
            neighbor_data = graph_service.G.nodes[u]
            nodes.append(NodeModel(id=u, type=neighbor_data.get("node_type", "Unknown"), metadata=neighbor_data))
            seen_nodes.add(u)
        edges.append(EdgeModel(source=u, target=v, relationship=d.get("relationship_type", "Unknown")))
        
    return GraphResponse(nodes=nodes, edges=edges)

@app.get("/trace/{document_id}")
def trace_business_flow(document_id: str):
    """
    Traces the business flow starting from a document ID.
    Supports SO_*, DEL_*, BILL_*, CUSTOMER_*.
    """
    if not graph_service.G.has_node(document_id):
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found in graph")

    # Perform a descendant search to find the full flow
    # We use BFS to build a subgraph of the flow
    nodes = list(nx.descendants(graph_service.G, document_id)) + [document_id]
    subgraph = graph_service.G.subgraph(nodes)
    
    # Also look at ancestors if it's a late-stage document (like Billing or Payment) 
    # to provide context (e.g. tracing back to the SO)
    ancestors = list(nx.ancestors(graph_service.G, document_id))
    all_nodes = list(set(nodes) | set(ancestors))
    subgraph = graph_service.G.subgraph(all_nodes)

    # Format result as a sequence/path representation
    flow_nodes = []
    for n_id in all_nodes:
        data = subgraph.nodes[n_id]
        flow_nodes.append({"id": n_id, "type": data.get("node_type")})
        
    flow_edges = []
    for u, v, data in subgraph.edges(data=True):
        flow_edges.append({"source": u, "target": v, "type": data.get("relationship_type")})

    return {
        "start_node": document_id,
        "nodes": flow_nodes,
        "edges": flow_edges
    }

@app.get("/health")
def health_check():
    stats = graph_service.get_stats()
    return {"status": "healthy", "graph_stats": stats}


@app.post("/chat/query", response_model=ChatQueryResponse)
def chat_query(request: ChatQueryRequest):
    """
    Grounded chat-query endpoint:
    question -> guardrails -> intent -> query plan -> execution -> formatted response.
    """
    return chat_controller.handle_query(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
