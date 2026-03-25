import os
import glob
import json
import sqlite3
from pathlib import Path

DATA_DIR = r"d:\train\dataset"
DB_PATH = str(Path(__file__).resolve().parent / "database.db")

TABLE_SCHEMAS = {
    "business_partners": {"pk": "businessPartner"},
    "plants": {"pk": "plant"},
    "products": {"pk": "product"},
    "product_descriptions": {"pk": "product, language", "fk": [("product", "products", "product")]},
    "product_plants": {"pk": "product, plant", "fk": [("product", "products", "product"), ("plant", "plants", "plant")]},
    "product_storage_locations": {"pk": "product, plant, storageLocation", "fk": [("product", "products", "product"), ("plant", "plants", "plant")]},
    "business_partner_addresses": {"pk": "businessPartner, addressId", "fk": [("businessPartner", "business_partners", "businessPartner")]},
    "customer_company_assignments": {"pk": "customer, companyCode", "fk": [("customer", "business_partners", "businessPartner")]},
    "customer_sales_area_assignments": {"pk": "customer, salesOrganization, distributionChannel, division", "fk": [("customer", "business_partners", "businessPartner")]},
    "sales_order_headers": {"pk": "salesOrder", "fk": [("soldToParty", "business_partners", "businessPartner")]},
    "sales_order_items": {"pk": "salesOrder, salesOrderItem", "fk": [("salesOrder", "sales_order_headers", "salesOrder"), ("material", "products", "product")]},
    "sales_order_schedule_lines": {"pk": "salesOrder, salesOrderItem, scheduleLine", "fk": [("salesOrder, salesOrderItem", "sales_order_items", "salesOrder, salesOrderItem")]},
    "outbound_delivery_headers": {"pk": "deliveryDocument"},
    "outbound_delivery_items": {"pk": "deliveryDocument, deliveryDocumentItem", "fk": [("deliveryDocument", "outbound_delivery_headers", "deliveryDocument")]},
    "billing_document_headers": {"pk": "billingDocument", "fk": [("soldToParty", "business_partners", "businessPartner")]},
    "billing_document_cancellations": {"pk": "billingDocument", "fk": [("soldToParty", "business_partners", "businessPartner")]},
    "billing_document_items": {"pk": "billingDocument, billingDocumentItem", "fk": [("billingDocument", "billing_document_headers", "billingDocument")]},
    "journal_entry_items_accounts_receivable": {"pk": "companyCode, fiscalYear, accountingDocument, accountingDocumentItem", "fk": [("customer", "business_partners", "businessPartner")]},
    "payments_accounts_receivable": {"pk": "companyCode, fiscalYear, accountingDocument, accountingDocumentItem", "fk": [("customer", "business_partners", "businessPartner")]}
}

def infer_columns(folder_path):
    jsonl_files = glob.glob(os.path.join(folder_path, "**", "*.jsonl"), recursive=True)
    if not jsonl_files:
        return None
    keys = set()
    with open(jsonl_files[0], 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i > 100: break
            if not line.strip(): continue
            data = json.loads(line)
            keys.update(data.keys())
    return list(keys)

def generate_ddl(table_name, columns):
    cols_def = []
    for c in columns:
        cols_def.append(f'"{c}" TEXT')
        
    schema = TABLE_SCHEMAS.get(table_name, {})
    
    pk = schema.get("pk")
    if pk:
        pk_cols = [f'"{p.strip()}"' for p in pk.split(",")]
        cols_def.append(f'PRIMARY KEY ({", ".join(pk_cols)})')
        
    for fk in schema.get("fk", []):
        fk_cols = [f'"{c.strip()}"' for c in fk[0].split(",")]
        ref_table = fk[1]
        ref_cols = [f'"{c.strip()}"' for c in fk[2].split(",")]
        cols_def.append(f'FOREIGN KEY ({", ".join(fk_cols)}) REFERENCES "{ref_table}"({", ".join(ref_cols)})')
        
    ddl = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n  ' + ',\n  '.join(cols_def) + '\n)'
    return ddl

def flatten_dict(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            out[k] = json.dumps(v)
        elif isinstance(v, bool):
            out[k] = "true" if v else "false"
        elif v is None:
            out[k] = None
        else:
            out[k] = str(v)
    return out

def ingest():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Disable FK constraints during bulk load
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    folders = [f.path for f in os.scandir(DATA_DIR) if f.is_dir()]
    
    table_columns = {}
    
    # 1. Create Tables
    print("Creating tables...")
    for folder in folders:
        table_name = os.path.basename(folder)
        cols = infer_columns(folder)
        if not cols:
            continue
        table_columns[table_name] = cols
        
        ddl = generate_ddl(table_name, cols)
        try:
            cursor.execute(ddl)
            print(f"Created table: {table_name}")
        except Exception as e:
            print(f"Error creating table {table_name}:\n{ddl}\n{e}")
    
    conn.commit()
    
    # 2. Insert Data
    print("Ingesting data...")
    for folder in folders:
        table_name = os.path.basename(folder)
        cols = table_columns.get(table_name)
        if not cols:
            continue
            
        jsonl_files = glob.glob(os.path.join(folder, "**", "*.jsonl"), recursive=True)
        total_rows = 0
        for filepath in jsonl_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                batch = []
                for line in f:
                    if not line.strip(): continue
                    data = flatten_dict(json.loads(line))
                    row = tuple(data.get(c, None) for c in cols)
                    batch.append(row)
                    
                    if len(batch) >= 2000:
                        placeholders = ",".join(["?"] * len(cols))
                        try:
                            cursor.executemany(f'INSERT OR REPLACE INTO "{table_name}" VALUES ({placeholders})', batch)
                        except Exception as e:
                            print(f"Error inserting into {table_name}: {e}")
                        total_rows += len(batch)
                        batch = []
                if batch:
                    placeholders = ",".join(["?"] * len(cols))
                    try:
                        cursor.executemany(f'INSERT OR REPLACE INTO "{table_name}" VALUES ({placeholders})', batch)
                    except Exception as e:
                        print(f"Error inserting into {table_name}: {e}")
                    total_rows += len(batch)
        print(f"Ingested {total_rows} rows into {table_name}")
        
    conn.commit()
    conn.close()
    print(f"Ingestion complete. Database saved to {DB_PATH}")

if __name__ == "__main__":
    ingest()
