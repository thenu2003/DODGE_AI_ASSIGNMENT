import re
from typing import Any, Dict

from chat_models import QueryPlan, QueryStep


def _normalized_doc_id(raw: str, entity_type: str = "") -> str:
    token = raw.strip()
    if token.upper().startswith(("SO_", "DEL_", "BILL_", "CUSTOMER_", "PRODUCT_")):
        return token.upper()
    if entity_type == "sales_order":
        return f"SO_{token}"
    if entity_type == "delivery":
        return f"DEL_{token}"
    if entity_type == "billing_document":
        return f"BILL_{token}"
    if entity_type == "customer":
        return f"CUSTOMER_{token}"
    if entity_type == "product":
        return f"PRODUCT_{token}"
    return token


def build_query_plan(question: str, intent_info: Dict[str, Any], top_k: int = 10) -> QueryPlan:
    intent = intent_info["intent"]
    entities = intent_info.get("entities", {}) or {}

    if intent == "aggregation":
        steps = [
            QueryStep(
                kind="sql",
                name="top_products_by_distinct_billing_docs",
                sql=(
                    "SELECT soi.material AS product, "
                    "COUNT(DISTINCT bi.billingDocument) AS billing_doc_count "
                    "FROM sales_order_items soi "
                    "JOIN outbound_delivery_items di "
                    "  ON CAST(soi.salesOrder AS INTEGER)=CAST(di.referenceSdDocument AS INTEGER) "
                    " AND CAST(soi.salesOrderItem AS INTEGER)=CAST(di.referenceSdDocumentItem AS INTEGER) "
                    "JOIN billing_document_items bi "
                    "  ON CAST(di.deliveryDocument AS INTEGER)=CAST(bi.referenceSdDocument AS INTEGER) "
                    " AND CAST(di.deliveryDocumentItem AS INTEGER)=CAST(bi.referenceSdDocumentItem AS INTEGER) "
                    "GROUP BY soi.material "
                    "ORDER BY billing_doc_count DESC "
                    "LIMIT :top_k"
                ),
                params={"top_k": top_k},
            )
        ]
        return QueryPlan(intent="aggregation", entities=entities, steps=steps, notes="Aggregation over SQL lifecycle joins")

    if intent == "trace_flow":
        doc = entities.get("document_id")
        if not doc:
            match = re.search(r"\b\d{5,}\b", question)
            doc = match.group(0) if match else ""
        doc_prefix = _normalized_doc_id(str(doc), entities.get("entity_type", "billing_document"))
        entities["document_id"] = doc_prefix
        steps = [QueryStep(kind="graph", name="trace_document_flow", graph_action="trace_flow")]
        return QueryPlan(intent="trace_flow", entities=entities, steps=steps, notes="Graph traversal over cached NetworkX graph")

    if intent == "broken_flow":
        steps = [
            QueryStep(
                kind="sql",
                name="sales_orders_delivered_not_billed",
                sql=(
                    "SELECT DISTINCT di.referenceSdDocument AS sales_order "
                    "FROM outbound_delivery_items di "
                    "LEFT JOIN billing_document_items bi "
                    "  ON CAST(di.deliveryDocument AS INTEGER)=CAST(bi.referenceSdDocument AS INTEGER) "
                    " AND CAST(di.deliveryDocumentItem AS INTEGER)=CAST(bi.referenceSdDocumentItem AS INTEGER) "
                    "WHERE di.referenceSdDocument IS NOT NULL "
                    "  AND bi.billingDocument IS NULL "
                    "ORDER BY CAST(di.referenceSdDocument AS INTEGER) "
                    "LIMIT :top_k"
                ),
                params={"top_k": top_k},
            )
        ]
        return QueryPlan(intent="broken_flow", entities=entities, steps=steps, notes="Detect missing downstream billing records")

    # entity_lookup default
    entity_type = entities.get("entity_type", "sales_order")
    entity_id = entities.get("entity_id") or entities.get("document_id")
    if not entity_id:
        match = re.search(r"\b\d{3,}\b", question)
        entity_id = match.group(0) if match else ""
    entities["entity_id"] = str(entity_id)
    entities["entity_type"] = entity_type
    table_by_entity = {
        "sales_order": ("sales_order_headers", "salesOrder"),
        "delivery": ("outbound_delivery_headers", "deliveryDocument"),
        "billing_document": ("billing_document_headers", "billingDocument"),
        "customer": ("business_partners", "businessPartner"),
        "product": ("products", "product"),
    }
    table, key_col = table_by_entity.get(entity_type, ("sales_order_headers", "salesOrder"))
    steps = [
        QueryStep(
            kind="sql",
            name="entity_lookup_header",
            sql=f'SELECT * FROM "{table}" WHERE CAST("{key_col}" AS TEXT)=:entity_id LIMIT 1',
            params={"entity_id": str(entity_id)},
        )
    ]
    return QueryPlan(intent="entity_lookup", entities=entities, steps=steps, notes="Header-level entity lookup")
