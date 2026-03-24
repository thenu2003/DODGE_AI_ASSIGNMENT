import sqlite3
import os

DB_PATH = r"d:\train\database.db"

def validate():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tables check
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print("--- TABLES PRESENT ---")
    print(tables)
    print()

    # 2. Row count validation
    print("--- ROW COUNTS ---")
    select_clauses = [f"SELECT '{t}', COUNT(*) FROM '{t}'" for t in tables]
    count_query = " UNION ALL ".join(select_clauses)
    cursor.execute(count_query)
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
    print()

    # 3. Primary Key Uniqueness Check (based on TABLE_SCHEMAS from ingest script)
    # Mapping based on TABLE_SCHEMAS in ingest_data.py
    pk_mapping = {
        "business_partners": "businessPartner",
        "plants": "plant",
        "products": "product",
        "product_descriptions": "product, language",
        "product_plants": "product, plant",
        "product_storage_locations": "product, plant, storageLocation",
        "business_partner_addresses": "businessPartner, addressId",
        "customer_company_assignments": "customer, companyCode",
        "customer_sales_area_assignments": "customer, salesOrganization, distributionChannel, division",
        "sales_order_headers": "salesOrder",
        "sales_order_items": "salesOrder, salesOrderItem",
        "sales_order_schedule_lines": "salesOrder, salesOrderItem, scheduleLine",
        "outbound_delivery_headers": "deliveryDocument",
        "outbound_delivery_items": "deliveryDocument, deliveryDocumentItem",
        "billing_document_headers": "billingDocument",
        "billing_document_cancellations": "billingDocument",
        "billing_document_items": "billingDocument, billingDocumentItem",
        "journal_entry_items_accounts_receivable": "companyCode, fiscalYear, accountingDocument, accountingDocumentItem",
        "payments_accounts_receivable": "companyCode, fiscalYear, accountingDocument, accountingDocumentItem"
    }

    print("--- PK UNIQUENESS CHECK ---")
    for table, pk in pk_mapping.items():
        if table in tables:
            query = f"SELECT {pk}, COUNT(*) FROM \"{table}\" GROUP BY {pk} HAVING COUNT(*) > 1;"
            cursor.execute(query)
            dupes = cursor.fetchall()
            print(f"{table}: {'OK' if not dupes else 'FAILED (' + str(len(dupes)) + ' duplicates)'}")
    print()

    # 4. Lifecycle Joins
    print("--- LIFECYCLE JOINS ---")
    # a) Sales Order Header <-> Items
    cursor.execute("SELECT COUNT(*) FROM sales_order_headers h JOIN sales_order_items i ON h.salesOrder = i.salesOrder;")
    print(f"Sales Order Header <-> Items: {cursor.fetchone()[0]}")

    # b) Sales Order Item <-> Delivery Item (Mapped via referenceSdDocument/referenceSdDocumentItem)
    cursor.execute("SELECT COUNT(*) FROM sales_order_items i JOIN outbound_delivery_items d ON i.salesOrder = d.referenceSdDocument AND i.salesOrderItem = d.referenceSdDocumentItem;")
    print(f"Sales Order Item <-> Delivery Item (via reference): {cursor.fetchone()[0]}")

    # c) Delivery <-> Billing (Mapped via referenceSdDocument/referenceSdDocumentItem in billing items)
    cursor.execute("SELECT COUNT(*) FROM outbound_delivery_items d JOIN billing_document_items b ON d.deliveryDocument = b.referenceSdDocument AND d.deliveryDocumentItem = b.referenceSdDocumentItem;")
    print(f"Delivery Item <-> Billing Item (via reference): {cursor.fetchone()[0]}")

    # d) Billing <-> Payment (Mapped via customer and reference document or specifically billing document lookup)
    # Looking at the records, payments_accounts_receivable contains accountingDocument and customer.
    # The journal_entry_items_accounts_receivable contains referenceDocument which links to billingDocument.
    cursor.execute("SELECT COUNT(*) FROM billing_document_headers b JOIN payments_accounts_receivable p ON b.billingDocument = p.accountingDocument;")
    print(f"Billing Header <-> Payment (direct match test): {cursor.fetchone()[0]}")

    # 5. Foreign Key Integrity Check
    print()
    print("--- PRAGMA FOREIGN_KEY_CHECK ---")
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    print(f"Violations: {len(violations)}")
    for v in violations:
        print(v)

    conn.close()

if __name__ == "__main__":
    validate()
