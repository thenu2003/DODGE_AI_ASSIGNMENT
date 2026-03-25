import sqlite3
from typing import Any, Dict, List
from pathlib import Path

import networkx as nx

from chat_models import QueryPlan
from graph_service import GraphService

DB_PATH = str(Path(__file__).resolve().parent / "database.db")


class QueryExecutor:
    def __init__(self, db_path: str = DB_PATH, graph_service: GraphService | None = None):
        self.db_path = db_path
        self.graph_service = graph_service or GraphService()

    def _validate_sql_step(self, sql: str) -> None:
        stripped = sql.strip().lower()
        if not stripped.startswith("select "):
            raise ValueError("Only SELECT queries are allowed in query plans")
        forbidden = [" insert ", " update ", " delete ", " drop ", " alter ", " pragma ", ";"]
        for token in forbidden:
            if token in f" {stripped} ":
                raise ValueError("Unsafe SQL detected in query plan")

    def _run_sql(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        self._validate_sql_step(sql)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def _trace_flow(self, document_id: str) -> Dict[str, Any]:
        if not self.graph_service.G.has_node(document_id):
            # Try common fallback prefixes when user gives raw numeric ID
            for pref in ("BILL_", "DEL_", "SO_", "CUSTOMER_", "PRODUCT_"):
                node = f"{pref}{document_id}"
                if self.graph_service.G.has_node(node):
                    document_id = node
                    break

        if not self.graph_service.G.has_node(document_id):
            return {"nodes": [], "edges": [], "highlight_nodes": []}

        descendants = list(nx.descendants(self.graph_service.G, document_id))
        ancestors = list(nx.ancestors(self.graph_service.G, document_id))
        all_nodes = list(set([document_id] + descendants + ancestors))
        subgraph = self.graph_service.G.subgraph(all_nodes)

        nodes = [{"id": n, "type": subgraph.nodes[n].get("node_type")} for n in subgraph.nodes()]
        edges = [
            {"source": u, "target": v, "type": d.get("relationship_type")}
            for u, v, d in subgraph.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges, "highlight_nodes": all_nodes}

    def execute_plan(self, plan: QueryPlan) -> Dict[str, Any]:
        if not plan.steps:
            raise ValueError("Query plan contains no steps")

        output: Dict[str, Any] = {"steps": [], "records": [], "highlight_nodes": []}
        for step in plan.steps:
            if step.kind == "sql":
                if not step.sql:
                    raise ValueError(f"SQL step '{step.name}' missing sql")
                rows = self._run_sql(step.sql, step.params)
                output["steps"].append({"step": step.name, "row_count": len(rows)})
                output["records"] = rows

                # Build graph highlights where relevant
                if plan.intent == "aggregation":
                    output["highlight_nodes"] = [f"PRODUCT_{r['product']}" for r in rows if r.get("product")]
                elif plan.intent == "broken_flow":
                    output["highlight_nodes"] = [f"SO_{r['sales_order']}" for r in rows if r.get("sales_order")]
                elif plan.intent == "entity_lookup" and rows:
                    et = plan.entities.get("entity_type")
                    eid = str(plan.entities.get("entity_id", ""))
                    prefix = {
                        "sales_order": "SO_",
                        "delivery": "DEL_",
                        "billing_document": "BILL_",
                        "customer": "CUSTOMER_",
                        "product": "PRODUCT_",
                    }.get(et, "SO_")
                    output["highlight_nodes"] = [f"{prefix}{eid}"]

            elif step.kind == "graph":
                if step.graph_action != "trace_flow":
                    raise ValueError(f"Unsupported graph action: {step.graph_action}")
                trace_result = self._trace_flow(str(plan.entities.get("document_id", "")))
                output["steps"].append({"step": step.name, "node_count": len(trace_result["nodes"])})
                output["records"] = trace_result
                output["highlight_nodes"] = trace_result.get("highlight_nodes", [])
            else:
                raise ValueError(f"Unsupported step kind: {step.kind}")

        return output
