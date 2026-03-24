from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


IntentType = Literal["aggregation", "trace_flow", "broken_flow", "entity_lookup"]


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    use_llm: bool = Field(default=True, description="Use Gemini for intent extraction when available")
    top_k: int = Field(default=10, ge=1, le=100)


class GuardrailResult(BaseModel):
    allowed: bool
    reason: str
    matched_keywords: List[str] = Field(default_factory=list)


class QueryStep(BaseModel):
    kind: Literal["sql", "graph"]
    name: str
    sql: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    graph_action: Optional[str] = None


class QueryPlan(BaseModel):
    version: str = "v1"
    intent: IntentType
    entities: Dict[str, Any] = Field(default_factory=dict)
    steps: List[QueryStep]
    notes: Optional[str] = None


class ChatQueryResponse(BaseModel):
    answer_text: str
    detected_intent: str
    query_plan: Dict[str, Any]
    data_result: Dict[str, Any]
    highlight_nodes: List[str] = Field(default_factory=list)
    guardrail: Dict[str, Any]
