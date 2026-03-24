import sqlite3
import os

DB_PATH = r"d:\train\database.db"

def validate_system():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Row Counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    
    print("# RELATIONAL MODEL VALIDATION REPORT\n")
    print("## 1. TABLE-WISE SUMMARY")
    print("| Table Name | Row Count |")
    print("| :--- | :--- |")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM \"{table}\"")
        print(f"| {table} | {cursor.fetchone()[0]} |")
    print("\n")

    # 2. PK / FK Mapping
    mapping = [
        ("business_partners", "businessPartner", "None", "Central Entity"),
        ("products", "product", "None", "Master Data"),
        ("sales_order_headers", "salesOrder", "soldToParty -> business_partners", "Order Entry"),
        ("sales_order_items", "salesOrder, salesOrderItem", "salesOrder -> headers, material -> products", "Line Items"),
        ("outbound_delivery_headers", "deliveryDocument", "None", "Shipping"),
        ("outbound_delivery_items", "deliveryDocument, deliveryDocumentItem", "deliveryDocument -> headers", "Ref: salesOrder"),
        ("billing_document_headers", "billingDocument", "soldToParty -> business_partners", "Invoicing"),
        ("billing_document_items", "billingDocument, billingDocumentItem", "billingDocument -> headers", "Ref: deliveryDocument"),
        ("payments_accounts_receivable", "companyCode...accountingDocumentItem", "customer -> business_partners", "Financial Entry")
    ]
    print("## 2. PK / FK MAPPING SHEET")
    print("| Table Name | Primary Key | Foreign Keys | Business Context |")
    print("| :--- | :--- | :--- | :--- |")
    for m in mapping:
        print(f"| {' | '.join(m)} |")
    print("\n")

    # 3. Join & Traceability Metrics (Using CAST for type integrity)
    print("## 3. JOIN & TRACEABILITY METRICS")
    print("| Lifecycle Relationship | Join Success Count | Success Rate |")
    print("| :--- | :--- | :--- |")

    # SO Header -> Items
    cursor.execute("SELECT COUNT(*) FROM sales_order_headers h JOIN sales_order_items i ON CAST(h.salesOrder AS INTEGER) = CAST(i.salesOrder AS INTEGER)")
    so_match = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sales_order_items")
    so_total = cursor.fetchone()[0]
    print(f"| Sales Order Header ↔ Items | {so_match} / {so_total} items | {round(so_match/so_total*100, 2)}% |")

    # SO Item -> Delivery Item
    cursor.execute("SELECT COUNT(*) FROM sales_order_items i JOIN outbound_delivery_items d ON CAST(i.salesOrder AS INTEGER) = CAST(d.referenceSdDocument AS INTEGER) AND CAST(i.salesOrderItem AS INTEGER) = CAST(d.referenceSdDocumentItem AS INTEGER)")
    del_match = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM outbound_delivery_items")
    del_total = cursor.fetchone()[0]
    print(f"| Sales Order Item ↔ Delivery Item | {del_match} / {del_total} items | {round(del_match/del_total*100, 2)}% |")

    # Delivery Item -> Billing Item
    cursor.execute("SELECT COUNT(*) FROM outbound_delivery_items d JOIN billing_document_items b ON CAST(d.deliveryDocument AS INTEGER) = CAST(b.referenceSdDocument AS INTEGER) AND CAST(d.deliveryDocumentItem AS INTEGER) = CAST(b.referenceSdDocumentItem AS INTEGER)")
    bill_match = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM billing_document_items")
    bill_total = cursor.fetchone()[0]
    print(f"| Delivery Item ↔ Billing Item | {bill_match} / {bill_total} items | {round(bill_match/bill_total*100, 2)}% |")

    # Billing Header -> Payment (Using accountingDocument match)
    cursor.execute("SELECT COUNT(*) FROM billing_document_headers b JOIN payments_accounts_receivable p ON CAST(b.billingDocument AS INTEGER) = CAST(p.accountingDocument AS INTEGER)")
    pay_match = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM billing_document_headers")
    pay_total = cursor.fetchone()[0]
    print(f"| Billing Header ↔ Payment Link | {pay_match} / {pay_total} bills | {round(pay_match/pay_total*100, 2)}% |")

    print("\n")

    # 4. Business Flow Analysis
    print("## 4. BUSINESS FLOW INTEGRITY")
    cursor.execute("SELECT COUNT(*) FROM sales_order_headers WHERE CAST(salesOrder AS INTEGER) NOT IN (SELECT DISTINCT CAST(referenceSdDocument AS INTEGER) FROM outbound_delivery_items WHERE referenceSdDocument IS NOT NULL)")
    so_no_del = cursor.fetchone()[0]
    print(f"* **Orders Pending Delivery:** {so_no_del}")

    cursor.execute("SELECT COUNT(*) FROM outbound_delivery_headers WHERE CAST(deliveryDocument AS INTEGER) NOT IN (SELECT DISTINCT CAST(referenceSdDocument AS INTEGER) FROM billing_document_items WHERE referenceSdDocument IS NOT NULL)")
    del_no_bill = cursor.fetchone()[0]
    print(f"* **Deliveries Pending Billing:** {del_no_bill}")

    cursor.execute("PRAGMA foreign_key_check")
    violations = len(cursor.fetchall())
    print(f"* **Referential Integrity (FK Violations):** {violations}")

    conn.close()

if __name__ == "__main__":
    validate_system()
