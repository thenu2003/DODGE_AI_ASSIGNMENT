# DATA VALIDATION REPORT

## 1. TABLE-WISE SUMMARY
| Table Name | Row Count | columns |
| :--- | :--- | :--- |
| billing_document_cancellations | 80 | 14 |
| billing_document_headers | 163 | 14 |
| billing_document_items | 245 | 9 |
| business_partners | 8 | 19 |
| business_partner_addresses | 8 | 20 |
| customer_company_assignments | 8 | 13 |
| customer_sales_area_assignments | 28 | 19 |
| journal_entry_items_accounts_receivable | 123 | 22 |
| outbound_delivery_headers | 86 | 13 |
| outbound_delivery_items | 137 | 11 |
| payments_accounts_receivable | 120 | 23 |
| plants | 44 | 14 |
| products | 69 | 17 |
| product_descriptions | 69 | 3 |
| product_plants | 3036 | 9 |
| product_storage_locations | 16723 | 5 |
| sales_order_headers | 100 | 24 |
| sales_order_items | 167 | 13 |
| sales_order_schedule_lines | 179 | 6 |


## 2. RELATIONAL MAPPING SHEET
| Table Name | Primary Key | Foreign Keys | Business Reference Columns |
| :--- | :--- | :--- | :--- |
| business_partners | businessPartner |  |  |
| products | product |  |  |
| product_descriptions | product, language | product -> products | product |
| sales_order_headers | salesOrder | soldToParty -> business_partners | salesOrder, soldToParty |
| sales_order_items | salesOrder, salesOrderItem | salesOrder -> sales_order_headers, material -> products | salesOrder, material |
| outbound_delivery_headers | deliveryDocument |  | deliveryDocument |
| outbound_delivery_items | deliveryDocument, deliveryDocumentItem | deliveryDocument -> outbound_delivery_headers | salesOrder: referenceSdDocument, item: referenceSdDocumentItem |
| billing_document_headers | billingDocument | soldToParty -> business_partners | billingDocument, soldToParty |
| billing_document_items | billingDocument, billingDocumentItem | billingDocument -> billing_document_headers | delivery: referenceSdDocument, item: referenceSdDocumentItem |
| payments_accounts_receivable | companyCode, fiscalYear, accountingDocument, accountingDocumentItem | customer -> business_partners | accountingDocument |


## 3. JOIN & TRACEABILITY METRICS
| Relationship | Join Success Count | Match Rate |
| :--- | :--- | :--- |
