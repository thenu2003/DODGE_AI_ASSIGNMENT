# SAP O2C Graph-Based Query System

Graph-based data modeling and grounded conversational analytics for SAP Order-to-Cash (O2C) data.

The system combines:
- a normalized relational store (SQLite),
- a derived business graph (NetworkX),
- a FastAPI backend with structured query planning,
- and a React + Cytoscape frontend with progressive graph exploration.

---

## 1) What This Project Solves

This project supports business questions like:
- "Which products are associated with the highest number of billing documents?"
- "Trace the full flow of billing document 90012345"
- "Find sales orders that were delivered but not billed"
- "Show details for sales order 12345"

The key design principle is **grounded answers only**:
- The LLM is not allowed to directly answer from imagination.
- The backend always converts a user question into a structured plan and executes real SQL and/or graph traversal.

---

## 2) High-Level Architecture

### Backend (`backend/`)

- `main.py`
  - FastAPI app and route composition
  - Graph endpoints (`/graph/*`, `/node/*`, `/trace/*`)
  - Chat pipeline endpoint (`POST /chat/query`)
- `ingest_data.py`
  - Ingests JSONL dataset into SQLite (`database.db`)
- `graph_builder.py`
  - Builds directed O2C graph from relational tables
- `graph_service.py`
  - Loads cached graph (`backend/graph.pkl`) and provides graph operations
- `chat_models.py`
  - Pydantic request/response and query-plan schema
- `guardrails.py`
  - Domain relevance checks and off-topic rejection
- `intent_classifier.py`
  - Gemini-based intent/entity extraction with rule-based fallback
- `query_planner.py`
  - Converts intent + entities into validated query steps
- `query_executor.py`
  - Executes SQL or graph steps with safety checks
- `response_formatter.py`
  - Builds user-facing answer text from execution results
- `chat_controller.py`
  - Orchestrates full chat/query flow

### Frontend (`frontend/`)

- `src/components/Dashboard.jsx`
  - Main screen layout (graph canvas + chat panel)
- `src/components/GraphController.js`
  - Progressive graph loading, expand-on-click, trace/query orchestration
- `src/components/GraphView.jsx`
  - Cytoscape rendering and interaction
- `src/components/NodePopupCard.jsx`
  - In-canvas node detail card on click
- `src/components/QueryPanel.jsx`
  - Chat-like query UI
- `src/api/graphApi.js`
  - Backend API client wrappers

---

## 3) Data Model and Graph Model

### Relational (SQLite)

The normalized O2C model includes:
- master data: `business_partners`, `products`, `plants`, addresses
- transactional flow:
  - `sales_order_headers`, `sales_order_items`, `sales_order_schedule_lines`
  - `outbound_delivery_headers`, `outbound_delivery_items`
  - `billing_document_headers`, `billing_document_items`
  - `journal_entry_items_accounts_receivable`, `payments_accounts_receivable`

### Graph (NetworkX DiGraph)

The graph maps business entities to nodes and lifecycle links to directed edges.

Main node classes:
- `Customer`, `SalesOrder`, `SalesOrderItem`, `ScheduleLine`
- `Delivery`, `DeliveryItem`
- `BillingDocument`, `BillingDocumentItem`
- `JournalEntry`, `Payment`
- `Product`, `Plant`, `Address`

Examples of relationship edges:
- `PLACED`, `HAS_ITEM`, `FULFILLED_BY`, `BILLED_AS`, `POSTED_TO`, `SETTLED_BY`

---

## 4) Why SQLite Was Chosen

SQLite is used intentionally for this phase because:
- **local-first simplicity**: zero setup and fast iteration
- **deterministic analytics**: stable SQL execution for query plans
- **good fit for medium dataset**: enough for development-scale O2C analysis
- **portable artifact**: one file (`database.db`) simplifies reproducibility

Tradeoffs acknowledged:
- no multi-user write scaling,
- limited advanced query optimization compared to server DBs.

This is acceptable because current workloads are read-heavy analytical lookups.

---

## 5) Conversational Query Pipeline

`POST /chat/query` follows this deterministic path:

1. **Guardrail check**
2. **Intent + entity extraction** (Gemini preferred, rules fallback)
3. **Structured query-plan generation**
4. **Plan validation**
5. **Execution** (SQLite and/or graph traversal)
6. **Grounded response formatting**

Response includes:
- `answer_text`
- `detected_intent`
- `query_plan`
- `data_result`
- `highlight_nodes`
- `guardrail`

---

## 6) LLM Prompting Strategy

LLM usage is intentionally constrained to **classification/extraction only**.

### Prompt design in `intent_classifier.py`

The prompt asks Gemini to:
- classify one of: `aggregation | trace_flow | broken_flow | entity_lookup`
- extract relevant entities (`document_id`, `entity_type`, `entity_id`)
- return strict JSON only

### Model selection/fallback

Current attempt order:
1. `gemini-2.5-flash`
2. `gemini-2.0-flash`
3. `gemini-flash-latest`

If LLM fails:
- classifier falls back to deterministic rules,
- error context is attached in `data_result.classifier.llm_error`.

### Why this strategy

- Keeps LLM useful where natural language ambiguity exists.
- Prevents hallucinated business answers.
- Preserves auditability via explicit query plan and raw execution output.

---

## 7) Guardrails Strategy

Implemented in `guardrails.py`.

Guardrails reject:
- empty prompts
- clearly off-topic prompts (blocklist patterns)
- prompts without O2C/domain context unless document-like IDs are present

Allowed prompts pass with keyword match metadata (`matched_keywords`).

This is a **lightweight first layer** and can be extended with:
- policy classes (PII/security),
- prompt-injection signatures,
- rate limits/abuse rules.

---

## 8) Query Planning and Execution Decisions

### Structured Plan Format

Plan is explicit (`QueryPlan`, `QueryStep`) with step kinds:
- `sql`
- `graph`

This ensures:
- explainability,
- stable execution behavior,
- future ability to add approval/simulation before run.

### Safety controls

`query_executor.py` enforces:
- only `SELECT` SQL allowed
- no mutating/DDL tokens (`insert`, `update`, `delete`, `drop`, `alter`, `pragma`, `;`)

### Intent handling

- **Aggregation**: SQL joins across SO -> Delivery -> Billing items
- **Trace flow**: graph ancestors + descendants subgraph
- **Broken flow**: delivered items lacking billing mapping
- **Entity lookup**: header table lookup by entity type

---

## 9) Frontend UX Decisions

The graph UI is progressive, not dump-all:

1. Start with high-level business flow nodes:
   - `Customer -> SalesOrder -> Delivery -> BillingDocument -> Payment`
2. Expand-on-click for abstract nodes and real nodes
3. Show in-canvas popup details when clicking a node
4. Use chat panel to run natural-language questions that render focused subgraphs

This balances:
- readability,
- performance,
- analyst workflow.

---

## 10) API Surface (Current)

Graph:
- `GET /graph`
- `GET /graph/summary`
- `GET /graph/business-flow`
- `GET /graph/expand/{node_id}?limit=20`
- `GET /node/{node_id}`
- `GET /node/{node_id}/neighbors`
- `GET /trace/{document_id}`
- `GET /health`

Conversational:
- `POST /chat/query`

---

## 11) Setup

## Prerequisites
- Python 3.10+
- Node.js 18+

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Set API key in `backend/.env`:

```env
GEMINI_API_KEY=your_key_here
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Backend runs on `http://127.0.0.1:8000` and frontend uses that API.

---

## 12) Known Constraints and Next Steps

Current constraints:
- rule-based guardrails are keyword-oriented
- planner is deterministic per intent (not cost-based optimization)
- graph expansion can still be dense for some entity neighborhoods

Recommended next steps:
- add unit/integration tests for planner + executor + guardrails
- add schema-aware planner validation (table/column whitelist contract)
- persist chat history/session memory on backend
- add auth + role-aware data access controls
- optionally migrate analytics workloads to PostgreSQL if data volume grows

