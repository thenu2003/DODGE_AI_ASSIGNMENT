import sqlite3
import networkx as nx
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "database.db")

class GraphBuilder:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.G = nx.DiGraph()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def build(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        # 1. Load Customers & Addresses
        cursor.execute("SELECT businessPartner, businessPartnerGrouping FROM business_partners")
        for row in cursor.fetchall():
            node_id = f"CUSTOMER_{row[0]}"
            self.G.add_node(node_id, node_type="Customer", customer_id=row[0], group=row[1])

        cursor.execute("SELECT businessPartner, addressId, cityName, country, streetName FROM business_partner_addresses")
        for row in cursor.fetchall():
            addr_id = f"ADDR_{row[0]}_{row[1]}"
            self.G.add_node(addr_id, node_type="Address", address_id=row[1], city=row[2], country=row[3], street=row[4])
            cust_node = f"CUSTOMER_{row[0]}"
            if self.G.has_node(cust_node):
                self.G.add_edge(cust_node, addr_id, relationship_type="HAS_ADDRESS")

        # 2. Products & Plants
        cursor.execute("SELECT product, productGroup, productType FROM products")
        for row in cursor.fetchall():
            self.G.add_node(f"PRODUCT_{row[0]}", node_type="Product", product_id=row[0], group=row[1], type=row[2])

        cursor.execute("SELECT plant, plantName FROM plants")
        for row in cursor.fetchall():
            self.G.add_node(f"PLANT_{row[0]}", node_type="Plant", plant_id=row[0], name=row[1])

        # 3. SalesOrders & Items
        cursor.execute("SELECT salesOrder, soldToParty, creationDate, totalNetAmount, transactionCurrency FROM sales_order_headers")
        for row in cursor.fetchall():
            so_id = f"SO_{row[0]}"
            self.G.add_node(so_id, node_type="SalesOrder", sales_order=row[0], date=row[2], amount=row[3], currency=row[4])
            customer_node = f"CUSTOMER_{row[1]}"
            if self.G.has_node(customer_node):
                self.G.add_edge(customer_node, so_id, relationship_type="PLACED")

        cursor.execute("SELECT salesOrder, salesOrderItem, material, productionPlant, netAmount FROM sales_order_items")
        for row in cursor.fetchall():
            soi_id = f"SOI_{row[0]}_{row[1]}"
            self.G.add_node(soi_id, node_type="SalesOrderItem", sales_order=row[0], item=row[1], product=row[2], net_amount=row[4])
            self.G.add_edge(f"SO_{row[0]}", soi_id, relationship_type="HAS_ITEM")
            
            prod_node = f"PRODUCT_{row[2]}"
            if self.G.has_node(prod_node):
                self.G.add_edge(soi_id, prod_node, relationship_type="FOR_PRODUCT")
            
            plant_node = f"PLANT_{row[3]}"
            if self.G.has_node(plant_node):
                self.G.add_edge(soi_id, plant_node, relationship_type="FROM_PLANT")

        # 4. Schedule Lines
        cursor.execute("SELECT salesOrder, salesOrderItem, scheduleLine, confdOrderQtyByMatlAvailCheck FROM sales_order_schedule_lines")
        for row in cursor.fetchall():
            sl_id = f"SL_{row[0]}_{row[1]}_{row[2]}"
            self.G.add_node(sl_id, node_type="ScheduleLine", sales_order=row[0], item=row[1], line=row[2], conf_qty=row[3])
            soi_node = f"SOI_{row[0]}_{row[1]}"
            if self.G.has_node(soi_node):
                self.G.add_edge(soi_node, sl_id, relationship_type="HAS_SCHEDULE_LINE")

        # 5. Delivery Headers & Items
        cursor.execute("SELECT deliveryDocument, creationDate, shippingPoint FROM outbound_delivery_headers")
        for row in cursor.fetchall():
            del_id = f"DEL_{row[0]}"
            self.G.add_node(del_id, node_type="Delivery", delivery_id=row[0], date=row[1], shipping_point=row[2])

        cursor.execute("SELECT deliveryDocument, deliveryDocumentItem, actualDeliveryQuantity, referenceSdDocument, referenceSdDocumentItem FROM outbound_delivery_items")
        for row in cursor.fetchall():
            deli_id = f"DELI_{row[0]}_{row[1]}"
            self.G.add_node(deli_id, node_type="DeliveryItem", delivery_id=row[0], item_id=row[1], qty=row[2])
            self.G.add_edge(deli_id, f"DEL_{row[0]}", relationship_type="PART_OF_DELIVERY")
            
            soi_node = f"SOI_{row[3]}_{row[4]}"
            if self.G.has_node(soi_node):
                self.G.add_edge(soi_node, deli_id, relationship_type="FULFILLED_BY")

        # 6. Billing Headers & Items
        cursor.execute("SELECT billingDocument, creationDate, totalNetAmount, soldToParty FROM billing_document_headers")
        for row in cursor.fetchall():
            bill_id = f"BILL_{row[0]}"
            self.G.add_node(bill_id, node_type="BillingDocument", billing_id=row[0], date=row[1], amount=row[2])

        cursor.execute("SELECT billingDocument, billingDocumentItem, netAmount, referenceSdDocument, referenceSdDocumentItem FROM billing_document_items")
        for row in cursor.fetchall():
            billi_id = f"BILLI_{row[0]}_{row[1]}"
            self.G.add_node(billi_id, node_type="BillingDocumentItem", billing_id=row[0], item_id=row[1], amount=row[2])
            self.G.add_edge(billi_id, f"BILL_{row[0]}", relationship_type="PART_OF_BILLING")
            
            deli_node = f"DELI_{row[3]}_{row[4]}"
            if self.G.has_node(deli_node):
                self.G.add_edge(deli_node, billi_id, relationship_type="BILLED_AS")

        # 7. Journal Entries & Payments
        cursor.execute("SELECT companyCode, fiscalYear, accountingDocument, referenceDocument FROM journal_entry_items_accounts_receivable")
        for row in cursor.fetchall():
            je_id = f"JE_{row[0]}_{row[1]}_{row[2]}"
            self.G.add_node(je_id, node_type="JournalEntry", company=row[0], year=row[1], doc=row[2])
            bill_node = f"BILL_{row[3]}"
            if self.G.has_node(bill_node):
                self.G.add_edge(bill_node, je_id, relationship_type="POSTED_TO")

        cursor.execute("SELECT companyCode, fiscalYear, accountingDocument FROM payments_accounts_receivable")
        for row in cursor.fetchall():
            pay_id = f"PAY_{row[2]}"
            self.G.add_node(pay_id, node_type="Payment", doc=row[2])
            je_node = f"JE_{row[0]}_{row[1]}_{row[2]}"
            if self.G.has_node(je_node):
                # Instructions: BillingDocument SETTLED_BY Payment
                # We link via JE
                incoming_bills = [u for u, v, d in self.G.in_edges(je_node, data=True) if d.get('relationship_type') == 'POSTED_TO']
                for bill in incoming_bills:
                    self.G.add_edge(bill, pay_id, relationship_type="SETTLED_BY")

        conn.close()
        return self.G

if __name__ == "__main__":
    builder = GraphBuilder()
    graph = builder.build()
    print(f"Graph build complete.")
    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")
