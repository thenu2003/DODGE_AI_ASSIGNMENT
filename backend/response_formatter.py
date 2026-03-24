from typing import Any, Dict

from chat_models import QueryPlan


def format_answer_text(plan: QueryPlan, exec_result: Dict[str, Any]) -> str:
    records = exec_result.get("records")
    if plan.intent == "aggregation":
        if not records:
            return "No matching product-to-billing associations were found."
        top = records[0]
        return (
            f"Top product by billing-document count is {top.get('product')} "
            f"with {top.get('billing_doc_count')} billing documents."
        )

    if plan.intent == "trace_flow":
        nodes = records.get("nodes", []) if isinstance(records, dict) else []
        edges = records.get("edges", []) if isinstance(records, dict) else []
        if not nodes:
            return "No traceable flow found for the requested document."
        return f"Found a connected flow with {len(nodes)} nodes and {len(edges)} edges."

    if plan.intent == "broken_flow":
        count = len(records or [])
        if count == 0:
            return "No delivered-but-not-billed sales orders were found."
        return f"Found {count} sales orders that appear delivered but not billed."

    if plan.intent == "entity_lookup":
        if not records:
            return "No entity record found for the requested identifier."
        return "Entity details found."

    return "Query executed."
